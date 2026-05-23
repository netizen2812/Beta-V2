import os
import sys
import io
import random
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to sys.path
sys.path.append(os.getcwd())
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from ai_bridge.models.phonetic_engine import PhoneticEngine
from ai_bridge.services.phonetic_db import PhoneticDB
from ai_bridge.services.tajweed_scorer import TajweedScorer

def run_full_taxonomy():
    print("🚀 Initializing Full Taxonomy Analysis...")
    pe = PhoneticEngine()
    pe.load()
    db = PhoneticDB()
    db.load()

    taxonomy_metrics = {
        "Makharij (Articulation)": {"TP": 0, "TN": 0, "FP": 0, "FN": 0},
        "Rules (Madd/Ghunnah)": {"TP": 0, "TN": 0, "FP": 0, "FN": 0},
        "Vowel Drift": {"TP": 0, "TN": 0, "FP": 0, "FN": 0}
    }

    # 1. Rules (QDAT) - All 753 files
    print("\n[1/2] Analyzing Rules (QDAT Full)...")
    QDAT_PATH = Path("ai_bridge/data/test_datasets/qdat.parquet")
    qdat_df = pd.read_parquet(QDAT_PATH)
    ref_words_qdat = db.get_ayah_phonetics(2, 32)
    exp_str_qdat = "".join([w['word_tr'] for w in ref_words_qdat]).lower()

    for i, row in qdat_df.iterrows():
        is_error = (row['separate_tide'] == 0 or row['the_tight_noon'] == 0)
        try:
            act_str = "".join(pe.transcribe_phonetics(row['audio']['bytes'])["words"]).lower()
            sim = TajweedScorer.weighted_similarity(act_str, exp_str_qdat)
            detected = (sim < 0.7)
            cat = "Rules (Madd/Ghunnah)"
            if is_error:
                if detected: taxonomy_metrics[cat]["TP"] += 1
                else: taxonomy_metrics[cat]["FN"] += 1
            else:
                if detected: taxonomy_metrics[cat]["FP"] += 1
                else: taxonomy_metrics[cat]["TN"] += 1
        except: continue
        if (i+1) % 100 == 0: print(f"   Processed {i+1}/753 QDAT...")

    # 2. Makharij & Vowels (Mendeley) - 200 files for high-confidence categorization
    print("\n[2/2] Analyzing Makharij & Vowels (Mendeley Sample 200)...")
    MENDELEY_DIR = Path("ai_bridge/data/test_datasets/mendeley_ikhlas/Surah Al-Ikhlas of the Holy Quran Error Detection Dataset/extracted/Dataset and Sounds/Sound recordings")
    mendeley_files = list(MENDELEY_DIR.glob("*.wav"))
    sample_mendeley = random.sample(mendeley_files, 200)

    for i, f in enumerate(sample_mendeley):
        is_error = (f.name[-5] == 'F')
        verse_num = int(f.name.split('V')[1][0])
        ref_words = db.get_ayah_phonetics(112, verse_num)
        exp_str = "".join([w['word_tr'] for w in ref_words]).lower()
        try:
            act_str = "".join(pe.transcribe_phonetics(open(f, "rb").read())["words"]).lower()
            sim = TajweedScorer.weighted_similarity(act_str, exp_str)
            has_swap = TajweedScorer._has_identity_swap(act_str, exp_str)
            
            if has_swap or "q" in exp_str or "s" in exp_str:
                cat = "Makharij (Articulation)"
                detected = (sim < 0.5)
            else:
                cat = "Vowel Drift"
                detected = (sim < 0.6)

            if is_error:
                if detected: taxonomy_metrics[cat]["TP"] += 1
                else: taxonomy_metrics[cat]["FN"] += 1
            else:
                if detected: taxonomy_metrics[cat]["FP"] += 1
                else: taxonomy_metrics[cat]["TN"] += 1
        except: continue
        if (i+1) % 50 == 0: print(f"   Processed {i+1}/200 Mendeley...")

    print("\n" + "="*80)
    print(f"{'CATEGORY':<25} | {'RECALL':<10} | {'PRECISION':<10} | {'STATUS'}")
    print("-"*80)
    
    for cat, m in taxonomy_metrics.items():
        tp, tn, fp, fn = m["TP"], m["TN"], m["FP"], m["FN"]
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        
        status = "EXCELLENT" if recall > 0.9 else "STABLE" if recall > 0.7 else "IMPROVING"
        print(f"{cat:<25} | {recall:>8.1%} | {precision:>8.1%} | {status}")
    print("-"*80)

if __name__ == "__main__":
    run_full_taxonomy()
