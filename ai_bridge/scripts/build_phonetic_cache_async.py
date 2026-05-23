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

CONCURRENCY = 4  # Balanced concurrency
BATCH_SIZE = 100  # Max allowed by HF rows API

async def fetch_batch(client, offset, total_target, retries=3):
    for attempt in range(retries):
        try:
            resp = await client.get(BASE_URL, params={
                "dataset": DATASET_ID,
                "config": "default",
                "split": "train",
                "length": BATCH_SIZE,
                "offset": offset,
            }, timeout=30.0)
            resp.raise_for_status()
            return resp.json().get("rows", [])
        except Exception as e:
            if attempt < retries - 1:
                logger.warning(f"⚠️ Retry {attempt+1} for offset {offset}: {e}")
                await asyncio.sleep(5 * (attempt + 1))
            else:
                logger.error(f"❌ Failed at offset {offset} after {retries} attempts: {e}")
                return None

async def build_cache():
    logger.info(f"📥 Fetching {DATASET_ID} via HF Datasets Server API (Async)...")
    
    data_store = {}
    total_target = 77429
    offset = 0
    
    async with httpx.AsyncClient() as client:
        # Initial request to get the real total count if it differs
        first_batch = await fetch_batch(client, 0, total_target)
        if not first_batch:
            logger.error("❌ Failed to fetch first batch. Aborting.")
            return

        # Process first batch
        def process_rows(rows):
            for rw in rows:
                s = rw.get("row", {})
                sid = s.get("surah_id")
                aid = s.get("ayah_id")
                if sid is None: continue
                key = f"{sid}:{aid}"
                if key not in data_store: data_store[key] = []
                data_store[key].append({
                    "word_index": s.get("word_index", 0),
                    "word_ar": s.get("word_ar", ""),
                    "word_en": s.get("word_en", ""),
                    "word_tr": s.get("word_tr", ""),
                })

        process_rows(first_batch)
        offset = len(first_batch)
        
        # Prepare all offsets
        offsets = list(range(offset, total_target, BATCH_SIZE))
        
        # Fetch in concurrent chunks
        for i in range(0, len(offsets), CONCURRENCY):
            batch_offsets = offsets[i : i + CONCURRENCY]
            tasks = [fetch_batch(client, off, total_target) for off in batch_offsets]
            results = await asyncio.gather(*tasks)
            
            for rows in results:
                if rows:
                    process_rows(rows)
                    offset += len(rows)
            
            await asyncio.sleep(2.0)  # Rate limit safety
            
            pct = (offset / total_target) * 100
            logger.info(f"Progress: {offset}/{total_target} ({pct:.1f}%)")

    logger.info(f"📊 Total words: {sum(len(v) for v in data_store.values())}")
    logger.info(f"📊 Total ayahs: {len(data_store)}")

    # Sort
    logger.info("🧹 Sorting words...")
    for key in data_store:
        data_store[key].sort(key=lambda w: w["word_index"])

    # Save
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"💾 Saving to {CACHE_FILE}...")
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data_store, f, ensure_ascii=False, indent=None)

    size_mb = CACHE_FILE.stat().st_size / 1024 / 1024
    logger.info(f"✅ Cache saved: {CACHE_FILE} ({size_mb:.1f} MB)")

if __name__ == "__main__":
    asyncio.run(build_cache())
