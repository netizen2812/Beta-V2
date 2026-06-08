"""
Tafsir RAG — ChromaDB vector store for scholarly Quran interpretations.

Indexes AlQuran.Cloud tafsir/translation text into ChromaDB for
retrieval-augmented generation. When the user asks about an ayah,
we first retrieve the exact scholarly interpretation, then the LLM
only rephrases/explains — never hallucinates theology.

Flow:
  1. On first run, fetches tafsir data from AlQuran.Cloud API (all 114 surahs)
  2. Indexes into ChromaDB with sentence-transformer embeddings
  3. On query, retrieves top-K relevant tafsir passages

Environment:
  TAFSIR_FAST_START=1   — Only index core surahs (1,2,18,36,55,67,112-114).
                          Use on RAM-constrained deployments. Default: full Quran.
"""

import os
import json
import time
import logging
import httpx
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
TAFSIR_CACHE = DATA_DIR / "tafsir_cache.json"
CHROMA_DIR = DATA_DIR / "chroma_db"
if os.getenv("HF_HOME") and os.path.exists("/models"):
    CHROMA_DIR = Path("/models/chroma_db")

# Tafsir editions to index (scholarly sources)
TAFSIR_EDITIONS = {
    "en.kathir": "Ibn Kathir (English Translation)",
    "ar.quran": "Quran Arabic Text",
}

# AlQuran.Cloud API
API_BASE = "http://api.alquran.cloud/v1"

# ── Fast-start mode: only index these surahs when TAFSIR_FAST_START=1 ──────────
# Covers: Al-Fatihah, Al-Baqarah, Al-Kahf, Ya-Sin, Ar-Rahman, Al-Mulk,
#         Al-Ikhlas, Al-Falaq, An-Nas — the most commonly recited surahs.
FAST_START_SURAHS = {1, 2, 18, 36, 55, 67, 112, 113, 114}
FAST_START_MODE = os.getenv("TAFSIR_FAST_START", "0").strip() == "1"


class TafsirRAG:
    def __init__(self):
        self._client = None
        self._collection = None
        self.is_loaded = False
        self.collection_size = 0

    def load(self):
        """Initialize ChromaDB and load/build the tafsir index."""
        try:
            import chromadb
        except ImportError:
            logger.warning("⚠️ ChromaDB not installed. Tafsir RAG disabled.")
            self.is_loaded = False
            self.collection_size = 0
            return

        CHROMA_DIR.mkdir(parents=True, exist_ok=True)

        self._client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        
        import torch
        device = "cpu"
        from chromadb.utils import embedding_functions
        emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="intfloat/multilingual-e5-large", device=device)

        # Get or create collection
        try:
            self._collection = self._client.get_or_create_collection(
                name="quran_tafsir",
                metadata={"hnsw:space": "cosine"},
                embedding_function=emb_fn
            )
        except ValueError as e:
            if "embedding function" in str(e).lower() or "conflict" in str(e).lower():
                logger.warning("⚠️ Embedding function conflict in quran_tafsir. Recreating collection...")
                try:
                    self._client.delete_collection("quran_tafsir")
                except Exception:
                    pass
                self._collection = self._client.create_collection(
                    name="quran_tafsir",
                    metadata={"hnsw:space": "cosine"},
                    embedding_function=emb_fn
                )
            else:
                raise e


        # Use a versioned flag so changing the surah scope triggers a rebuild.
        scope_tag = "fast" if FAST_START_MODE else "full"
        flag_file = CHROMA_DIR / f"tafsir_build_{scope_tag}.flag"
        self.collection_size = self._collection.count()

        if not flag_file.exists() or self.collection_size == 0:
            mode_label = "FAST-START (9 core surahs)" if FAST_START_MODE else "FULL QURAN (114 surahs)"
            logger.info(f"📥 Tafsir collection rebuild triggered [{mode_label}]...")
            try:
                self._client.delete_collection("quran_tafsir")
                self._collection = self._client.create_collection(
                    name="quran_tafsir",
                    metadata={"hnsw:space": "cosine"},
                    embedding_function=emb_fn
                )
            except Exception:
                pass
            self._build_index()
            flag_file.touch()
            self.collection_size = self._collection.count()
            logger.info(f"✅ Tafsir index complete: {self.collection_size} entries indexed.")

        self.is_loaded = True

    def _build_index(self):
        """Fetch tafsir data and index into ChromaDB — full Quran or fast-start subset."""
        tafsir_data = self._fetch_tafsir_data()

        if not tafsir_data:
            logger.warning("⚠️ No tafsir data fetched. Skipping indexing.")
            return

        # ── Surah scope filter ──────────────────────────────────────────────────
        if FAST_START_MODE:
            tafsir_data = [e for e in tafsir_data if e.get("surah") in FAST_START_SURAHS]
            logger.info(
                f"⚡ FAST-START mode: indexing {len(FAST_START_SURAHS)} core surahs "
                f"({len(tafsir_data)} entries). Set TAFSIR_FAST_START=0 to index full Quran."
            )
        else:
            logger.info(f"📖 FULL-QURAN mode: indexing all {len(tafsir_data)} ayah entries across 114 surahs.")

        # ── Batch upsert into ChromaDB ──────────────────────────────────────────
        batch_size = 1000  # Larger batch = fewer round trips to ChromaDB
        ids = []
        documents = []
        metadatas = []

        for entry in tafsir_data:
            doc_id = f"{entry['edition']}_{entry['surah']}_{entry['ayah']}"
            ids.append(doc_id)
            documents.append(entry["text"])
            metadatas.append({
                "surah": int(entry["surah"]),
                "ayah": int(entry["ayah"]),
                "ayah_id": f"{entry['surah']}:{entry['ayah']}",
                "edition": entry["edition"],
                "edition_name": entry["edition_name"],
            })

        total = len(ids)
        for i in range(0, total, batch_size):
            self._collection.add(
                ids=ids[i:i + batch_size],
                documents=documents[i:i + batch_size],
                metadatas=metadatas[i:i + batch_size],
            )
            indexed = min(i + batch_size, total)
            logger.info(f"  Indexed {indexed}/{total} entries ({indexed * 100 // total}%)...")

        logger.info(f"✅ Tafsir index built: {total} entries ({len(TAFSIR_EDITIONS)} editions)")

    def _fetch_tafsir_data(self) -> list[dict]:
        """Fetch tafsir text from AlQuran.Cloud API or disk cache.

        Uses paginated surah-by-surah requests to avoid gateway timeouts
        on the full-Quran endpoint. Falls back to the bulk endpoint on error.
        Results are cached to `tafsir_cache.json` so subsequent cold-starts
        skip the network entirely.
        """
        if TAFSIR_CACHE.exists():
            logger.info(f"📂 Loading tafsir from disk cache: {TAFSIR_CACHE}")
            with open(TAFSIR_CACHE, "r", encoding="utf-8") as f:
                return json.load(f)

        all_entries = []
        MAX_RETRIES = 3
        RETRY_DELAY = 2.0   # seconds between retries
        REQUEST_TIMEOUT = 20.0  # per-surah timeout (much safer than 60s for full Quran)

        for edition, edition_name in TAFSIR_EDITIONS.items():
            logger.info(f"📥 Fetching full Quran — edition: {edition} (paginated, surah-by-surah)...")
            edition_count = 0

            for surah_num in range(1, 115):  # Surahs 1–114
                url = f"{API_BASE}/surah/{surah_num}/{edition}"
                fetched = False

                for attempt in range(1, MAX_RETRIES + 1):
                    try:
                        response = httpx.get(url, timeout=REQUEST_TIMEOUT)
                        response.raise_for_status()
                        data = response.json()

                        surah_data = data.get("data", {})
                        ayahs = surah_data.get("ayahs", [])

                        for ayah in ayahs:
                            all_entries.append({
                                "surah": surah_num,
                                "ayah": ayah["numberInSurah"],
                                "text": ayah["text"],
                                "edition": edition,
                                "edition_name": edition_name,
                            })

                        edition_count += len(ayahs)
                        fetched = True
                        break  # Success — move to next surah

                    except httpx.TimeoutException:
                        logger.warning(
                            f"  ⏳ Timeout fetching {edition} surah {surah_num} "
                            f"(attempt {attempt}/{MAX_RETRIES}). Retrying in {RETRY_DELAY}s..."
                        )
                        time.sleep(RETRY_DELAY)
                    except Exception as e:
                        logger.warning(
                            f"  ⚠️ Error fetching {edition} surah {surah_num} "
                            f"(attempt {attempt}/{MAX_RETRIES}): {e}"
                        )
                        time.sleep(RETRY_DELAY)

                if not fetched:
                    logger.error(f"  ❌ Failed all {MAX_RETRIES} attempts for {edition} surah {surah_num}. Skipping.")

                # Brief courtesy pause to avoid hammering the free API
                time.sleep(0.05)

            logger.info(f"  ✅ Edition '{edition}' fetched: {edition_count} ayahs across 114 surahs.")

        if all_entries:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            with open(TAFSIR_CACHE, "w", encoding="utf-8") as f:
                json.dump(all_entries, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ Tafsir cache saved: {len(all_entries)} total entries — next startup will use cache.")
        else:
            logger.error("❌ No tafsir entries fetched. RAG will be empty.")

        return all_entries

    def query(self, text: str, ayah_id: str = None, n_results: int = 5) -> list[dict]:
        """
        Query the tafsir vector store.

        Args:
            text: Search query (user question or ayah text)
            ayah_id: Optional filter by specific ayah (e.g., "2:255")
            n_results: Number of results to return
        """
        if not self.is_loaded or self._collection is None:
            return []

        n_results = min(max(1, n_results), 10)

        # Direct bypass for exact ayah_id
        if ayah_id:
            exact_results = self._collection.get(where={"ayah_id": ayah_id})
            if exact_results and exact_results["documents"]:
                output = []
                for i, doc in enumerate(exact_results["documents"]):
                    meta = exact_results["metadatas"][i] if exact_results["metadatas"] else {}
                    output.append({
                        "text": doc,
                        "ayah_id": meta.get("ayah_id", ""),
                        "edition": meta.get("edition", ""),
                        "edition_name": meta.get("edition_name", ""),
                        "distance": 0.0,
                    })
                return output[:n_results]

        # 1. Query Expansion (Synonyms)
        synonyms = {
            "elongation": ["madd", "elongation", "stretch", "lengthening"],
            "madd": ["madd", "elongation", "stretch", "lengthening"],
            "echo": ["qalqalah", "echo", "bounce", "bouncing", "vibration"],
            "echoing": ["qalqalah", "echoing", "bounce", "bouncing", "vibration"],
            "bounce": ["qalqalah", "echoing", "bounce", "bouncing", "vibration"],
            "bouncing": ["qalqalah", "echoing", "bounce", "bouncing", "vibration"],
            "qalqalah": ["qalqalah", "echoing", "bounce", "bouncing", "vibration"],
            "nasal": ["ghunnah", "nasal", "nasalization", "nose"],
            "nasalization": ["ghunnah", "nasal", "nasalization", "nose"],
            "nose": ["ghunnah", "nasal", "nasalization", "nose"],
            "ghunnah": ["ghunnah", "nasal", "nasalization", "nose"],
            "merging": ["idgham", "merging", "blend", "blending", "combining"],
            "blend": ["idgham", "merging", "blend", "blending", "combining"],
            "combining": ["idgham", "merging", "blend", "blending", "combining"],
            "idgham": ["idgham", "merging", "blend", "blending", "combining"],
            "hiding": ["ikhfa", "hiding", "concealing", "conceal"],
            "concealing": ["ikhfa", "hiding", "concealing", "conceal"],
            "ikhfa": ["ikhfa", "hiding", "concealing", "conceal"],
            "changing": ["iqlab", "changing", "converting", "conversion", "flipping"],
            "converting": ["iqlab", "changing", "converting", "conversion", "flipping"],
            "iqlab": ["iqlab", "changing", "converting", "conversion", "flipping"],
            "articulation": ["makhraj", "articulation", "pronunciation", "mouth", "throat", "tongue", "lips"],
            "pronunciation": ["makhraj", "articulation", "pronunciation", "mouth", "throat", "tongue", "lips"],
            "makhraj": ["makhraj", "articulation", "pronunciation", "mouth", "throat", "tongue", "lips"],
            "wudu": ["wudu", "ablution", "purification", "washing"],
            "ablution": ["wudu", "ablution", "purification", "washing"],
            "salah": ["salah", "prayer", "namaz", "praying"],
            "prayer": ["salah", "prayer", "namaz", "praying"],
            "namaz": ["salah", "prayer", "namaz", "praying"],
            "fasting": ["sawm", "fasting", "fast", "ramadan"],
            "sawm": ["sawm", "fasting", "fast", "ramadan"],
            "fast": ["sawm", "fasting", "fast", "ramadan"],
        }
        
        query_text = text
        if text:
            words = text.lower().split()
            expanded_terms = []
            for w in words:
                w_clean = w.strip("?,.:;!\"'()")
                if w_clean in synonyms:
                    expanded_terms.extend(synonyms[w_clean])
            if expanded_terms:
                seen = set()
                unique_expanded = [x for x in expanded_terms if not (x in seen or seen.add(x))]
                query_text = f"{text} ({' '.join(unique_expanded)})"

        try:
            # Fetch n_results * 2 candidates to allow room for keyword-overlap re-ranking
            results = self._collection.query(
                query_texts=[query_text],
                n_results=n_results * 2,
            )
        except Exception as e:
            logger.error(f"ChromaDB query error: {e}")
            return []

        output = []
        if results and results["documents"]:
            # Extract query keywords for lexical re-ranking overlap
            query_words = set(w.lower().strip("?,.:;!\"'()") for w in text.split() if len(w) > 2) if text else set()
            
            for i, doc in enumerate(results["documents"][0]):
                meta = results["metadatas"][0][i] if results["metadatas"] else {}
                dist = results["distances"][0][i] if results["distances"] else 0
                
                # Lexical re-ranking boost
                doc_words = set(w.lower().strip("?,.:;!\"'()") for w in doc.split())
                overlap = len(query_words.intersection(doc_words))
                boosted_dist = dist - (overlap * 0.05)
                
                output.append({
                    "text": doc,
                    "ayah_id": meta.get("ayah_id", ""),
                    "edition": meta.get("edition", ""),
                    "edition_name": meta.get("edition_name", ""),
                    "distance": round(dist, 4),
                    "boosted_distance": round(boosted_dist, 4)
                })
                
            # Sort by boosted distance (smaller is better)
            output = sorted(output, key=lambda x: x["boosted_distance"])

        return output[:n_results]

    def get_ayah_context(self, ayah_id: str) -> str:
        """
        Get all indexed tafsir text for a specific ayah.
        Used to ground LLM explanations in scholarly sources.
        """
        if not self.is_loaded or self._collection is None:
            return ""

        try:
            results = self._collection.get(
                where={"ayah_id": ayah_id},
            )
        except Exception:
            return ""

        if results and results["documents"]:
            return "\n\n---\n\n".join(results["documents"])

        return ""
