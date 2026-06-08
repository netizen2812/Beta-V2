import os
import sys
import json
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
CHROMA_DIR = DATA_DIR / "chroma_db"
if os.getenv("HF_HOME") and os.path.exists("/models"):
    CHROMA_DIR = Path("/models/chroma_db")

TAJWEED_JSON_PATH = DATA_DIR / "tajweed_rules.json"
HADITH_JSON_PATH = DATA_DIR / "hadiths.json"

def main():
    # 1. Load SentenceTransformer on CPU
    try:
        from chromadb.utils import embedding_functions
        emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="intfloat/multilingual-e5-large",
            device="cpu"
        )
        logger.info("🤖 SentenceTransformer initialized successfully.")
    except Exception as e:
        logger.error(f"❌ Failed to load embedding model: {e}")
        sys.exit(1)

    # 2. Check for ChromaDB
    try:
        import chromadb
    except ImportError:
        logger.error("❌ ChromaDB is not installed in the environment!")
        sys.exit(1)

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    # 3. Index Tajweed Rules
    if TAJWEED_JSON_PATH.exists():
        logger.info(f"📂 Found Tajweed rules: {TAJWEED_JSON_PATH}")
        with open(TAJWEED_JSON_PATH, "r", encoding="utf-8") as f:
            tajweed_rules = json.load(f)
            
        try:
            client.delete_collection("tajweed_rules")
            logger.info("🗑️ Existing 'tajweed_rules' collection deleted.")
        except Exception:
            pass

        collection = client.create_collection(
            name="tajweed_rules",
            metadata={"hnsw:space": "cosine"},
            embedding_function=emb_fn
        )

        ids = []
        documents = []
        metadatas = []

        for item in tajweed_rules:
            letters_str = ", ".join(item.get("letters", []))
            types_desc = ""
            if "types" in item:
                desc_lines = []
                for t in item["types"]:
                    detail = t.get("condition") or t.get("description") or ""
                    desc_lines.append(f"- {t['name']}: {detail} (Example: {t.get('example', '')})")
                types_desc = "\nSubtypes:\n" + "\n".join(desc_lines)
                
            doc_text = f"Rule: {item['rule_name']} (Category: {item['category']})\nDescription: {item['description']}\nLetters: {letters_str}\nGuidance: {item.get('guidance', '')}{types_desc}"
            
            ids.append(item["id"])
            documents.append(doc_text)
            metadatas.append({
                "rule_name": item["rule_name"],
                "category": item["category"],
                "letters": letters_str
            })

        collection.add(ids=ids, documents=documents, metadatas=metadatas)
        logger.info(f"✅ Indexed {collection.count()} Tajweed rules into ChromaDB 'tajweed_rules'.")

    # 4. Index Hadiths
    if HADITH_JSON_PATH.exists():
        logger.info(f"📂 Found Hadiths: {HADITH_JSON_PATH}")
        with open(HADITH_JSON_PATH, "r", encoding="utf-8") as f:
            hadiths = json.load(f)

        try:
            client.delete_collection("hadiths")
            logger.info("🗑️ Existing 'hadiths' collection deleted.")
        except Exception:
            pass

        collection = client.create_collection(
            name="hadiths",
            metadata={"hnsw:space": "cosine"},
            embedding_function=emb_fn
        )

        ids = []
        documents = []
        metadatas = []

        for item in hadiths:
            doc_text = f"Hadith Narrated by {item['narrator']} (Source: {item['source']})\nTopic: {item['topic']}\nText: {item['text']}"
            
            ids.append(item["id"])
            documents.append(doc_text)
            metadatas.append({
                "narrator": item["narrator"],
                "source": item["source"],
                "topic": item["topic"]
            })

        collection.add(ids=ids, documents=documents, metadatas=metadatas)
        logger.info(f"✅ Indexed {collection.count()} Hadiths into ChromaDB 'hadiths'.")

if __name__ == "__main__":
    main()
