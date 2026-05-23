import json
from pathlib import Path

CACHE_FILE = Path(__file__).parent.parent / "data" / "phonetic_cache.json"
TOTAL_WORDS = 77429
TOTAL_AYAHS = 6236

def check():
    if not CACHE_FILE.exists():
        print("Error: Cache file not found yet.")
        return

    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        current_ayahs = len(data)
        current_words = sum(len(v) for v in data.values())
        
        word_pct = (current_words / TOTAL_WORDS) * 100
        ayah_pct = (current_ayahs / TOTAL_AYAHS) * 100
        
        print("\n--- PHONETIC CACHE PROGRESS ---")
        print(f"Words: {current_words:,} / {TOTAL_WORDS:,} ({word_pct:.2f}%)")
        print(f"Ayahs: {current_ayahs:,} / {TOTAL_AYAHS:,} ({ayah_pct:.2f}%)")
        
        # Determine last surah:ayah
        keys = sorted(data.keys(), key=lambda x: [int(i) for i in x.split(':')])
        if keys:
            print(f"Coverage: 1:1 up to {keys[-1]}")
        
        print("-" * 33)
        if word_pct < 100:
            print("Status: Actively Building...")
        else:
            print("Status: Complete!")
            
    except Exception as e:
        print(f"Error reading cache: {e}")

if __name__ == "__main__":
    check()
