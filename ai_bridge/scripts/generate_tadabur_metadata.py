import json
from pathlib import Path

CACHE_PATH = Path("ai_bridge/data/phonetic_cache.json")
OUTPUT_PATH = Path("ai_bridge/data/tadabur_metadata.json")

def generate():
    if not CACHE_PATH.exists():
        print("Phonetic cache not found!")
        return

    with open(CACHE_PATH, "r", encoding="utf-8") as f:
        cache = json.load(f)

    metadata = {}

    for ayah_id, words in cache.items():
        gold_words = []
        for word_info in words:
            word_tr = word_info["word_tr"]
            
            # Simple heuristic for Madd/Ghunnah
            is_madd = any(v in word_tr.lower() for v in ['ā', 'ī', 'ū', 'aa', 'ee', 'oo'])
            is_ghunnah = any(g in word_tr.lower() for g in ['nn', 'mm'])
            
            # Base duration
            duration = 0.5 + (len(word_tr) * 0.05)
            if is_madd:
                duration += 0.4
            if is_ghunnah:
                duration += 0.3
                
            gold_words.append({
                "word": word_tr,
                "duration": round(duration, 2),
                "is_madd": is_madd or is_ghunnah
            })
            
        metadata[ayah_id] = {"words": gold_words}

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"Generated Tadabur metadata for {len(metadata)} ayahs.")

if __name__ == "__main__":
    generate()
