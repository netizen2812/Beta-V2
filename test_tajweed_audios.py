import sys
import os
import torch
import logging
from pathlib import Path

# Add ai_bridge to sys.path
sys.path.append(str(Path("ai_bridge").absolute()))
sys.stdout.reconfigure(encoding='utf-8')

from ai_bridge.models.whisper_engine import WhisperEngine
from ai_bridge.models.phonetic_engine import PhoneticEngine
from ai_bridge.services.phonetic_db import PhoneticDB
from ai_bridge.services.tajweed_scorer import TajweedScorer
from ai_bridge.services.alignment import AlignmentEngine
from ai_bridge.services.temporal_engine import TemporalEngine
from ai_bridge.services.spectral_analyzer import SpectralAnalyzer, QALQALAH_LETTERS_TR, QALQALAH_LETTERS_AR

# Suppress logging for cleaner output
logging.basicConfig(level=logging.ERROR)

def test_audios():
    # 1. Initialize Engines
    print("Initializing Engines (this may take a minute)...")
    whisper = WhisperEngine()
    whisper.load()
    
    phonetic_engine = PhoneticEngine()
    phonetic_engine.load()
    
    phonetic_db = PhoneticDB()
    phonetic_db.load()
    
    temporal_engine = TemporalEngine()
    spectral_analyzer = SpectralAnalyzer()
    
    audio_folder = Path("testing dataset")
    audio_files = sorted(list(audio_folder.glob("*.mp3")))
    print(f"Found {len(audio_files)} audio files in '{audio_folder}'")

    # Combine all ayahs of Surah Naas (114:1 - 114:6)
    reference_words = []
    for i in range(1, 7):
        ayah_words = phonetic_db.search_by_ayah_id(f"114:{i}")
        if ayah_words:
            reference_words.extend(ayah_words)
    
    if not reference_words:
        print("No reference found for Surah Naas")
        return

    results = []

    for audio_path in audio_files:
        print(f"\nProcessing: {audio_path.name}")
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()
            
        # Step 1: Whisper ASR
        whisper_result = whisper.transcribe(audio_bytes)
        transcribed_text = whisper_result["text"]
        
        # Step 2: Phonetic Analysis
        logits, audio_length = phonetic_engine.get_ctc_logits(audio_bytes)
        phonetic_result = phonetic_engine.decode_logits(logits)
        actual_phonetics = phonetic_result["words"]
        
        # Step 3: Alignment
        aligned_words = AlignmentEngine.align_words(
            logits, audio_length, phonetic_engine.processor
        )
        
        # Step 4: Precision Feedback
        precision_feedback = []
        
        # Temporal (Disabled for full surah batch)
        # user_word_timings = [
        #     {"word_index": i, "duration": w["end_time"] - w["start_time"]} 
        #     for i, w in enumerate(aligned_words)
        # ]
        # precision_feedback.extend(temporal_engine.validate_durations("114:1", user_word_timings))
        
        # Spectral (Qalqalah)
        # We need a temp wav file for spectral analyzer
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            temp_audio_path = tmp.name
            
        segment_times = []
        for i, word in enumerate(reference_words):
            if i >= len(aligned_words): continue
            is_qal = any(l in word["word_tr"].lower() for l in QALQALAH_LETTERS_TR) or \
                     any(l in word["word_ar"] for l in QALQALAH_LETTERS_AR)
            segment_times.append({
                "word_index": i,
                "start": aligned_words[i]["start_time"],
                "end": aligned_words[i]["end_time"],
                "is_qalqalah": is_qal
            })
            
        spectral_feedback = spectral_analyzer.detect_qalqalah(temp_audio_path, segment_times)
        precision_feedback.extend(spectral_feedback)
        
        os.remove(temp_audio_path)
        
        # Step 5: Final Scoring (Word-Level Pinpointing)
        def segment_phonetics(act_str, ref_list):
            segments = []
            cursor = 0
            for ref_word in ref_list:
                # Approximate length of the word in phonetics
                target_len = len(ref_word["word_tr"].lower().replace("-", "").replace("'", ""))
                chunk = act_str[cursor:cursor+target_len]
                segments.append(chunk if chunk else "")
                cursor += target_len
            return segments

        actual_phonetic_string = "".join(actual_phonetics).replace("|", "").replace(" ", "").lower()
        word_level_act = segment_phonetics(actual_phonetic_string, reference_words)
        
        report = TajweedScorer.score_recitation(
            actual_phonetics=word_level_act, 
            reference_words=reference_words,
            temporal_feedback=[] 
        )
        
        # Pinpoint mistakes
        print(f"  Mistake Pinpointing:")
        found_mistakes = False
        for m in report["word_results"]:
            if m["status"] != "correct":
                act = m['actual_phonetic'] if m['actual_phonetic'] else "[Nothing]"
                print(f"    - Word '{m['word_ar']}': Expected '{m['expected_phonetic']}', Got '{act}' ({m['rule']})")
                found_mistakes = True
        
        if not found_mistakes:
            print("    - No specific errors detected.")
        
        results.append({
            "file": audio_path.name,
            "text": transcribed_text,
            "feedback": report["maulana_feedback"],
            "word_results": report["word_results"]
        })
        
        # Print Summary for this file
        fb = report["maulana_feedback"]
        print(f"  Overall Score: {fb['score']}% - {fb['status']}")
        
    return results

if __name__ == "__main__":
    test_audios()
