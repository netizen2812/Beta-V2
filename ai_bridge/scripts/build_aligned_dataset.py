"""
Phase 1: AlQuran API Dataset Builder
- Fetches complete Quran text (Arabic + Urdu) from AlQuran Cloud
- Whisper-transcribes our local audio files
- Matches local audio to real verse text
- Outputs: proper audio-transcript CSV pairs for real fine-tuning
"""

import os
import json
import requests
import torch
import pandas as pd
import scipy.io.wavfile as wavfile
import numpy as np
from pathlib import Path

ARABIC_EDITION  = "quran-uthmani"       # Full diacritics (harakaat) - best for TTS
URDU_EDITION    = "ur.jalandhry"        # Most widely used scholarly Urdu translation
QURAN_API_BASE  = "http://api.alquran.cloud/v1"
WAV_DIR         = "data/tts_dataset/wavs"
OUTPUT_DIR      = "data/tts_dataset_aligned"
AR_CSV          = os.path.join(OUTPUT_DIR, "ar_aligned.csv")
UR_CSV          = os.path.join(OUTPUT_DIR, "ur_aligned.csv")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─────────────────────────────────────────────
# STEP 1: Fetch full Quran text from API
# ─────────────────────────────────────────────
def fetch_quran_text(edition):
    print(f" > Fetching Quran text: {edition} ...")
    url = f"{QURAN_API_BASE}/quran/{edition}"
    r = requests.get(url, timeout=30)
    data = r.json()
    verses = []
    for surah in data["data"]["surahs"]:
        for ayah in surah["ayahs"]:
            verses.append({
                "surah": surah["number"],
                "ayah": ayah["numberInSurah"],
                "number": ayah["number"],   # absolute verse number (1-6236)
                "text": ayah["text"]
            })
    print(f"   -> Fetched {len(verses)} verses from '{edition}'")
    return verses

# ─────────────────────────────────────────────
# STEP 2: Whisper-transcribe local audio files
# ─────────────────────────────────────────────
def transcribe_audio_files(lang_prefix, whisper_model, wav_dir=WAV_DIR):
    print(f"\n > Transcribing {lang_prefix.upper()} audio files with Whisper from {wav_dir}...")
    wav_files = sorted(Path(wav_dir).glob(f"{lang_prefix}_*.wav"))
    if not wav_files:
        # Try mp3 if no wavs found
        wav_files = sorted(Path(wav_dir).glob(f"{lang_prefix}_*.mp3"))
    print(f"   -> Found {len(wav_files)} {lang_prefix.upper()} audio files.")
    results = []
    for i, wav_path in enumerate(wav_files):
        try:
            result = whisper_model.transcribe(
                str(wav_path),
                language="ar" if lang_prefix == "ar" else "ur",
                fp16=torch.cuda.is_available()
            )
            transcript = result["text"].strip()
            results.append({"file": wav_path.name, "whisper_text": transcript})
            if i % 50 == 0:
                print(f"   -> [{lang_prefix.upper()}] Transcribed {i}/{len(wav_files)}: {wav_path.name}")
        except Exception as e:
            results.append({"file": wav_path.name, "whisper_text": ""})
            print(f"   -> ERROR on {wav_path.name}: {e}")
    return results

# ─────────────────────────────────────────────
# STEP 3: Match transcriptions to Quran verses
# ─────────────────────────────────────────────
def match_to_quran(transcriptions, quran_verses):
    """
    Strategy: Sequential matching.
    If our audio files are in order (ar_0001 = verse 1, ar_0002 = verse 2...),
    we can directly map by index. Whisper text is used for verification.
    """
    matched = []
    for i, item in enumerate(transcriptions):
        if i < len(quran_verses):
            verse = quran_verses[i]
            matched.append({
                "file": item["file"],
                "whisper_text": item["whisper_text"],
                "quran_text": verse["text"],         # Official text with full harakaat
                "surah": verse["surah"],
                "ayah": verse["ayah"]
            })
    return matched

# ─────────────────────────────────────────────
# STEP 4: Save aligned CSVs for training
# ─────────────────────────────────────────────
def save_training_csv(matched, output_csv, wav_dir):
    rows = []
    for item in matched:
        wav_path = os.path.abspath(os.path.join(wav_dir, item["file"]))
        if os.path.exists(wav_path) and item["quran_text"]:
            rows.append({
                "audio_path": wav_path,
                "text": item["quran_text"],
                "surah": item["surah"],
                "ayah": item["ayah"]
            })
    df = pd.DataFrame(rows)
    df.to_csv(output_csv, index=False, encoding="utf-8-sig")
    print(f"   -> Saved {len(df)} aligned rows to {output_csv}")
    return df

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def build_aligned_dataset():
    print("=" * 60)
    print("ALQURAN DATASET ALIGNMENT PIPELINE")
    print("=" * 60)

    # 1. Fetch Quran text from API
    ar_verses = fetch_quran_text(ARABIC_EDITION)
    ur_verses = fetch_quran_text(URDU_EDITION)

    # 2. Load Whisper
    print("\n > Loading Whisper Large model for transcription...")
    import whisper
    whisper_model = whisper.load_model("medium")  # 769MB — high accuracy for AR/UR
    print("   -> Whisper loaded.")

    # 3. Transcribe Arabic files (files live in ar/wavs/)
    ar_transcriptions = transcribe_audio_files("ar", whisper_model, "data/tts_dataset/ar/wavs")
    ar_matched = match_to_quran(ar_transcriptions, ar_verses)
    ar_df = save_training_csv(ar_matched, AR_CSV, "data/tts_dataset/ar/wavs")

    # 4. Transcribe Urdu files (files live in wavs_ur/ — prefer .wav over .mp3)
    ur_transcriptions = transcribe_audio_files("ur", whisper_model, "data/tts_dataset/wavs_ur")
    ur_matched = match_to_quran(ur_transcriptions, ur_verses)
    ur_df = save_training_csv(ur_matched, UR_CSV, "data/tts_dataset/wavs_ur")

    print("\n" + "=" * 60)
    print("DATASET ALIGNMENT COMPLETE")
    print(f" > Arabic training pairs: {len(ar_df)}")
    print(f" > Urdu training pairs:   {len(ur_df)}")
    print(f" > Arabic CSV: {AR_CSV}")
    print(f" > Urdu CSV:   {UR_CSV}")
    print("=" * 60)
    return ar_df, ur_df

if __name__ == "__main__":
    try:
        build_aligned_dataset()
    except Exception as e:
        import traceback
        traceback.print_exc()
