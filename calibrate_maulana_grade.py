import os
import sys
import io
import pandas as pd
from pathlib import Path
import numpy as np

# Add project root to sys.path
sys.path.append(os.getcwd())
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from ai_bridge.models.phonetic_engine import PhoneticEngine
from ai_bridge.services.phonetic_db import PhoneticDB
from ai_bridge.services.tajweed_scorer import TajweedScorer

def calibrate():
    print("🎯 Starting Maulana Grade Calibration Sweep (QDAT Full)...")
    pe = PhoneticEngine()
    pe.load()
    db = PhoneticDB()
    db.load()

    QDAT_PATH = Path("ai_bridge/data/test_datasets/qdat.parquet")
    df = pd.read_parquet(QDAT_PATH)
    ref_words = db.get_ayah_phonetics(2, 32)
    exp_str = "".join([w['word_tr'] for w in ref_words]).lower()

    # Pre-calculate all transcriptions to save time
    results = []
    print(f"   Transcribing {len(df)} files...")
    for i, row in df.iterrows():
        is_error_gt = (row['separate_tide'] == 0 or row['the_tight_noon'] == 0)
        res = pe.transcribe_phonetics(row['audio']['bytes'])
        act_str = "".join(res["words"]).lower()
        sim = TajweedScorer.weighted_similarity(act_str, exp_str)
        results.append((is_error_gt, sim))
        if (i+1) % 100 == 0: print(f"      {i+1}/{len(df)} done.")

    print("\n" + "="*70)
    print(f"{'THRESHOLD':<10} | {'PRECISION':<12} | {'RECALL':<10} | {'F1 SCORE'}")
    print("-"*70)

    best_f1 = 0
    best_thresh = 0

    for thresh in np.arange(0.3, 0.85, 0.05):
        tp = tn = fp = fn = 0
        for is_error_gt, sim in results:
            detected = (sim < thresh)
            if is_error_gt:
                if detected: tp += 1
                else: fn += 1
            else:
                if detected: fp += 1
                else: tn += 1
        
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0
        
        print(f"{thresh:>9.2f} | {prec:>11.1%} | {rec:>9.1%} | {f1:.4f}")
        
        if f1 > best_f1:
            best_f1 = f1
            best_thresh = thresh

    print("="*70)
    print(f"✅ Optimal 'Maulana Grade' Found: {best_thresh:.2f} (F1: {best_f1:.4f})")

if __name__ == "__main__":
    calibrate()
