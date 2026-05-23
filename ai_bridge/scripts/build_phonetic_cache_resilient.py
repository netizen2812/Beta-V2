import asyncio
import httpx
import json
import logging
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

DATASET_ID = "Buraaq/quran-md-words"
CACHE_DIR = Path(__file__).parent.parent / "data"
CACHE_FILE = CACHE_DIR / "phonetic_cache.json"
BASE_URL = "https://datasets-server.huggingface.co/rows"

BATCH_SIZE = 100 
SAFE_DELAY = 1.5  # Reduced for faster progress

async def fetch_batch(client, offset, retries=5):
    for attempt in range(retries):
        try:
            resp = await client.get(BASE_URL, params={
                "dataset": DATASET_ID,
                "config": "default",
                "split": "train",
                "length": BATCH_SIZE,
                "offset": offset,
            }, timeout=30.0)
            
            if resp.status_code == 429:
                wait_time = 30 * (attempt + 1)
                logger.warning(f"🛑 Rate limited (429) at offset {offset}. Sleeping for {wait_time}s...")
                await asyncio.sleep(wait_time)
                continue
                
            resp.raise_for_status()
            return resp.json().get("rows", [])
        except Exception as e:
            if attempt < retries - 1:
                wait_time = 10 * (attempt + 1)
                logger.warning(f"⚠️ Error at offset {offset}: {e}. Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"❌ Failed at offset {offset} after {retries} attempts: {e}")
                return None

async def build_cache():
    logger.info(f"📥 Starting Resilient Phonetic Cache Builder for {DATASET_ID}")
    
    data_store = {}
    
    # 1. Load existing cache to resume if possible
    if CACHE_FILE.exists():
        logger.info(f"📂 Found existing cache at {CACHE_FILE}. Loading...")
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data_store = json.load(f)
            total_words_loaded = sum(len(v) for v in data_store.values())
            logger.info(f"✅ Loaded {total_words_loaded} words from existing cache.")
        except Exception as e:
            logger.warning(f"⚠️ Could not load existing cache: {e}. Starting fresh.")
            data_store = {}

    total_target = 77429
    # Estimate starting offset based on words loaded
    # NOTE: This assumes the dataset order is stable and no gaps.
    current_offset = sum(len(v) for v in data_store.values())
    
    if current_offset >= total_target:
        logger.info("✨ Cache already complete! (Offset matches target)")
        return

    logger.info(f"🚀 Resuming/Starting from offset: {current_offset}")

    async with httpx.AsyncClient() as client:
        while current_offset < total_target:
            rows = await fetch_batch(client, current_offset)
            
            if rows is None:
                logger.error("🛑 Critical failure during fetch. Saving progress and exiting.")
                break
                
            if not rows:
                logger.info("🏁 No more rows returned. Finshing...")
                break

            for rw in rows:
                s = rw.get("row", {})
                sid = s.get("surah_id")
                aid = s.get("ayah_id")
                if sid is None: continue
                key = f"{sid}:{aid}"
                if key not in data_store: data_store[key] = []
                
                # Avoid duplicates if resuming
                word_idx = s.get("word_index", 0)
                if not any(w["word_index"] == word_idx for w in data_store[key]):
                    data_store[key].append({
                        "word_index": word_idx,
                        "word_ar": s.get("word_ar", ""),
                        "word_en": s.get("word_en", ""),
                        "word_tr": s.get("word_tr", ""),
                    })

            current_offset += len(rows)
            pct = (current_offset / total_target) * 100
            logger.info(f"Progress: {current_offset}/{total_target} ({pct:.1f}%)")
            
            # Save every batch to ensure progress is visible
            if True:
                logger.info("💾 Saving progress...")
                with open(CACHE_FILE, "w", encoding="utf-8") as f:
                    json.dump(data_store, f, ensure_ascii=False)

            await asyncio.sleep(SAFE_DELAY)

    # Final Sort and Save
    logger.info("🧹 Finalizing cache: Sorting and saving...")
    for key in data_store:
        data_store[key].sort(key=lambda w: w["word_index"])

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data_store, f, ensure_ascii=False)

    size_mb = CACHE_FILE.stat().st_size / 1024 / 1024
    logger.info(f"✅ SUCCESS! Cache saved: {CACHE_FILE} ({size_mb:.1f} MB)")

if __name__ == "__main__":
    asyncio.run(build_cache())
