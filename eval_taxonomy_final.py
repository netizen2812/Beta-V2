import os
import sys
import io
import random
from pathlib import Path

# Add project root to sys.path
sys.path.append(os.getcwd())
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def calculate_metrics(results):
    tp = sum(1 for r in results if r['ground_truth_error'] and r['detected_error'])
    tn = sum(1 for r in results if not r['ground_truth_error'] and not r['detected_error'])
    fp = sum(1 for r in results if not r['ground_truth_error'] and r['detected_error'])
    fn = sum(1 for r in results if r['ground_truth_error'] and not r['detected_error'])
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    return recall, precision

def run_taxonomy():
    from ai_bridge.models.phonetic_engine import PhoneticEngine
    from ai_bridge.services.phonetic_db import PhoneticDB
    from ai_bridge.services.tajweed_scorer import TajweedScorer
    import pandas as pd

    pe = PhoneticEngine()
    pe.load()
    db = PhoneticDB()
    db.load()

    taxonomy = {
        "Makharij": [],
        "Rules (Madd/Ghunnah)": [],
        "Vowels": []
    }

    # 1. Rules from QDAT
    pq_path = Path("ai_bridge/data/test_datasets/qdat.parquet")
    if pq_path.exists():
        df = pd.read_parquet(pq_path).head(20)
        ref_words = db.get_ayah_phonetics(2, 32)
        exp_str = "".join([w['word_tr'] for w in ref_words]).lower()
        for _, row in df.iterrows():
            is_error = (row['separate_tide'] == 0 or row['the_tight_noon'] == 0)
            act_str = "".join(pe.transcribe_phonetics(row['audio']['bytes'])["words"]).lower()
            sim = TajweedScorer.weighted_similarity(act_str, exp_str)
            detected = (sim < 0.7)
            taxonomy["Rules (Madd/Ghunnah)"].append({"ground_truth_error": is_error, "detected_error": detected})

    # 2. Makharij from Mendeley
    DATA_DIR = Path("ai_bridge/data/test_datasets/mendeley_ikhlas/Surah Al-Ikhlas of the Holy Quran Error Detection Dataset/extracted/Dataset and Sounds/Sound recordings")
    files = list(DATA_DIR.glob("*.wav"))
    sample = random.sample(files, 20)
    for f in sample:
        is_error = (f.name[-5] == 'F')
        verse_num = int(f.name.split('V')[1][0])
        ref_words = db.get_ayah_phonetics(112, verse_num)
        act_str = "".join(pe.transcribe_phonetics(open(f, "rb").read())["words"]).lower()
        exp_str = "".join([w['word_tr'] for w in ref_words]).lower()
        sim = TajweedScorer.weighted_similarity(act_str, exp_str)
        has_swap = TajweedScorer._has_identity_swap(act_str, exp_str)
        detected = (sim < 0.5)
        if has_swap or "q" in exp_str or "s" in exp_str:
            taxonomy["Makharij"].append({"ground_truth_error": is_error, "detected_error": detected})
        else:
            taxonomy["Vowels"].append({"ground_truth_error": is_error, "detected_error": detected})

    print("\n--- TAXONOMY REPORT ---")
    for cat, results in taxonomy.items():
        if not results: continue
        rec, prec = calculate_metrics(results)
        print(f"{cat:<25} | Recall: {rec:>8.1%} | Precision: {prec:>8.1%}")

if __name__ == "__main__":
    run_taxonomy()
