import os
import sys
import io
import json
import time
import random
from pathlib import Path
import pandas as pd
import numpy as np
import torch
import gc
import builtins

# Add project root to sys.path
sys.path.append(os.getcwd())
sys.stdout.reconfigure(encoding='utf-8')

# Silence the verbose prints from the scoring engines
original_print = builtins.print
def silent_print(*args, **kwargs):
    if args and isinstance(args[0], str) and ("[DEBUG]" in args[0] or "Madd" in args[0] or "Ghunnah" in args[0]):
        return
    original_print(*args, **kwargs)
builtins.print = silent_print

from ai_bridge.models.phonetic_engine import PhoneticEngine
from ai_bridge.services.phonetic_db import PhoneticDB
from ai_bridge.services.tajweed_scorer import TajweedScorer
from ai_bridge.services.voice_processor import VoiceProcessor

# Evaluation constants
MAULANA_GRADE = 0.70
CHECKPOINT_PATH = Path("scratch/evaluation_checkpoint.json")

def local_align_chars(actual: str, reference: str):
    N = len(actual)
    M = len(reference)
    if N == 0 or M == 0:
        return 0, 0, 0.0

    dp = np.zeros((N + 1, M + 1))
    match_score = 2
    mismatch_penalty = -1
    gap_penalty = -1.5

    best_val = 0
    best_cell = (0, 0)

    for i in range(1, N + 1):
        a_char = actual[i-1]
        for j in range(1, M + 1):
            r_char = reference[j-1]
            score_match = match_score if a_char == r_char else mismatch_penalty
            
            s_match = dp[i-1][j-1] + score_match
            s_ins = dp[i-1][j] + gap_penalty
            s_del = dp[i][j-1] + gap_penalty

            val = max(0, s_match, s_ins, s_del)
            dp[i][j] = val

            if val > best_val:
                best_val = val
                best_cell = (i, j)

    if best_val == 0:
        return 0, 0, 0.0

    i, j = best_cell
    end_ref = j - 1
    
    while i > 0 and j > 0 and dp[i][j] > 0:
        a_char = actual[i-1]
        r_char = reference[j-1]
        score_match = match_score if a_char == r_char else mismatch_penalty
        
        s_match = dp[i-1][j-1] + score_match
        s_ins = dp[i-1][j] + gap_penalty
        s_del = dp[i][j-1] + gap_penalty

        max_val = max(s_match, s_ins, s_del)
        if max_val == s_match:
            i -= 1
            j -= 1
        elif max_val == s_ins:
            i -= 1
        else:
            j -= 1

    start_ref = j
    normalized_score = best_val / (match_score * min(N, M))
    return start_ref, end_ref, normalized_score

def calculate_metrics(results):
    if not results:
        return {"Accuracy": 0, "Precision": 0, "Recall": 0, "F1": 0, "TP": 0, "TN": 0, "FP": 0, "FN": 0, "Count": 0}
    tp = sum(1 for r in results if r['gt'] and r['det'])
    tn = sum(1 for r in results if not r['gt'] and not r['det'])
    fp = sum(1 for r in results if not r['gt'] and r['det'])
    fn = sum(1 for r in results if r['gt'] and not r['det'])
    
    count = len(results)
    acc = (tp + tn) / count
    prec = tp / (tp + fp) if (tp + fp) > 0 else 0
    rec = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0
    
    return {
        "Accuracy": acc,
        "Precision": prec,
        "Recall": rec,
        "F1": f1,
        "TP": tp,
        "TN": tn,
        "FP": fp,
        "FN": fn,
        "Count": count
    }

def main():
    original_print("🚀 INITIALIZING OPTIMIZED TAJWEED EVALUATION PIPELINE (NO WHISPER)...")
    
    # 1. Initialize Engines
    original_print("🤖 Loading Wav2Vec2 Phonetic Engine on GPU...")
    pe = PhoneticEngine()
    pe.load()
    db = PhoneticDB()
    db.load()
    original_print("   Engine loaded successfully.")
    
    # 2. Load Datasets
    original_print("📂 Loading Mendeley (1,506) and QDAT (753)...")
    MENDELEY_DIR = Path("ai_bridge/data/test_datasets/mendeley_ikhlas/Surah Al-Ikhlas of the Holy Quran Error Detection Dataset/extracted/Dataset and Sounds/Sound recordings")
    mendeley_files = list(MENDELEY_DIR.glob("*.wav"))
    
    QDAT_PATH = Path("ai_bridge/data/test_datasets/qdat.parquet")
    qdat_df = pd.read_parquet(QDAT_PATH)
    ref_words_qdat = db.get_ayah_phonetics(2, 32)
    exp_str_qdat = "".join([w['word_tr'] for w in ref_words_qdat]).lower()
    
    # Initialize state from checkpoint if available
    checkpoint = {
        "m2_results": {
            "Madd (Timing)": [], "Ghunnah (Nasal)": [], "Makharij (Articulation)": [],
            "Vowel Drift": [], "Global Mendeley": [], "Global QDAT": []
        },
        "m2_times": [],
        "processed_qdat_ids": [],
        "processed_mendeley_names": []
    }
    
    # Make sure scratch dir exists
    Path("scratch").mkdir(exist_ok=True)
    
    if CHECKPOINT_PATH.exists():
        try:
            with open(CHECKPOINT_PATH, "r") as f:
                loaded = json.load(f)
                for k in checkpoint.keys():
                    if k in loaded:
                        checkpoint[k] = loaded[k]
            original_print(f"🔄 Resuming from checkpoint: {len(checkpoint['processed_qdat_ids'])} QDAT and {len(checkpoint['processed_mendeley_names'])} Mendeley processed.")
        except Exception as e:
            original_print(f"⚠️ Failed to load checkpoint ({e}). Starting fresh.")
            
    m2_results = checkpoint["m2_results"]
    m2_times = checkpoint["m2_times"]
    processed_qdat_ids = set(checkpoint["processed_qdat_ids"])
    processed_mendeley_names = set(checkpoint["processed_mendeley_names"])
    
    total_processed = len(processed_qdat_ids) + len(processed_mendeley_names)
    
    def save_checkpoint():
        checkpoint["processed_qdat_ids"] = list(processed_qdat_ids)
        checkpoint["processed_mendeley_names"] = list(processed_mendeley_names)
        with open(CHECKPOINT_PATH, "w") as checkpoint_file:
            json.dump(checkpoint, checkpoint_file)
            
    original_print("\n[1/2] Evaluating QDAT Rules (Madd & Ghunnah)...")
    for idx, row in qdat_df.iterrows():
        qdat_id = row['id']
        if qdat_id in processed_qdat_ids:
            continue
            
        audio_bytes = row['audio']['bytes']
        
        audio_array = VoiceProcessor.process_audio(audio_bytes, 16000)
        if len(audio_array) == 0:
            m2_madd_det = True
            m2_ghunnah_det = True
            is_madd_error = (row['separate_tide'] == 0)
            is_ghunnah_error = (row['the_tight_noon'] == 0)
            is_global_qdat_error = (is_madd_error or is_ghunnah_error)
            m2_global_det = True
            
            m2_results["Madd (Timing)"].append({"gt": is_madd_error, "det": m2_madd_det})
            m2_results["Ghunnah (Nasal)"].append({"gt": is_ghunnah_error, "det": m2_ghunnah_det})
            m2_results["Global QDAT"].append({"gt": is_global_qdat_error, "det": m2_global_det})
            processed_qdat_ids.add(qdat_id)
            total_processed += 1
            continue
            
        # =====================================================================
        # MODEL EVALUATION (WITHOUT WHISPER)
        # =====================================================================
        m2_start = time.time()
        phonetic_result_m2 = pe.transcribe_phonetics(audio_array)
        m2_times.append(time.time() - m2_start)
        
        madd_feedback = TajweedScorer.score_temporal_madd(
            phonetic_result_m2['char_durations'], 
            ref_words_qdat
        )
        ghunnah_feedback = TajweedScorer.score_temporal_ghunnah(
            phonetic_result_m2['char_durations'], 
            ref_words_qdat
        )
        
        m2_madd_det = madd_feedback[4]['error'] if len(madd_feedback) > 4 else False
        m2_ghunnah_det = ghunnah_feedback[8]['error'] if len(ghunnah_feedback) > 8 else False
        
        is_madd_error = (row['separate_tide'] == 0)
        is_ghunnah_error = (row['the_tight_noon'] == 0)
        is_global_qdat_error = (is_madd_error or is_ghunnah_error)
        m2_global_det = (m2_madd_det or m2_ghunnah_det)
        
        m2_results["Madd (Timing)"].append({"gt": is_madd_error, "det": m2_madd_det})
        m2_results["Ghunnah (Nasal)"].append({"gt": is_ghunnah_error, "det": m2_ghunnah_det})
        m2_results["Global QDAT"].append({"gt": is_global_qdat_error, "det": m2_global_det})
        
        processed_qdat_ids.add(qdat_id)
        total_processed += 1
        if total_processed % 50 == 0:
            original_print(f"   Processed {len(processed_qdat_ids)}/753 QDAT files...")
            save_checkpoint()
            gc.collect()
            torch.cuda.empty_cache()
            
    original_print("\n[2/2] Evaluating Mendeley Articulation & Vowels (Makharij & Vowel Drift)...")
    for idx, f in enumerate(mendeley_files):
        f_name = f.name
        if f_name in processed_mendeley_names:
            continue
            
        is_error_gt = (f.name[-5] == 'F')
        verse_num = int(f.name.split('V')[1][0])
        ref_words = db.get_ayah_phonetics(112, verse_num)
        exp_str = "".join([w['word_tr'] for w in ref_words]).lower()
        
        try:
            with open(f, "rb") as audio_file:
                audio_bytes = audio_file.read()
            audio_array = VoiceProcessor.process_audio(audio_bytes, 16000)
        except Exception as e:
            original_print(f"Error loading {f.name}: {e}")
            processed_mendeley_names.add(f_name)
            continue
            
        if len(audio_array) == 0:
            if "q" in exp_str or "s" in exp_str:
                m2_results["Makharij (Articulation)"].append({"gt": is_error_gt, "det": True})
            else:
                m2_results["Vowel Drift"].append({"gt": is_error_gt, "det": True})
            m2_results["Global Mendeley"].append({"gt": is_error_gt, "det": True})
            processed_mendeley_names.add(f_name)
            continue
            
        # =====================================================================
        # MODEL EVALUATION (WITHOUT WHISPER)
        # =====================================================================
        m2_start = time.time()
        phonetic_result_m2 = pe.transcribe_phonetics(audio_array)
        act_str_m2 = "".join(phonetic_result_m2["words"]).lower()
        
        sim_m2 = TajweedScorer.weighted_similarity(act_str_m2, exp_str)
        m2_times.append(time.time() - m2_start)
        
        has_swap_m2 = TajweedScorer._has_identity_swap(act_str_m2, exp_str)
        is_makharij_category_m2 = ("q" in exp_str or "s" in exp_str)
        
        if is_makharij_category_m2:
            m2_det = has_swap_m2 or (sim_m2 < 0.70)
            m2_results["Makharij (Articulation)"].append({"gt": is_error_gt, "det": m2_det})
        else:
            m2_det = (sim_m2 < 0.75)
            m2_results["Vowel Drift"].append({"gt": is_error_gt, "det": m2_det})
            
        m2_global_det = (has_swap_m2 or (sim_m2 < 0.70)) if is_makharij_category_m2 else (sim_m2 < 0.75)
        m2_results["Global Mendeley"].append({"gt": is_error_gt, "det": m2_global_det})
        
        processed_mendeley_names.add(f_name)
        total_processed += 1
        if total_processed % 50 == 0:
            original_print(f"   Processed {len(processed_mendeley_names)}/{len(mendeley_files)} Mendeley files...")
            save_checkpoint()
            gc.collect()
            torch.cuda.empty_cache()
            
    original_print("\n✅ EVALUATION COMPLETED! Generating report...")
    
    # 3. Report Results
    report = {
        "summary": {
            "total_evaluated": total_processed,
            "m2_avg_time_ms": round(np.mean(m2_times) * 1000, 1)
        },
        "model_2": {}
    }
    
    for category in m2_results.keys():
        report["model_2"][category] = calculate_metrics(m2_results[category])
        
    # Print results to stdout
    original_print("\n" + "="*75)
    original_print(f"{'TAJWEED ERROR PRECISION & PERFORMANCE MATRIX':^75}")
    original_print("="*75)
    original_print(f"{'CATEGORY':<25} | {'COUNT':<5} | {'MODEL 2 (OPTIMIZED PIPELINE)':<38}")
    original_print(f"{'':<25} | {'':<5} | {'REC':<6} {'PREC':<6} {'F1':<6} {'(TP/FP/FN)':<10}")
    original_print("-"*75)
    
    for cat in m2_results.keys():
        m2 = report["model_2"][cat]
        m2_counts = f"{m2['TP']}/{m2['FP']}/{m2['FN']}"
        original_print(f"{cat:<25} | {m2['Count']:<5} | "
                       f"{m2['Recall']:>5.1%} {m2['Precision']:>5.1%} {m2['F1']:>5.3f} {m2_counts:<10}")
              
    original_print("="*75)
    original_print(f"Performance Stats:")
    original_print(f"  Optimized Pipeline Average Time per Audio: {report['summary']['m2_avg_time_ms']} ms")
    original_print("="*75)
    
    # Save report to json
    out_path = Path("scratch/evaluation_results.json")
    with open(out_path, "w") as f:
        json.dump(report, f, indent=4)
    original_print(f"Saved evaluation results to {out_path}")
    
    # Delete checkpoint file on successful completion
    if CHECKPOINT_PATH.exists():
        try:
            CHECKPOINT_PATH.unlink()
            original_print("🧹 Checkpoint cleared.")
        except Exception:
            pass

if __name__ == "__main__":
    main()
