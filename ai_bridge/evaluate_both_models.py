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
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Silence the verbose prints from the scoring engines
original_print = builtins.print
def silent_print(*args, **kwargs):
    if args and isinstance(args[0], str) and ("[DEBUG]" in args[0] or "Madd" in args[0] or "Ghunnah" in args[0]):
        return
    original_print(*args, **kwargs)
builtins.print = silent_print

from ai_bridge.models.whisper_engine import WhisperEngine
from ai_bridge.models.phonetic_engine import PhoneticEngine
from ai_bridge.services.phonetic_db import PhoneticDB
from ai_bridge.services.tajweed_scorer import TajweedScorer
from ai_bridge.services.voice_processor import VoiceProcessor
from ai_bridge.services.alignment import AlignmentEngine

# Evaluation constants
MAULANA_GRADE = 0.55
CONF_THRESHOLD = 0.85
CHECKPOINT_PATH = Path("scratch/evaluation_checkpoint.json")

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
    original_print("🚀 INITIALIZING COMPREHENSIVE TAJWEED EVALUATION PIPELINE...")
    
    # 1. Initialize Engines
    original_print("🤖 Loading Neural Engines on GPU...")
    we = WhisperEngine()
    we.load()
    pe = PhoneticEngine()
    pe.load()
    db = PhoneticDB()
    db.load()
    original_print("   Engines loaded successfully.")
    
    # Monkeypatch Whisper transcribe to restrict tokens and speed up generation
    def custom_transcribe(audio_bytes, mime_type="audio/webm"):
        if isinstance(audio_bytes, np.ndarray):
            audio_array = audio_bytes
        else:
            audio_array = we._bytes_to_array(audio_bytes)
        if len(audio_array) == 0:
            return {"text": "", "chunks": []}
        
        result = we.pipe(
            audio_array,
            generate_kwargs={"max_new_tokens": 40},
            return_timestamps=False,
        )
        return {
            "text": result.get("text", "").strip(),
            "chunks": result.get("chunks", []),
        }
    we.transcribe = custom_transcribe
    original_print("   Optimized Whisper max_new_tokens=40 for speed.")
    
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
        "m1_results": {
            "Madd (Timing)": [], "Ghunnah (Nasal)": [], "Makharij (Articulation)": [],
            "Vowel Drift": [], "Global Mendeley": [], "Global QDAT": []
        },
        "m2_results": {
            "Madd (Timing)": [], "Ghunnah (Nasal)": [], "Makharij (Articulation)": [],
            "Vowel Drift": [], "Global Mendeley": [], "Global QDAT": []
        },
        "m1_times": [],
        "m2_times": [],
        "processed_qdat_ids": [],
        "processed_mendeley_names": [],
        "whisper_empty_count": 0
    }
    
    # Make sure scratch dir exists
    Path("scratch").mkdir(exist_ok=True)
    
    if CHECKPOINT_PATH.exists():
        try:
            with open(CHECKPOINT_PATH, "r") as f:
                loaded = json.load(f)
                # Merge loaded keys to handle any structural updates
                for k in checkpoint.keys():
                    if k in loaded:
                        checkpoint[k] = loaded[k]
            original_print(f"🔄 Resuming from checkpoint: {len(checkpoint['processed_qdat_ids'])} QDAT and {len(checkpoint['processed_mendeley_names'])} Mendeley processed.")
        except Exception as e:
            original_print(f"⚠️ Failed to load checkpoint ({e}). Starting fresh.")
            
    m1_results = checkpoint["m1_results"]
    m2_results = checkpoint["m2_results"]
    m1_times = checkpoint["m1_times"]
    m2_times = checkpoint["m2_times"]
    processed_qdat_ids = set(checkpoint["processed_qdat_ids"])
    processed_mendeley_names = set(checkpoint["processed_mendeley_names"])
    whisper_empty_count = checkpoint["whisper_empty_count"]
    
    total_processed = len(processed_qdat_ids) + len(processed_mendeley_names)
    
    def save_checkpoint():
        checkpoint["processed_qdat_ids"] = list(processed_qdat_ids)
        checkpoint["processed_mendeley_names"] = list(processed_mendeley_names)
        checkpoint["whisper_empty_count"] = whisper_empty_count
        with open(CHECKPOINT_PATH, "w") as checkpoint_file:
            json.dump(checkpoint, checkpoint_file)
            
    original_print("\n[1/2] Evaluating QDAT Rules (Madd & Ghunnah)...")
    for idx, row in qdat_df.iterrows():
        qdat_id = row['id']
        if qdat_id in processed_qdat_ids:
            continue
            
        audio_bytes = row['audio']['bytes']
        is_madd_error = (row['separate_tide'] == 0)
        is_ghunnah_error = (row['the_tight_noon'] == 0)
        is_global_qdat_error = (is_madd_error or is_ghunnah_error)
        
        audio_array = VoiceProcessor.process_audio(audio_bytes, 16000)
        if len(audio_array) == 0:
            for model_res in [m1_results, m2_results]:
                model_res["Madd (Timing)"].append({"gt": is_madd_error, "det": True})
                model_res["Ghunnah (Nasal)"].append({"gt": is_ghunnah_error, "det": True})
                model_res["Global QDAT"].append({"gt": is_global_qdat_error, "det": True})
            processed_qdat_ids.add(qdat_id)
            continue
            
        # =====================================================================
        # MODEL 1: WITH WHISPER
        # =====================================================================
        m1_start = time.time()
        whisper_res = we.transcribe(audio_array)
        trans_text = whisper_res.get("text", "").strip()
        
        if not trans_text:
            m1_madd_det = True
            m1_ghunnah_det = True
            m1_global_det = True
            whisper_empty_count += 1
        else:
            phonetic_result = pe.transcribe_phonetics(audio_array)
            act_str = "".join(phonetic_result["words"]).lower()
            conf = phonetic_result["confidence"]
            durations = phonetic_result["char_durations"]
            
            sim = TajweedScorer.weighted_similarity(act_str, exp_str_qdat)
            temp_madd = TajweedScorer.score_temporal_madd(durations, ref_words_qdat)
            temp_ghunnah = TajweedScorer.score_temporal_ghunnah(durations, ref_words_qdat)
            
            m1_madd_det = (sim < MAULANA_GRADE) and (conf > CONF_THRESHOLD) or any(t['error'] for t in temp_madd)
            m1_ghunnah_det = (sim < MAULANA_GRADE) and (conf > CONF_THRESHOLD) or any(t['error'] for t in temp_ghunnah)
            m1_global_det = (m1_madd_det or m1_ghunnah_det)
            
        m1_times.append(time.time() - m1_start)
        
        m1_results["Madd (Timing)"].append({"gt": is_madd_error, "det": m1_madd_det})
        m1_results["Ghunnah (Nasal)"].append({"gt": is_ghunnah_error, "det": m1_ghunnah_det})
        m1_results["Global QDAT"].append({"gt": is_global_qdat_error, "det": m1_global_det})
        
        # =====================================================================
        # MODEL 2: WITHOUT WHISPER
        # =====================================================================
        m2_start = time.time()
        phonetic_result_m2 = pe.transcribe_phonetics(audio_array)
        act_str_m2 = "".join(phonetic_result_m2["words"]).lower()
        conf_m2 = phonetic_result_m2["confidence"]
        durations_m2 = phonetic_result_m2["char_durations"]
        
        sim_m2 = TajweedScorer.weighted_similarity(act_str_m2, exp_str_qdat)
        temp_madd_m2 = TajweedScorer.score_temporal_madd(durations_m2, ref_words_qdat)
        temp_ghunnah_m2 = TajweedScorer.score_temporal_ghunnah(durations_m2, ref_words_qdat)
        
        m2_madd_det = (sim_m2 < MAULANA_GRADE) and (conf_m2 > CONF_THRESHOLD) or any(t['error'] for t in temp_madd_m2)
        m2_ghunnah_det = (sim_m2 < MAULANA_GRADE) and (conf_m2 > CONF_THRESHOLD) or any(t['error'] for t in temp_ghunnah_m2)
        m2_global_det = (m2_madd_det or m2_ghunnah_det)
        
        m2_times.append(time.time() - m2_start)
        
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
    mendeley_start_count = len(processed_qdat_ids)
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
            for model_res in [m1_results, m2_results]:
                if "q" in exp_str or "s" in exp_str:
                    model_res["Makharij (Articulation)"].append({"gt": is_error_gt, "det": True})
                else:
                    model_res["Vowel Drift"].append({"gt": is_error_gt, "det": True})
                model_res["Global Mendeley"].append({"gt": is_error_gt, "det": True})
            processed_mendeley_names.add(f_name)
            continue
            
        # =====================================================================
        # MODEL 1: WITH WHISPER
        # =====================================================================
        m1_start = time.time()
        whisper_res = we.transcribe(audio_array)
        trans_text = whisper_res.get("text", "").strip()
        
        if not trans_text:
            m1_det = True
            whisper_empty_count += 1
        else:
            phonetic_result = pe.transcribe_phonetics(audio_array)
            act_str = "".join(phonetic_result["words"]).lower()
            conf = phonetic_result["confidence"]
            
            sim = TajweedScorer.weighted_similarity(act_str, exp_str)
            m1_det = (sim < MAULANA_GRADE) and (conf > CONF_THRESHOLD)
            
        m1_times.append(time.time() - m1_start)
        
        has_swap = False if not trans_text else TajweedScorer._has_identity_swap(act_str, exp_str)
        is_makharij_category = (has_swap or "q" in exp_str or "s" in exp_str)
        
        if is_makharij_category:
            m1_results["Makharij (Articulation)"].append({"gt": is_error_gt, "det": m1_det})
        else:
            m1_results["Vowel Drift"].append({"gt": is_error_gt, "det": m1_det})
        m1_results["Global Mendeley"].append({"gt": is_error_gt, "det": m1_det})
        
        # =====================================================================
        # MODEL 2: WITHOUT WHISPER
        # =====================================================================
        m2_start = time.time()
        phonetic_result_m2 = pe.transcribe_phonetics(audio_array)
        act_str_m2 = "".join(phonetic_result_m2["words"]).lower()
        conf_m2 = phonetic_result_m2["confidence"]
        
        sim_m2 = TajweedScorer.weighted_similarity(act_str_m2, exp_str)
        m2_det = (sim_m2 < MAULANA_GRADE) and (conf_m2 > CONF_THRESHOLD)
        
        m2_times.append(time.time() - m2_start)
        
        has_swap_m2 = TajweedScorer._has_identity_swap(act_str_m2, exp_str)
        is_makharij_category_m2 = (has_swap_m2 or "q" in exp_str or "s" in exp_str)
        
        if is_makharij_category_m2:
            m2_results["Makharij (Articulation)"].append({"gt": is_error_gt, "det": m2_det})
        else:
            m2_results["Vowel Drift"].append({"gt": is_error_gt, "det": m2_det})
        m2_results["Global Mendeley"].append({"gt": is_error_gt, "det": m2_det})
        
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
            "whisper_empty_detections": whisper_empty_count,
            "m1_avg_time_ms": round(np.mean(m1_times) * 1000, 1),
            "m2_avg_time_ms": round(np.mean(m2_times) * 1000, 1),
            "speedup_ratio": round(np.mean(m1_times) / np.mean(m2_times), 1)
        },
        "model_1": {},
        "model_2": {}
    }
    
    for category in m1_results.keys():
        report["model_1"][category] = calculate_metrics(m1_results[category])
        report["model_2"][category] = calculate_metrics(m2_results[category])
        
    # Print results to stdout
    original_print("\n" + "="*100)
    original_print(f"{'TAJWEED ERROR PRECISION & PERFORMANCE MATRIX':^100}")
    original_print("="*100)
    original_print(f"{'CATEGORY':<25} | {'COUNT':<5} | {'MODEL 1 (ASR)':<30} | {'MODEL 2 (WHISPER-SKIP)':<30}")
    original_print(f"{'':<25} | {'':<5} | {'REC':<6} {'PREC':<6} {'F1':<6} {'(TP/FP/FN)':<9} | {'REC':<6} {'PREC':<6} {'F1':<6} {'(TP/FP/FN)':<9}")
    original_print("-"*100)
    
    for cat in m1_results.keys():
        m1 = report["model_1"][cat]
        m2 = report["model_2"][cat]
        
        m1_counts = f"{m1['TP']}/{m1['FP']}/{m1['FN']}"
        m2_counts = f"{m2['TP']}/{m2['FP']}/{m2['FN']}"
        
        original_print(f"{cat:<25} | {m1['Count']:<5} | "
                      f"{m1['Recall']:>5.1%} {m1['Precision']:>5.1%} {m1['F1']:>5.3f} {m1_counts:<9} | "
                      f"{m2['Recall']:>5.1%} {m2['Precision']:>5.1%} {m2['F1']:>5.3f} {m2_counts:<9}")
              
    original_print("="*100)
    original_print(f"Performance Stats:")
    original_print(f"  Model 1 Average Time per Audio: {report['summary']['m1_avg_time_ms']} ms")
    original_print(f"  Model 2 Average Time per Audio: {report['summary']['m2_avg_time_ms']} ms")
    original_print(f"  Speedup Ratio: {report['summary']['speedup_ratio']}x faster without Whisper!")
    original_print(f"  Whisper Empty Transcription False Detections: {whisper_empty_count} items")
    original_print("="*100)
    
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
