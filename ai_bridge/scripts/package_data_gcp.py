"""
package_data_gcp.py
============================================================
Packages the local TTS dataset into LJSpeech-format zips
ready for GCP Vertex AI training jobs.

FIXES applied (v2):
  - Duration filter: clips > MAX_DUR_S are SKIPPED (XTTS
    silently drops them at 11.6s — better to catch it here)
  - Enforces 3-column LJSpeech format: id|text|normalized_text
  - Reports exact count of kept vs skipped clips so you know
    what the training job will actually see
  - Always run validate_gcp_dataset.py after this script
============================================================
"""

import csv
import os
import shutil
import pandas as pd
import torchaudio
from pathlib import Path

DATASET_PATH    = r"c:\Users\acer\Downloads\AI\ai_bridge\data\tts_dataset"
UNIFIED_METADATA = os.path.join(DATASET_PATH, "metadata_unified.csv")

TARGET_SR   = 22050     # XTTS native sample rate
MAX_DUR_S   = 10.5      # XTTS max_wav_length = 11.6s; 1s safety margin
MIN_DUR_S   = 1.5       # Discard very short clips (noise / silence)


def get_wav_duration(wav_path: str) -> float | None:
    """Return duration in seconds, or None if the file can't be loaded."""
    try:
        info = torchaudio.info(wav_path)
        return info.num_frames / info.sample_rate
    except Exception:
        return None


import re

def clean_arabic(text: str) -> str:
    # Remove BOM if present
    text = text.replace("\ufeff", "")
    
    # 1. Normalize Alef Wasla 'ٱ' to standard Alef 'ا'
    text = text.replace("ٱ", "ا")
    
    # 2. Normalize superscript Alef (alef khanjariya) 'ٰ' to standard Alef 'ا'
    text = text.replace("\u0670", "ا")
    
    # 3. Strip all diacritics (harakat):
    # Fathah, Dammah, Kasrah, Fathatan, Dammatan, Kasratan, Shaddah, Sukun
    diacritics_pattern = re.compile(r"[\u064B-\u0652]")
    text = diacritics_pattern.sub("", text)
    
    # 4. Strip all Quranic annotation marks / pause marks (range U+06D6 to U+06ED)
    quranic_pattern = re.compile(r"[\u06D6-\u06ED]")
    text = quranic_pattern.sub("", text)
    
    # 5. Remove any other non-standard characters (keep standard Arabic alphabet and spaces)
    # Standard Arabic characters range: U+0621 to U+064A
    cleaned_chars = []
    for c in text:
        if '\u0621' <= c <= '\u064A' or c.isspace():
            cleaned_chars.append(c)
    text = "".join(cleaned_chars)
    
    # 6. Normalize multiple spaces
    text = re.sub(r"\s+", " ", text).strip()
    return text

def prepare_lang_data(lang_prefix: str):
    print(f"\n{'='*60}")
    print(f"  PACKAGING: {lang_prefix.upper()}")
    print(f"{'='*60}")

    # ── Load unified metadata ──────────────────────────────────────────────────
    df = pd.read_csv(UNIFIED_METADATA, sep="|", header=None, names=["id", "text", "extra"])
    df_lang = df[df["id"].str.startswith(f"{lang_prefix}_")].copy()
    print(f"> Found {len(df_lang)} metadata rows for [{lang_prefix.upper()}]")

    # ── Resolve WAV source directory ───────────────────────────────────────────
    if lang_prefix in ("en", "ar"):
        wav_src = os.path.join(DATASET_PATH, lang_prefix, "wavs")
    else:
        wav_src = os.path.join(DATASET_PATH, f"wavs_{lang_prefix}")

    # ── Duration filter ────────────────────────────────────────────────────────
    kept, skipped_long, skipped_short, skipped_missing = [], [], [], []

    for _, row in df_lang.iterrows():
        file_id  = row["id"].strip()
        text     = str(row["text"]).strip()
        wav_path = os.path.join(wav_src, f"{file_id}.wav")

        if not os.path.exists(wav_path):
            skipped_missing.append(file_id)
            continue

        dur = get_wav_duration(wav_path)
        if dur is None:
            skipped_missing.append(file_id)
            continue

        if dur > MAX_DUR_S:
            skipped_long.append((file_id, round(dur, 1)))
        elif dur < MIN_DUR_S:
            skipped_short.append((file_id, round(dur, 1)))
        else:
            if lang_prefix == "ar":
                text = clean_arabic(text)
            kept.append({"id": file_id, "text": text, "wav": wav_path})

    print(f"\n  Duration audit:")
    print(f"    Kept          : {len(kept)} clips ({MIN_DUR_S:.1f}s – {MAX_DUR_S:.1f}s)")
    print(f"    Skipped long  : {len(skipped_long)} clips (> {MAX_DUR_S}s) — XTTS would drop these")
    print(f"    Skipped short : {len(skipped_short)} clips (< {MIN_DUR_S}s) — likely silence/noise")
    print(f"    Missing WAV   : {len(skipped_missing)} entries")

    if len(kept) < 50:
        print(f"\n  [ERROR] Only {len(kept)} usable clips. Too few for fine-tuning.")
        print(f"          Run repackage_dataset.py first to segment long clips, then re-run.")
        return

    # ── Write LJSpeech metadata (3-column) ────────────────────────────────────
    output_meta = os.path.join(DATASET_PATH, f"metadata_{lang_prefix}.csv")
    with open(output_meta, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="|")
        for item in kept:
            # LJSpeech: id | raw_text | normalized_text
            writer.writerow([item["id"], item["text"], item["text"]])
    print(f"\n  Metadata written: {output_meta}  ({len(kept)} rows)")

    # ── Build zip ─────────────────────────────────────────────────────────────
    temp_dir = os.path.join(r"c:\Users\acer\Downloads\AI", f"temp_package_{lang_prefix}")
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(os.path.join(temp_dir, "wavs"), exist_ok=True)

    shutil.copy(output_meta, os.path.join(temp_dir, "metadata.csv"))

    print(f"  Copying {len(kept)} WAV files...")
    for item in kept:
        shutil.copy(item["wav"], os.path.join(temp_dir, "wavs", f"{item['id']}.wav"))

    zip_name = os.path.join(r"c:\Users\acer\Downloads\AI", f"{lang_prefix}_gcp_forge")
    shutil.make_archive(zip_name, "zip", temp_dir)
    shutil.rmtree(temp_dir)

    zip_size = os.path.getsize(zip_name + ".zip") / 1024 / 1024
    print(f"\n  [DONE] {zip_name}.zip  ({zip_size:.1f} MB)")
    print(f"  Next step: python scripts/validate_gcp_dataset.py --zip {lang_prefix}_gcp_forge.zip --lang {lang_prefix}")


if __name__ == "__main__":
    # prepare_lang_data("en")
    prepare_lang_data("ar")
