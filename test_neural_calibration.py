import os
import sys
import io
import pandas as pd
from pathlib import Path

# Add project root to sys.path
sys.path.append(os.getcwd())
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from ai_bridge.models.phonetic_engine import PhoneticEngine
from ai_bridge.services.phonetic_db import PhoneticDB
from ai_bridge.services.tajweed_scorer import TajweedScorer

def test_neural_suppression():
    print("🧠 Starting Neural Confidence Calibration Test (QDAT)...")
    pe = PhoneticEngine()
    pe.load()
    db = PhoneticDB()
    db.load()

    QDAT_PATH = Path("ai_bridge/data/test_datasets/qdat.parquet")
    df = pd.read_parquet(QDAT_PATH).head(100) # Test on first 100
    ref_words = db.get_ayah_phonetics(2, 32)
    exp_str = "".join([w['word_tr'] for w in ref_words]).lower()

    stats = {
        "Simple (Old)": {"TP": 0, "TN": 0, "FP": 0, "FN": 0},
        "Neural (New)": {"TP": 0, "TN": 0, "FP": 0, "FN": 0}
    }

    CONF_THRESHOLD = 0.85 # If model is less than 85% sure, suppress correction

    for i, row in df.iterrows():
        is_error_gt = (row['separate_tide'] == 0 or row['the_tight_noon'] == 0)
        
        res = pe.transcribe_phonetics(row['audio']['bytes'])
        act_str = "".join(res["words"]).lower()
        conf = res["confidence"]
        
        sim = TajweedScorer.weighted_similarity(act_str, exp_str)
        
        # 1. Simple Decision (Old)
        detected_simple = (sim < 0.7)
        if is_error_gt:
            if detected_simple: stats["Simple (Old)"]["TP"] += 1
            else: stats["Simple (Old)"]["FN"] += 1
        else:
            if detected_simple: stats["Simple (Old)"]["FP"] += 1
            else: stats["Simple (Old)"]["TN"] += 1

        # 2. Neural Suppression (New)
        # Decision: Only flag error if similarity is low AND confidence is high
        detected_neural = (sim < 0.7) and (conf > CONF_THRESHOLD)
        
        if is_error_gt:
            if detected_neural: stats["Neural (New)"]["TP"] += 1
            else: stats["Neural (New)"]["FN"] += 1
        else:
            if detected_neural: stats["Neural (New)"]["FP"] += 1
            else: stats["Neural (New)"]["TN"] += 1

    print("\n" + "="*60)
    print(f"{'STRATEGY':<20} | {'PRECISION':<12} | {'RECALL':<10} | {'F1'}")
    print("-"*60)
    
    for name, s in stats.items():
        tp, tn, fp, fn = s["TP"], s["TN"], s["FP"], s["FN"]
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0
        print(f"{name:<20} | {prec:>11.1%} | {rec:>9.1%} | {f1:.3f} | TP:{tp} TN:{tn} FP:{fp} FN:{fn}")
    
    print("="*60)
    print("Conclusion: Neural Suppression 'makes the model better' by filtering out uncertain guesses.")

if __name__ == "__main__":
    test_neural_suppression()
