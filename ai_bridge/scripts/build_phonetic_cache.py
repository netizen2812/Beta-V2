"""
Build phonetic cache from HuggingFace Datasets Server API.

Downloads 77,429 word entries from Buraaq/quran-md-words
(text-only, no audio) and saves as a JSON cache file.

Run once: python scripts/build_phonetic_cache.py
~Takes 30-40 minutes via the rows API.
"""

import sys
import os
import json
import httpx
from pathlib import Path

DATASET_ID = "Buraaq/quran-md-words"
CACHE_DIR = Path(__file__).parent.parent / "data"
CACHE_FILE = CACHE_DIR / "phonetic_cache.json"


def build_cache():
    print(f"📥 Fetching {DATASET_ID} via HF Datasets Server API...")
    print(f"   This will take 30-40 minutes. Cache will be saved to {CACHE_FILE}")
    print()

    base_url = "https://datasets-server.huggingface.co/rows"
    data_store = {}
    offset = 0
    total_target = 77429

    while offset < total_target:
        try:
            resp = httpx.get(base_url, params={
                "dataset": DATASET_ID,
                "config": "default",
                "split": "train",
                "length": 100,
                "offset": offset,
            }, timeout=30.0)
            resp.raise_for_status()
            result = resp.json()
        except Exception as e:
            print(f"❌ Failed at offset {offset}: {e}")
            print("   Retrying in 5s...")
            import time
            time.sleep(5)
            continue

        rows = result.get("rows", [])
        if not rows:
            break

        total_target = result.get("num_rows_total", total_target)

        for rw in rows:
            s = rw.get("row", {})
            sid = s.get("surah_id")
            aid = s.get("ayah_id")
            if sid is None:
                continue
            key = f"{sid}:{aid}"
            if key not in data_store:
                data_store[key] = []
            data_store[key].append({
                "word_index": s.get("word_index", 0),
                "word_ar": s.get("word_ar", ""),
                "word_en": s.get("word_en", ""),
                "word_tr": s.get("word_tr", ""),
            })

        offset += len(rows)
        pct = (offset / total_target) * 100
        print(f"\r  Progress: {offset}/{total_target} ({pct:.1f}%)", end="", flush=True)

    print()
    print(f"📊 Total words: {sum(len(v) for v in data_store.values())}")
    print(f"📊 Total ayahs: {len(data_store)}")

    # Sort
    for key in data_store:
        data_store[key].sort(key=lambda w: w["word_index"])

    # Save
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data_store, f, ensure_ascii=False, indent=None)

    size_mb = CACHE_FILE.stat().st_size / 1024 / 1024
    print(f"✅ Cache saved: {CACHE_FILE} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    if CACHE_FILE.exists():
        print(f"⚠️  Cache already exists: {CACHE_FILE}")
        print("   Delete it first to rebuild.")
        resp = input("   Delete and rebuild? (y/n): ")
        if resp.lower() != "y":
            print("   Skipped.")
            sys.exit(0)
        CACHE_FILE.unlink()

    build_cache()
