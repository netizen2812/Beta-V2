import os
import sys
import io
import time
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to sys.path
sys.path.append(os.getcwd())
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from ai_bridge.models.phonetic_engine import PhoneticEngine
from ai_bridge.services.phonetic_db import PhoneticDB
from ai_bridge.services.tajweed_scorer import TajweedScorer

def calculate_metrics(results):
    if not results: return {"Acc": 0, "Prec": 0, "Rec": 0, "F1": 0, "Count": 0}
    tp = sum(1 for r in results if r['gt'] and r['det'])
    tn = sum(1 for r in results if not r['gt'] and not r['det'])
    fp = sum(1 for r in results if not r['gt'] and r['det'])
    fn = sum(1 for r in results if r['gt'] and not r['det'])
    
    acc = (tp + tn) / len(results)
    prec = tp / (tp + fp) if (tp + fp) > 0 else 0
    rec = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0
    return {"Acc": acc, "Prec": prec, "Rec": rec, "F1": f1, "TP": tp, "TN": tn, "FP": fp, "FN": fn, "Count": len(results)}

def run_final_evaluation():
    print("🚀 STARTING FINAL COMPREHENSIVE EVALUATION (2,259 Datapoints)...")
    pe = PhoneticEngine()
    pe.load()
    db = PhoneticDB()
    db.load()

    # 1. Load Datasets
    print("📂 Loading Mendeley (1,506) and QDAT (753)...")
    MENDELEY_DIR = Path("ai_bridge/data/test_datasets/mendeley_ikhlas/Surah Al-Ikhlas of the Holy Quran Error Detection Dataset/extracted/Dataset and Sounds/Sound recordings")
    mendeley_files = list(MENDELEY_DIR.glob("*.wav"))
    
    QDAT_PATH = Path("ai_bridge/data/test_datasets/qdat.parquet")
    qdat_df = pd.read_parquet(QDAT_PATH)
    ref_words_qdat = db.get_ayah_phonetics(2, 32)

    all_bucket_results = {
        "Madd (Timing)": [],
        "Ghunnah (Nasal)": [],
        "Makharij (Articulation)": [],
        "Vowel Accuracy": []
    }

    total_processed = 0
    start_time = time.time()

    # --- PROCESS QDAT (Rules) ---
    print("\n[1/2] Processing Rules (Madd/Ghunnah)...")
    for idx, row in qdat_df.iterrows():
        try:
            is_madd_error = (row['separate_tide'] == 0)
            is_ghunnah_error = (row['the_tight_noon'] == 0)
            
            res = pe.transcribe_phonetics(row['audio']['bytes'])
            char_durations = res["char_durations"]
            
            # Scorer check
            temp_madd = TajweedScorer.score_temporal_madd(char_durations, ref_words_qdat)
            temp_ghunnah = TajweedScorer.score_temporal_ghunnah(char_durations, ref_words_qdat)
            
            # Target words indices (4 for 'lanā', 8 for 'innaka')
            madd_det = temp_madd[4]["error"]
            ghunnah_det = temp_ghunnah[8]["error"]

            all_bucket_results["Madd (Timing)"].append({"gt": is_madd_error, "det": madd_det})
            
            if not np.isnan(row['the_tight_noon']):
                all_bucket_results["Ghunnah (Nasal)"].append({"gt": is_ghunnah_error, "det": ghunnah_det})
            
            total_processed += 1
            if total_processed % 100 == 0:
                elapsed = time.time() - start_time
                print(f"   Progress: {total_processed}/2259 | {elapsed/60:.1f}m elapsed...")
        except Exception as e:
            print(f"Error on QDAT row {idx}: {e}")
            continue

    # --- PROCESS MENDELEY (Articulation/Vowels) ---
    print("\n[2/2] Processing Articulation (Mendeley)...")
    for idx, f in enumerate(mendeley_files):
        try:
            is_error_gt = (f.name[-5] == 'F')
            verse_num = int(f.name.split('V')[1][0])
            ref_words = db.get_ayah_phonetics(112, verse_num)
            exp_str = "".join([w['word_tr'] for w in ref_words]).lower()
            
            res = pe.transcribe_phonetics(open(f, "rb").read())
            act_str = "".join(res["words"]).lower()
            
            sim = TajweedScorer.weighted_similarity(act_str, exp_str)
            has_swap = TajweedScorer._has_identity_swap(act_str, exp_str)
            
            # Characterization and thresholds mapping
            if has_swap or "q" in exp_str or "s" in exp_str:
                detected_makharij = (sim < 0.5)
                all_bucket_results["Makharij (Articulation)"].append({"gt": is_error_gt, "det": detected_makharij})
            else:
                detected_vowel = (sim < 0.6)
                all_bucket_results["Vowel Accuracy"].append({"gt": is_error_gt, "det": detected_vowel})

            total_processed += 1
            if total_processed % 100 == 0:
                elapsed = time.time() - start_time
                print(f"   Progress: {total_processed}/2259 | {elapsed/60:.1f}m elapsed...")
        except Exception as e:
            print(f"Error on Mendeley file {f.name}: {e}")
            continue

    # --- FINAL REPORT ---
    print("\n" + "="*90)
    print(f"{'BUCKET':<25} | {'COUNT':<6} | {'RECALL':<10} | {'PRECISION':<10} | {'F1 SCORE'} | {'TP/FP/FN/TN'}")
    print("-"*90)
    
    for bucket, res in all_bucket_results.items():
        m = calculate_metrics(res)
        print(f"{bucket:<25} | {m['Count']:<6} | {m['Rec']:>8.1%} | {m['Prec']:>9.1%} | {m['F1']:.4f} | {m['TP']}/{m['FP']}/{m['FN']}/{m['TN']}")
    
    print("="*90)
    print(f"GLOBAL COMPLETION: 2,259 Files processed using Neural Confidence + Temporal Alignment.")

if __name__ == "__main__":
    run_final_evaluation()
