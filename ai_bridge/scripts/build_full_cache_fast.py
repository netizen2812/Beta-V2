"""
High-Speed Phonetic Cache Builder (Full Quran).
Uses HuggingFace 'streaming' mode to skip audio data and fetch
only text metadata for all 77,429 words in seconds/minutes.
"""

import os
import json
import logging
from pathlib import Path

# Setup logging to see progress
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

DATASET_ID = "Buraaq/quran-md-words"
CACHE_DIR = Path(__file__).parent.parent / "data"
CACHE_FILE = CACHE_DIR / "phonetic_cache.json"

def build_full_cache():
    try:
        from datasets import load_dataset
    except ImportError:
        logger.error("❌ 'datasets' package not found. Run: pip install datasets")
        return

    logger.info(f"📥 Loading {DATASET_ID} in streaming mode...")
    
    # Streaming=True is the KEY here. It avoids downloading the 2GB audio files.
    dataset = load_dataset(DATASET_ID, split="train", streaming=True)
    
    # Try to remove audio column to avoid decode errors
    dataset = dataset.remove_columns(["audio"])
    
    # We only care about these columns
    target_columns = ["surah_id", "ayah_id", "word_index", "word_ar", "word_en", "word_tr"]
    
    data_store = {}
    count = 0
    
    logger.info("🚀 Starting extraction (this should be FAST)...")
    
    for sample in dataset:
        sid = sample.get("surah_id")
        aid = sample.get("ayah_id")
        if sid is None or aid is None:
            continue
            
        key = f"{sid}:{aid}"
        if key not in data_store:
            data_store[key] = []
            
        data_store[key].append({
            "word_index": sample.get("word_index", 0),
            "word_ar": sample.get("word_ar", ""),
            "word_en": sample.get("word_en", ""),
            "word_tr": sample.get("word_tr", ""),
        })
        
        count += 1
        if count % 5000 == 0:
            logger.info(f"  Processed {count} words...")

    logger.info(f"✅ Extraction complete. Total words: {count}")
    logger.info(f"📊 Total Ayahs: {len(data_store)}")

    # Sort words by index within each ayah
    logger.info("🧹 Sorting words...")
    for key in data_store:
        data_store[key].sort(key=lambda w: w["word_index"])

    # Save to JSON
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"💾 Saving to {CACHE_FILE}...")
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data_store, f, ensure_ascii=False, indent=None)

    size_mb = CACHE_FILE.stat().st_size / 1024 / 1024
    logger.info(f"✨ SUCCESS! Full Quran Phonetic Cache built ({size_mb:.1f} MB)")

if __name__ == "__main__":
    build_full_cache()
