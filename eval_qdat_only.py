import os
import sys
import io
import pandas as pd
from pathlib import Path
import torch

# Add project root to sys.path
sys.path.append(os.getcwd())
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from ai_bridge.models.whisper_engine import WhisperEngine
from ai_bridge.models.phonetic_engine import PhoneticEngine
from ai_bridge.services.tajweed_scorer import TajweedScorer
from ai_bridge.services.phonetic_db import PhoneticDB

def calculate_metrics(results):
    tp = sum(1 for r in results if r['ground_truth_error'] and r['detected_error'])
    tn = sum(1 for r in results if not r['ground_truth_error'] and not r['detected_error'])
    fp = sum(1 for r in results if not r['ground_truth_error'] and r['detected_error'])
    fn = sum(1 for r in results if r['ground_truth_error'] and not r['detected_error'])
    
    acc = (tp + tn) / len(results) if results else 0
    prec = tp / (tp + fp) if (tp + fp) > 0 else 0
    rec = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0
    return {"Accuracy": acc, "Precision": prec, "Recall": rec, "F1": f1, "TP": tp, "TN": tn, "FP": fp, "FN": fn}

def evaluate_qdat(num_samples=20):
    print(f"\n--- EVALUATING QDAT DATASET ({num_samples} samples) ---")
    pq_path = Path("ai_bridge/data/test_datasets/qdat.parquet")
    if not pq_path.exists():
        print("QDAT Parquet not found!")
        return
        
    df = pd.read_parquet(pq_path)
    df_sample = df.head(num_samples)

    whisper_engine = WhisperEngine()
    whisper_engine.load()
    phonetic_engine = PhoneticEngine()
    phonetic_engine.load()
    phonetic_db = PhoneticDB()
    phonetic_db.load()

    ref_words = phonetic_db.get_ayah_phonetics(2, 32)
    exp_str = "".join([w['word_tr'] for w in ref_words]).lower()

    results = []
    for i, row in df_sample.iterrows():
        audio_bytes = row['audio']['bytes']
        is_error_gt = (row['separate_tide'] == 0 or row['the_tight_noon'] == 0)
        
        phonetic_result = phonetic_engine.transcribe_phonetics(audio_bytes)
        act_str = "".join(phonetic_result["words"]).lower()
        
        sim = TajweedScorer.weighted_similarity(act_str, exp_str)
        detected_error = (sim < 0.7)
        results.append({'ground_truth_error': is_error_gt, 'detected_error': detected_error})
        print(f"   Sample {i+1} | Label: {'E' if is_error_gt else 'C'} | Detected: {'E' if detected_error else 'C'} | Sim: {sim:.2f}")

    m = calculate_metrics(results)
    for k, v in m.items():
        if isinstance(v, float): print(f"{k}: {v:.2%}")
        else: print(f"{k}: {v}")

if __name__ == "__main__":
    evaluate_qdat(20)
