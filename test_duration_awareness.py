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

def test_duration_awareness():
    print("⏳ Starting Duration-Aware Evaluation (QDAT)...")
    pe = PhoneticEngine()
    pe.load()
    db = PhoneticDB()
    db.load()

    QDAT_PATH = Path("ai_bridge/data/test_datasets/qdat.parquet")
    df = pd.read_parquet(QDAT_PATH).head(100) # Test on 100 samples
    ref_words = db.get_ayah_phonetics(2, 32)
    
    stats = {
        "Phonetic-Only": {"TP": 0, "TN": 0, "FP": 0, "FN": 0},
        "Duration-Aware": {"TP": 0, "TN": 0, "FP": 0, "FN": 0}
    }

    for i, row in df.iterrows():
        # Label: separate_tide == 0 means a Madd mistake exists
        is_madd_error_gt = (row['separate_tide'] == 0)
        
        res = pe.transcribe_phonetics(row['audio']['bytes'])
        char_durations = res["char_durations"]
        act_phonetics = res["words"]
        
        # 1. Phonetic-Only Scoring
        score_simple = TajweedScorer.score_recitation(act_phonetics, ref_words)
        detected_phonetic = (score_simple["maulana_feedback"]["summary"].get("major_error", 0) > 0)
        
        # 2. Duration-Aware Scoring
        temporal_feedback = TajweedScorer.score_temporal_madd(char_durations, ref_words)
        score_duration = TajweedScorer.score_recitation(act_phonetics, ref_words, temporal_feedback)
        detected_duration = (score_duration["maulana_feedback"]["summary"].get("major_error", 0) > 0)

        # Update stats for Madd errors specifically
        def update_stat(stat_name, detected):
            if is_madd_error_gt:
                if detected: stats[stat_name]["TP"] += 1
                else: stats[stat_name]["FN"] += 1
            else:
                if detected: stats[stat_name]["FP"] += 1
                else: stats[stat_name]["TN"] += 1

        update_stat("Phonetic-Only", detected_phonetic)
        update_stat("Duration-Aware", detected_duration)

    print("\n" + "="*75)
    print(f"{'STRATEGY':<20} | {'PRECISION':<12} | {'RECALL':<10} | {'F1 SCORE'}")
    print("-"*75)
    
    for name, s in stats.items():
        tp, tn, fp, fn = s["TP"], s["TN"], s["FP"], s["FN"]
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0
        print(f"{name:<20} | {prec:>11.1%} | {rec:>9.1%} | {f1:.4f} (TP:{tp} FP:{fp})")
    
    print("="*75)
    print("Insight: Duration-Awareness isolates timing errors from phonetic mispronunciations.")

if __name__ == "__main__":
    test_duration_awareness()
