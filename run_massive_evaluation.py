import os
import sys
import io
import json
import time
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

REPORT_FILE = "full_validation_report.json"

def calculate_metrics(results):
    if not results: return {"Accuracy": 0, "Precision": 0, "Recall": 0, "F1": 0}
    tp = sum(1 for r in results if r['ground_truth_error'] and r['detected_error'])
    tn = sum(1 for r in results if not r['ground_truth_error'] and not r['detected_error'])
    fp = sum(1 for r in results if not r['ground_truth_error'] and r['detected_error'])
    fn = sum(1 for r in results if r['ground_truth_error'] and not r['detected_error'])
    
    acc = (tp + tn) / len(results)
    prec = tp / (tp + fp) if (tp + fp) > 0 else 0
    rec = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0
    return {"Accuracy": acc, "Precision": prec, "Recall": rec, "F1": f1, "TP": tp, "TN": tn, "FP": fp, "FN": fn}

def process_chunk(pe, db, chunk, dataset_type):
    chunk_results = []
    for item in chunk:
        try:
            if dataset_type == "mendeley":
                file_path = item
                is_error_gt = (file_path.name[-5] == 'F')
                verse_num = int(file_path.name.split('V')[1][0])
                ref_words = db.get_ayah_phonetics(112, verse_num)
                with open(file_path, "rb") as f: audio_bytes = f.read()
                threshold = 0.5
            elif dataset_type == "qdat":
                row = item
                is_error_gt = (row['separate_tide'] == 0 or row['the_tight_noon'] == 0)
                ref_words = db.get_ayah_phonetics(2, 32)
                audio_bytes = row['audio']['bytes']
                threshold = 0.7
            
            phonetic_result = pe.transcribe_phonetics(audio_bytes)
            act_str = "".join(phonetic_result["words"]).lower()
            exp_str = "".join([w['word_tr'] for w in ref_words]).lower()
            
            sim = TajweedScorer.weighted_similarity(act_str, exp_str)
            detected_error = (sim < threshold)
            
            chunk_results.append({
                "dataset": dataset_type,
                "ground_truth_error": is_error_gt,
                "detected_error": detected_error,
                "similarity": sim
            })
        except Exception as e:
            print(f"Error processing item: {e}")
            continue
    return chunk_results

def run_evaluation():
    print("🚀 Initializing Massive Evaluation Pipeline...")
    pe = PhoneticEngine()
    pe.load()
    db = PhoneticDB()
    db.load()

    # 1. Prepare Datasets
    print("📂 Loading Dataset Paths...")
    MENDELEY_DIR = Path("ai_bridge/data/test_datasets/mendeley_ikhlas/Surah Al-Ikhlas of the Holy Quran Error Detection Dataset/extracted/Dataset and Sounds/Sound recordings")
    mendeley_files = list(MENDELEY_DIR.glob("*.wav"))
    
    QDAT_PATH = Path("ai_bridge/data/test_datasets/qdat.parquet")
    qdat_df = pd.read_parquet(QDAT_PATH)
    qdat_rows = [row for _, row in qdat_df.iterrows()]

    all_work = [
        {"data": mendeley_files, "type": "mendeley"},
        {"data": qdat_rows, "type": "qdat"}
    ]

    total_results = []
    chunk_size = 50
    
    start_time = time.time()
    for work in all_work:
        data = work["data"]
        dtype = work["type"]
        print(f"\n📈 Processing {dtype.upper()} ({len(data)} items)...")
        
        for i in range(0, len(data), chunk_size):
            chunk = data[i : i + chunk_size]
            chunk_results = process_chunk(pe, db, chunk, dtype)
            total_results.extend(chunk_results)
            
            elapsed = time.time() - start_time
            processed = len(total_results)
            items_per_sec = processed / elapsed if elapsed > 0 else 0
            remaining = (len(mendeley_files) + len(qdat_rows) - processed) / items_per_sec if items_per_sec > 0 else 0
            
            print(f"   [{dtype}] Progress: {i + len(chunk)}/{len(data)} | Total: {processed} | Speed: {items_per_sec:.2f} it/s | Est. Left: {remaining/60:.1f}m")
            
            # Periodically save to disk to avoid data loss on crash
            with open(REPORT_FILE, "w") as f:
                json.dump(total_results, f)

    # Final Metrics
    print("\n" + "="*40)
    print("       FINAL GLOBAL VALIDATION REPORT")
    print("="*40)
    
    mendeley_res = [r for r in total_results if r['dataset'] == "mendeley"]
    qdat_res = [r for r in total_results if r['dataset'] == "qdat"]
    
    print("\n--- MENDELEY (1,506 files) ---")
    m_metrics = calculate_metrics(mendeley_res)
    for k, v in m_metrics.items(): print(f"{k}: {v}")

    print("\n--- QDAT (753 files) ---")
    q_metrics = calculate_metrics(qdat_res)
    for k, v in q_metrics.items(): print(f"{k}: {v}")

    print("\n--- GLOBAL AGGREGATE ---")
    g_metrics = calculate_metrics(total_results)
    for k, v in g_metrics.items(): print(f"{k}: {v}")

if __name__ == "__main__":
    run_evaluation()
