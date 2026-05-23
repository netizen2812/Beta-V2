"""
Pre-download script for HuggingFace models and Buraaq dataset.

Run once before first launch to avoid startup delays:
    python scripts/download_models.py

Downloads:
  1. tarteel-ai/whisper-base-ar-quran (~290MB)
  2. TBOGamer22/wav2vec2-quran-phonetics (~360MB)
  3. Buraaq/quran-md-words dataset (~2GB)
"""

import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def download_whisper():
    print("📥 Downloading Whisper model: tarteel-ai/whisper-base-ar-quran ...")
    from transformers import AutoProcessor, AutoModelForSpeechSeq2Seq
    AutoProcessor.from_pretrained("tarteel-ai/whisper-base-ar-quran")
    AutoModelForSpeechSeq2Seq.from_pretrained("tarteel-ai/whisper-base-ar-quran")
    print("✅ Whisper model downloaded and cached.")


def download_wav2vec2():
    print("📥 Downloading Wav2Vec2 model: TBOGamer22/wav2vec2-quran-phonetics ...")
    from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC
    Wav2Vec2Processor.from_pretrained("TBOGamer22/wav2vec2-quran-phonetics")
    Wav2Vec2ForCTC.from_pretrained("TBOGamer22/wav2vec2-quran-phonetics")
    print("✅ Wav2Vec2 phonetic model downloaded and cached.")


def download_buraaq_dataset():
    print("📥 Downloading Buraaq/quran-md-words dataset (~2GB) ...")
    from services.phonetic_db import PhoneticDB
    db = PhoneticDB()
    db.load()
    print(f"✅ Buraaq dataset cached: {db.total_words} words, {db.total_ayahs} ayahs.")


if __name__ == "__main__":
    print("=" * 60)
    print("  Faith-Tech AI Bridge — Model Download Script")
    print("=" * 60)
    print()

    download_whisper()
    print()

    download_wav2vec2()
    print()

    download_buraaq_dataset()
    print()

    print("=" * 60)
    print("  ✅ All models and data downloaded successfully!")
    print("  You can now start the AI Bridge: uvicorn main:app --port 8000")
    print("=" * 60)
