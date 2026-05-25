import os
import json
import logging
from pathlib import Path
import random

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
CHROMA_DIR = DATA_DIR / "chroma_db"
WISDOM_PATH = DATA_DIR / "wisdom_templates.json"

class SmartRAG:
    def __init__(self):
        self._client = None
        self._madhab_collection = None
        self._tafsir_collection = None
        self.is_loaded = False
        self.wisdom_templates = {}

    def load(self):
        """Initialize ChromaDB clients and collections."""
        try:
            import chromadb
        except ImportError:
            logger.warning("⚠️ ChromaDB not installed. SmartRAG disabled.")
            self.is_loaded = False
            return

        try:
            CHROMA_DIR.mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(path=str(CHROMA_DIR))
            from chromadb.utils import embedding_functions
            emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="intfloat/multilingual-e5-large", device="cpu")

            # Load madhab rules collection
            try:
                self._madhab_collection = self._client.get_collection(
                    name="madhab_rules",
                    embedding_function=emb_fn
                )
            except ValueError as e:
                if "embedding function" in str(e).lower() or "conflict" in str(e).lower():
                    logger.warning("⚠️ Embedding function conflict in madhab_rules. Deleting collection so it can be re-indexed...")
                    try:
                        self._client.delete_collection("madhab_rules")
                    except Exception:
                        pass
                else:
                    logger.warning(f"⚠️ ValueError loading 'madhab_rules': {e}")
            except Exception as e:
                logger.warning(f"⚠️ Could not load collection 'madhab_rules': {e}. Please run the index script.")

            # Load tafsir collection
            try:
                self._tafsir_collection = self._client.get_collection(
                    name="quran_tafsir",
                    embedding_function=emb_fn
                )
            except ValueError as e:
                if "embedding function" in str(e).lower() or "conflict" in str(e).lower():
                    logger.warning("⚠️ Embedding function conflict in quran_tafsir. Recreating collection...")
                    try:
                        self._client.delete_collection("quran_tafsir")
                    except Exception:
                        pass
                else:
                    logger.warning(f"⚠️ ValueError loading 'quran_tafsir': {e}")
            except Exception as e:
                logger.warning(f"⚠️ Could not load collection 'quran_tafsir': {e}")

            # Load wisdom templates
            if WISDOM_PATH.exists():
                with open(WISDOM_PATH, "r", encoding="utf-8") as f:
                    self.wisdom_templates = json.load(f)
                logger.info(f"📂 Loaded {len(self.wisdom_templates)} wisdom templates from {WISDOM_PATH}")
            else:
                logger.warning(f"⚠️ Wisdom templates not found at {WISDOM_PATH}")

            self.is_loaded = True
            logger.info("✅ SmartRAG service fully loaded.")

        except Exception as e:
            logger.error(f"❌ SmartRAG initialization failed: {e}")
            self.is_loaded = False

    def query_madhab(self, madhab: str, query_text: str, n_results: int = 3) -> list[dict]:
        """
        Query the madhab vector DB. Filters rules by the requested madhab.
        
        Args:
            madhab: One of 'hanafi', 'shafi', 'maliki', 'hanbali'
            query_text: The search text (e.g., "recitation of fatiha", "pronunciation mistake")
            n_results: Number of results to return
            
        Returns:
            List of matching passages with metadata
        """
        if not self.is_loaded or self._madhab_collection is None:
            logger.warning("SmartRAG not loaded or madhab collection missing.")
            return []

        madhab = madhab.lower().strip()
        
        # Valid schools
        valid_schools = ["hanafi", "shafi", "maliki", "hanbali"]
        where_filter = None
        
        if madhab in valid_schools:
            # We index with boolean flags for each school (e.g. shafi=True)
            where_filter = {madhab: True}

        try:
            results = self._madhab_collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where_filter
            )
        except Exception as e:
            logger.error(f"ChromaDB query error in madhab_rules: {e}")
            # Retry without metadata filter if it failed or had no results
            try:
                results = self._madhab_collection.query(
                    query_texts=[query_text],
                    n_results=n_results
                )
            except Exception:
                return []

        output = []
        if results and results["documents"] and len(results["documents"]) > 0:
            for i, doc in enumerate(results["documents"][0]):
                meta = results["metadatas"][0][i] if results["metadatas"] else {}
                dist = results["distances"][0][i] if results["distances"] else 0
                output.append({
                    "text": doc,
                    "page": meta.get("page", 0),
                    "primary_madhab": meta.get("primary_madhab", ""),
                    "is_fatiha": meta.get("is_fatiha", False),
                    "distance": round(dist, 4)
                })
        
        return output

    def get_premade_asset(self, category_key: str, index: int = None, lang: str = "en") -> str:
        """
        Retrieves a pre-made template text from wisdom_templates.json.
        
        Args:
            category_key: E.g., 'reception.greetings.time_based.morning' or 'pedagogy.correction.makharij.throat_halqi'
            index: Optional index to pick a specific template, otherwise random
            lang: Target language. Currently wisdom_templates has 'en' keys, so if a non-en language is 
                  requested, we retrieve the English text and return it so the caller can translate/adapt it.
        """
        # Formulate key
        prefix = "en"  # Wisdom templates are en.
        full_key = f"{prefix}.{category_key}"
        
        templates = self.wisdom_templates.get(full_key)
        if not templates:
            # Try exact key directly
            templates = self.wisdom_templates.get(category_key)

        if not templates:
            logger.warning(f"⚠️ Wisdom template key '{full_key}' or '{category_key}' not found.")
            return ""

        if index is not None and 0 <= index < len(templates):
            return templates[index]
        
        return random.choice(templates)

    def query_tafsir(self, query_text: str, ayah_id: str = None, n_results: int = 3) -> list[dict]:
        """Query the tafsir database."""
        if not self.is_loaded or self._tafsir_collection is None:
            return []

        # Direct get for exact ayah
        if ayah_id:
            try:
                exact_results = self._tafsir_collection.get(where={"ayah_id": ayah_id})
                if exact_results and exact_results["documents"]:
                    output = []
                    for i, doc in enumerate(exact_results["documents"]):
                        meta = exact_results["metadatas"][i] if exact_results["metadatas"] else {}
                        output.append({
                            "text": doc,
                            "ayah_id": meta.get("ayah_id", ""),
                            "edition": meta.get("edition", ""),
                            "edition_name": meta.get("edition_name", ""),
                            "distance": 0.0
                        })
                    return output[:n_results]
            except Exception:
                pass

        try:
            results = self._tafsir_collection.query(
                query_texts=[query_text],
                n_results=n_results
            )
        except Exception:
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
                    "distance": round(dist, 4)
                })
        return output

    def get_localized_template(self, lang: str, category_key: str, idx: int) -> str:
        """Retrieves a translated template text from wisdom_templates_localized.json."""
        if not hasattr(self, 'localized_templates') or not self.localized_templates:
            # Try to load
            localized_path = DATA_DIR / "wisdom_templates_localized.json"
            if localized_path.exists():
                try:
                    with open(localized_path, "r", encoding="utf-8") as f:
                        self.localized_templates = json.load(f)
                except Exception as e:
                    logger.error(f"Failed to load localized templates: {e}")
                    self.localized_templates = {}
            else:
                self.localized_templates = {}
                
        lang_data = self.localized_templates.get(lang)
        if lang_data:
            templates = lang_data.get(category_key)
            if templates and 0 <= idx < len(templates):
                return templates[idx]
                
        # Fallback to English template from wisdom_templates
        templates = self.wisdom_templates.get(f"en.{category_key}")
        if not templates:
            templates = self.wisdom_templates.get(category_key)
        if templates and 0 <= idx < len(templates):
            return templates[idx]
        return ""

# Singleton instance
smart_rag = SmartRAG()

