print("--- STARTING EVAL SCRIPT ---")
import os
import sys
import io
import time
import random
from pathlib import Path
import torch
import numpy as np

# Add project root to sys.path
sys.path.append(os.getcwd())
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from ai_bridge.models.phonetic_engine import PhoneticEngine
from ai_bridge.services.tajweed_scorer import TajweedScorer
from ai_bridge.services.phonetic_db import PhoneticDB

def evaluate_taxonomy(num_mendeley=50, num_qdat=20, engines=None):
    print("\n" + "="*60)
    print("      TAJWEED ERROR TAXONOMY & PERFORMANCE REPORT")
    print("="*60)

    whisper_engine, phonetic_engine, phonetic_db = engines
    from ai_bridge.services.tajweed_scorer import TajweedScorer

    taxonomy_metrics = {
        "Makharij (Articulation)": {"TP": 0, "TN": 0, "FP": 0, "FN": 0, "Description": "Identity letter swaps (e.g. Qaf vs Kaf)"},
        "Madd (Lengthening)": {"TP": 0, "TN": 0, "FP": 0, "FN": 0, "Description": "Temporal elongation rules"},
        "Ghunnah (Nasalization)": {"TP": 0, "TN": 0, "FP": 0, "FN": 0, "Description": "Noon/Meem Mushaddad"},
        "Vowel Drift": {"TP": 0, "TN": 0, "FP": 0, "FN": 0, "Description": "Fatha/Damma/Kasra shifts"}
    }

    # --- 1. Evaluate Makharij & Vowels (Mendeley) ---
    print(f"\n[1/2] Analyzing Makharij & Vowels (Mendeley Ikhlas)...")
    DATA_DIR = Path("ai_bridge/data/test_datasets/mendeley_ikhlas/Surah Al-Ikhlas of the Holy Quran Error Detection Dataset/extracted/Dataset and Sounds/Sound recordings")
    files = list(DATA_DIR.glob("*.wav"))
    random.seed(42)
    sample_files = random.sample(files, min(len(files), num_mendeley))

    print(f"   Sampled {len(sample_files)} files.")
    for i, file_path in enumerate(sample_files):
        try:
            print(f"      Processing {i+1}/{len(sample_files)}: {file_path.name}")
            is_error_gt = (file_path.name[-5] == 'F')
            verse_num = int(file_path.name.split('V')[1][0])
            ref_words = phonetic_db.get_ayah_phonetics(112, verse_num)
            
            with open(file_path, "rb") as f: audio_bytes = f.read()
            act_str = "".join(phonetic_engine.transcribe_phonetics(audio_bytes)["words"]).lower()
            exp_str = "".join([w['word_tr'] for w in ref_words]).lower()
            
            sim = TajweedScorer.weighted_similarity(act_str, exp_str)
            has_swap = TajweedScorer._has_identity_swap(act_str, exp_str)
            
            # Category: Makharij (if identity swap detected)
            if has_swap or "q" in exp_str or "s" in exp_str:
                detected = (sim < 0.5)
                cat = "Makharij (Articulation)"
                if is_error_gt:
                    if detected: taxonomy_metrics[cat]["TP"] += 1
                    else: taxonomy_metrics[cat]["FN"] += 1
                else:
                    if detected: taxonomy_metrics[cat]["FP"] += 1
                    else: taxonomy_metrics[cat]["TN"] += 1
            
            # Category: Vowel Drift
            if not has_swap:
                detected = (sim < 0.6)
                cat = "Vowel Drift"
                if is_error_gt:
                    if detected: taxonomy_metrics[cat]["TP"] += 1
                    else: taxonomy_metrics[cat]["FN"] += 1
                else:
                    if detected: taxonomy_metrics[cat]["FP"] += 1
                    else: taxonomy_metrics[cat]["TN"] += 1
        except Exception as e:
            print(f"      ERROR processing {file_path.name}: {e}")
            continue

    # --- 2. Evaluate Madd & Ghunnah (QDAT) ---
    print(f"[2/2] Analyzing Madd & Ghunnah (QDAT Baqarah 32)...")
    import pandas as pd
    pq_path = Path("ai_bridge/data/test_datasets/qdat.parquet")
    if pq_path.exists():
        df = pd.read_parquet(pq_path).head(num_qdat)
        ref_words = phonetic_db.get_ayah_phonetics(2, 32)
        exp_str = "".join([w['word_tr'] for w in ref_words]).lower()

        for _, row in df.iterrows():
            # Madd Rule (separate_tide)
            cat = "Madd (Lengthening)"
            is_error_gt = (row['separate_tide'] == 0)
            act_str = "".join(phonetic_engine.transcribe_phonetics(row['audio']['bytes'])["words"]).lower()
            sim = TajweedScorer.weighted_similarity(act_str, exp_str)
            detected = (sim < 0.8) # High precision for studio
            if is_error_gt:
                if detected: taxonomy_metrics[cat]["TP"] += 1
                else: taxonomy_metrics[cat]["FN"] += 1
            else:
                if detected: taxonomy_metrics[cat]["FP"] += 1
                else: taxonomy_metrics[cat]["TN"] += 1

            # Ghunnah Rule (the_tight_noon)
            cat = "Ghunnah (Nasalization)"
            is_error_gt = (row['the_tight_noon'] == 0)
            if is_error_gt:
                if detected: taxonomy_metrics[cat]["TP"] += 1
                else: taxonomy_metrics[cat]["FN"] += 1
            else:
                if detected: taxonomy_metrics[cat]["FP"] += 1
                else: taxonomy_metrics[cat]["TN"] += 1

    # --- Final Report ---
    print("\n" + "-"*80)
    print(f"{'CATEGORY':<25} | {'RECALL':<10} | {'PRECISION':<10} | {'STATUS'}")
    print("-"*80)
    
    for cat, m in taxonomy_metrics.items():
        tp, tn, fp, fn = m["TP"], m["TN"], m["FP"], m["FN"]
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        
        status = "EXCELLENT" if recall > 0.9 else "STABLE" if recall > 0.7 else "IMPROVING"
        print(f"{cat:<25} | {recall:>8.1%} | {precision:>8.1%} | {status}")
    
    print("-"*80)
    print("Pedagogical Note: Major Error Recall is the primary commercial KPI.")
    print("False Correction Rate (1-Precision) is communicated via Confidence UI.")

if __name__ == "__main__":
    import traceback
    try:
        print("Initializing Engines...")
        phonetic_engine = PhoneticEngine()
        phonetic_engine.load()
        print("   Phonetic Engine Loaded.")
        phonetic_db = PhoneticDB()
        phonetic_db.load()
        print("   Phonetic DB Loaded.")
        
        engines = (None, phonetic_engine, phonetic_db)
        evaluate_taxonomy(num_mendeley=10, num_qdat=10, engines=engines)
    except Exception:
        traceback.print_exc()
