import sys
import io
import os
from pathlib import Path

# Add the project root to sys.path for imports
sys.path.append(os.getcwd())
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from ai_bridge.models.whisper_engine import WhisperEngine
from ai_bridge.models.phonetic_engine import PhoneticEngine
from ai_bridge.models.whisper_engine import WhisperEngine
from ai_bridge.models.phonetic_engine import PhoneticEngine
from ai_bridge.services.phonetic_db import PhoneticDB
from ai_bridge.services.tajweed_scorer import TajweedScorer

def test_labeled_error():
    print("--- VERIFYING LABELED ERROR DETECTION ---")
    
    # Setup
    audio_path = Path("ai_bridge/data/test_datasets/ikhlas/ikhlas_v1_err1.wav")
    if not audio_path.exists():
        print(f"Error: {audio_path} not found.")
        return

    print(f"Testing File: {audio_path.name}")
    print("Known Error: Qalqalah error on Dal (Verse 1: qul huwa llāhu aḥad)")

    # 1. Load Engines
    whisper_engine = WhisperEngine()
    whisper_engine.load()
    phonetic_engine = PhoneticEngine()
    phonetic_engine.load()
    phonetic_db = PhoneticDB()
    phonetic_db.load()
    
    # 2. Transcription & Phonetics
    print(" > Transcribing...")
    with open(audio_path, "rb") as f:
        audio_bytes = f.read()
    transcription = whisper_engine.transcribe(audio_bytes)
    print(f"   Transcription: {transcription['text']}")
    
    print(" > Phonetic Extraction...")
    phonetic_result = phonetic_engine.transcribe_phonetics(audio_bytes)
    actual_phonetics = phonetic_result["words"]
    print(f"   Actual Phonetics: {actual_phonetics}")

    # 3. Get Reference
    print(" > Fetching Reference (112:1)...")
    reference_words = phonetic_db.get_ayah_phonetics(112, 1)
    
    # 4. Scoring
    print(" > Scoring...")
    report = TajweedScorer.score_recitation(
        actual_phonetics=actual_phonetics,
        reference_words=reference_words
    )

    # 5. Result Analysis
    fb = report["maulana_feedback"]
    print(f"\n--- MAULANA REPORT ---")
    print(f"Result: {fb['status']} (Score: {fb['score']}%)")
    print(f"Summary: {fb['summary']}")
    
    # Check for the Dal error in the last word (aḥad)
    last_word = report["word_results"][-1] if report["word_results"] else None
    if last_word:
        print(f"\nTarget Word Analysis (aḥad):")
        print(f"  Expected: {last_word['expected_phonetic']}")
        print(f"  Actual:   {last_word['actual_phonetic']}")
        print(f"  Status:   {last_word['status']}")
        print(f"  Rule:     {last_word['rule']}")
        print(f"  Guidance: {last_word['guidance']}")

if __name__ == "__main__":
    try:
        test_labeled_error()
    except Exception as e:
        print(f"ERROR: {e}")
