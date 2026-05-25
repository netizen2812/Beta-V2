"""
Tafsir RAG — ChromaDB vector store for scholarly Quran interpretations.

Indexes AlQuran.Cloud tafsir/translation text into ChromaDB for
retrieval-augmented generation. When the user asks about an ayah,
we first retrieve the exact scholarly interpretation, then the LLM
only rephrases/explains — never hallucinates theology.

Flow:
  1. On first run, fetches tafsir data from AlQuran.Cloud API
  2. Indexes into ChromaDB with sentence-transformer embeddings
  3. On query, retrieves top-K relevant tafsir passages
"""

import os
import json
import logging
import httpx
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
TAFSIR_CACHE = DATA_DIR / "tafsir_cache.json"
CHROMA_DIR = DATA_DIR / "chroma_db"

# Tafsir editions to index (scholarly sources)
TAFSIR_EDITIONS = {
    "en.kathir": "Ibn Kathir (English Translation)",
    "ar.quran": "Quran Arabic Text",
}

# AlQuran.Cloud API
API_BASE = "http://api.alquran.cloud/v1"


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
        
        from chromadb.utils import embedding_functions
        emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="intfloat/multilingual-e5-large", device="cpu")

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


        flag_file = CHROMA_DIR / "build_complete.flag"
        self.collection_size = self._collection.count()

        if not flag_file.exists() or self.collection_size == 0:
            logger.info("📥 Tafsir collection incomplete or empty. Building index...")
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

        self.is_loaded = True

    def _build_index(self):
        """Fetch tafsir data and index into ChromaDB."""
        tafsir_data = self._fetch_tafsir_data()

        if not tafsir_data:
            logger.warning("⚠️ No tafsir data fetched. Skipping indexing.")
            return

        # Keep only test surahs (Surahs 1, 112, 113, 114) for fast CPU startup
        tafsir_data = [
            entry for entry in tafsir_data
            if entry.get("surah") in [1, 112, 113, 114]
        ]
        logger.info(f"⚡ Filtered Tafsir RAG indexing to Surahs (1, 112, 113, 114). Count: {len(tafsir_data)} entries.")

        # Batch add to ChromaDB
        batch_size = 500
        ids = []
        documents = []
        metadatas = []

        for entry in tafsir_data:
            doc_id = f"{entry['edition']}_{entry['surah']}_{entry['ayah']}"
            ids.append(doc_id)
            documents.append(entry["text"])
            metadatas.append({
                "surah": entry["surah"],
                "ayah": entry["ayah"],
                "ayah_id": f"{entry['surah']}:{entry['ayah']}",
                "edition": entry["edition"],
                "edition_name": entry["edition_name"],
            })

        # Add in batches
        for i in range(0, len(ids), batch_size):
            self._collection.add(
                ids=ids[i:i + batch_size],
                documents=documents[i:i + batch_size],
                metadatas=metadatas[i:i + batch_size],
            )
            logger.info(f"  Indexed {min(i + batch_size, len(ids))}/{len(ids)} entries...")

        logger.info(f"✅ Tafsir index built: {len(ids)} entries")

    def _fetch_tafsir_data(self) -> list[dict]:
        """Fetch tafsir text from AlQuran.Cloud API or cache."""
        if TAFSIR_CACHE.exists():
            logger.info(f"📂 Loading tafsir from cache: {TAFSIR_CACHE}")
            with open(TAFSIR_CACHE, "r", encoding="utf-8") as f:
                return json.load(f)

        all_entries = []

        for edition, edition_name in TAFSIR_EDITIONS.items():
            logger.info(f"📥 Fetching edition: {edition}...")
            try:
                response = httpx.get(
                    f"{API_BASE}/quran/{edition}",
                    timeout=60.0,
                )
                response.raise_for_status()
                data = response.json()

                for surah in data["data"]["surahs"]:
                    for ayah in surah["ayahs"]:
                        all_entries.append({
                            "surah": surah["number"],
                            "ayah": ayah["numberInSurah"],
                            "text": ayah["text"],
                            "edition": edition,
                            "edition_name": edition_name,
                        })
            except Exception as e:
                logger.error(f"❌ Failed to fetch {edition}: {e}")

        if all_entries:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            with open(TAFSIR_CACHE, "w", encoding="utf-8") as f:
                json.dump(all_entries, f, ensure_ascii=False)
            logger.info(f"✅ Tafsir cache saved: {len(all_entries)} entries")

        return all_entries

    def query(self, text: str, ayah_id: str = None, n_results: int = 5) -> list[dict]:
        """
        Query the tafsir vector store.

        Args:
            text: Search query (user question or ayah text)
            ayah_id: Optional filter by specific ayah (e.g., "2:255")
            n_results: Number of results to return

        Returns:
            [
                {
                    "text": "In the name of Allah...",
                    "ayah_id": "1:1",
                    "edition": "en.sahih",
                    "distance": 0.12
                }
            ]
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

        try:
            results = self._collection.query(
                query_texts=[text],
                n_results=n_results,
            )
        except Exception as e:
            logger.error(f"ChromaDB query error: {e}")
            return []

        output = []
        if results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                meta = results["metadatas"][0][i] if results["metadatas"] else {}
                dist = results["distances"][0][i] if results["distances"] else 0
                output.append({
                    "text": doc,
                    "ayah_id": meta.get("ayah_id", ""),
                    "edition": meta.get("edition", ""),
                    "edition_name": meta.get("edition_name", ""),
                    "distance": round(dist, 4),
                })

        return output

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
