import os
import sys
import logging
from pathlib import Path
from pypdf import PdfReader

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
CHROMA_DIR = DATA_DIR / "chroma_db"
if os.getenv("HF_HOME") and os.path.exists("/models"):
    CHROMA_DIR = Path("/models/chroma_db")
PDF_PATH = DATA_DIR / "four-madhabs.pdf"
if not PDF_PATH.exists():
    # Fallback to absolute paths or other locations if needed
    for p in [BASE_DIR / "rag" / "four-madhabs.pdf", Path("c:/Users/acer/Downloads/AI/rag/four-madhabs.pdf"), Path("/usr/src/app/rag/four-madhabs.pdf")]:
        if p.exists():
            PDF_PATH = p
            break

def main():
    # 1. Load SentenceTransformer on CPU first to prevent memory/CUDA silent crashes
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

    # 2. Parse the PDF
    if not PDF_PATH.exists():
        logger.error(f"❌ PDF not found at {PDF_PATH}")
        sys.exit(1)

    logger.info(f"📂 Found PDF: {PDF_PATH} ({PDF_PATH.stat().st_size} bytes)")
    reader = PdfReader(PDF_PATH)
    total_pages = len(reader.pages)
    logger.info(f"📄 PDF has {total_pages} pages. Extracting and chunking...")

    chunks = []
    for page_idx in range(total_pages):
        page_num = page_idx + 1
        page = reader.pages[page_idx]
        text = page.extract_text()
        if not text or not text.strip():
            continue

        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        
        # If splitting by double newlines doesn't yield paragraphs, try splitting by single newlines
        # and merging into blocks of appropriate size
        if len(paragraphs) <= 1:
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            paragraphs = []
            current_block = []
            for line in lines:
                current_block.append(line)
                if len(" ".join(current_block)) > 400:
                    paragraphs.append(" ".join(current_block))
                    current_block = []
            if current_block:
                paragraphs.append(" ".join(current_block))

        # Classify default madhab by page range
        default_madhab = "general"
        if 6 <= page_num <= 25:
            default_madhab = "hanafi"
        elif 26 <= page_num <= 35:
            default_madhab = "maliki"
        elif 36 <= page_num <= 49:
            default_madhab = "shafi"
        elif 50 <= page_num <= 59:
            default_madhab = "hanbali"

        for p_idx, para in enumerate(paragraphs):
            para_lower = para.lower()
            madhabs = []
            if "hanafi" in para_lower or "abu hanifa" in para_lower:
                madhabs.append("hanafi")
            if "shafi" in para_lower or "shawaafi" in para_lower:
                madhabs.append("shafi")
            if "maliki" in para_lower or "imam maalik" in para_lower:
                madhabs.append("maliki")
            if "hanbali" in para_lower or "imam ahmad" in para_lower:
                madhabs.append("hanbali")

            # Fallback to default range if no specific madhab is mentioned
            if not madhabs:
                madhabs = [default_madhab]

            # Unique ID
            chunk_id = f"page_{page_num}_p_{p_idx}"
            chunks.append({
                "id": chunk_id,
                "text": para,
                "metadata": {
                    "page": page_num,
                    "paragraph_idx": p_idx,
                    "primary_madhab": madhabs[0] if len(madhabs) == 1 else "multi",
                    "hanafi": "hanafi" in madhabs or "multi" in madhabs,
                    "shafi": "shafi" in madhabs or "multi" in madhabs,
                    "maliki": "maliki" in madhabs or "multi" in madhabs,
                    "hanbali": "hanbali" in madhabs or "multi" in madhabs,
                    "is_fatiha": "fatiha" in para_lower or "recitation" in para_lower or "lahn" in para_lower,
                }
            })

    logger.info(f"🧩 Extracted {len(chunks)} text chunks for indexing.")

    # 3. Connect to ChromaDB
    try:
        import chromadb
    except ImportError:
        logger.error("❌ ChromaDB is not installed in the environment!")
        sys.exit(1)

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    
    # Re-create/get the collection
    try:
        client.delete_collection("madhab_rules")
        logger.info("🗑️ Existing 'madhab_rules' collection deleted.")
    except Exception:
        pass

    collection = client.create_collection(
        name="madhab_rules",
        metadata={"hnsw:space": "cosine"},
        embedding_function=emb_fn
    )

    # 4. Add to vector database in batches
    batch_size = 50
    ids = [c["id"] for c in chunks]
    documents = [c["text"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]

    logger.info("📥 Indexing into ChromaDB 'madhab_rules'...")
    for i in range(0, len(ids), batch_size):
        collection.add(
            ids=ids[i : i + batch_size],
            documents=documents[i : i + batch_size],
            metadatas=metadatas[i : i + batch_size]
        )
        logger.info(f"  Indexed {min(i + batch_size, len(ids))}/{len(ids)} chunks...")

    logger.info(f"✅ Success! Collection 'madhab_rules' has {collection.count()} entries.")

if __name__ == "__main__":
    main()
