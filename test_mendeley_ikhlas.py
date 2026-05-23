import os
import sys
import io
from pathlib import Path

# Add project root to sys.path
sys.path.append(os.getcwd())
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from ai_bridge.models.whisper_engine import WhisperEngine
from ai_bridge.models.phonetic_engine import PhoneticEngine
from ai_bridge.services.phonetic_db import PhoneticDB

def test_mendeley():
    print("--- TESTING ON MENDELEY IKHLAS DATASET ---")
    
    DATA_DIR = Path("ai_bridge/data/test_datasets/mendeley_ikhlas/Surah Al-Ikhlas of the Holy Quran Error Detection Dataset/extracted/Dataset and Sounds/Sound recordings")
    
    # Official References (Buraaq/Quran-MD format)
    REFERENCES = {
        "V1": "qul huwa llāhu aḥadun",
        "V2": "allāhu ṣ-ṣamadu",
        "V3": "lam yalid wa-lam yūlad",
        "V4": "wa-lam yakun lahū kufuwan aḥadun"
    }

    # Samples to test
    samples = [
        {"file": "ID105V1T.wav", "verse": "V1", "label": "Correct"},
        {"file": "ID105V2T.wav", "verse": "V2", "label": "Correct"},
        {"file": "ID100V1F.wav", "verse": "V1", "label": "Error"},
        {"file": "ID101V2F.wav", "verse": "V2", "label": "Error"},
        {"file": "ID1V1F.wav",   "verse": "V1", "label": "Error"}
    ]

    # Load Engines
    whisper_engine = WhisperEngine()
    whisper_engine.load()
    phonetic_engine = PhoneticEngine()
    phonetic_engine.load()

    print(f"\n{'FILE':<15} | {'LABEL':<8} | {'VERSE':<5} | {'MODEL PHONETICS'}")
    print("-" * 80)

    for s in samples:
        path = DATA_DIR / s["file"]
        if not path.exists():
            print(f"File not found: {s['file']}")
            continue
            
        with open(path, "rb") as f:
            audio_bytes = f.read()
            
        # Get Model Phonetics
        phonetic_result = phonetic_engine.transcribe_phonetics(audio_bytes)
        model_phonetics = phonetic_result["phonetics"]
        
        # Get Whisper ASR
        transcription = whisper_engine.transcribe(audio_bytes)
        asr_text = transcription["text"]
        
        print(f"{s['file']:<15} | {s['label']:<8} | {s['verse']:<5} | {model_phonetics}")
        print(f"{' ':<15} | {'ASR':<8} | {' ':<5} | {asr_text}")
        print(f"{' ':<15} | {'REF':<8} | {' ':<5} | {REFERENCES[s['verse']]}")
        print("-" * 80)

if __name__ == "__main__":
    try:
        test_mendeley()
    except Exception as e:
        print(f"ERROR: {e}")
