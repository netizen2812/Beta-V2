"""
repackage_dataset.py
============================================================
Fixes the critical over-length clip problem in EN/AR GCP zips.

ROOT CAUSE: The alQuran.cloud audio API returns full-surah MP3s
for some ayah numbers (esp. long surahs). XTTS silently discards
any clip > 11.6s (max_wav_length=255995 @ 22050Hz). This left
EN with only 367 usable clips and AR with only 94 usable clips.

STRATEGY:
  1. Load every WAV from the zip.
  2. If duration <= MAX_DUR_S  -> keep as-is.
  3. If duration > MAX_DUR_S  -> split at silence boundaries
     using energy-based VAD (no extra library needed).
     Each resulting segment that is within [MIN_DUR_S, MAX_DUR_S]
     is kept; the rest are discarded.
  4. The parent ayah's text is assigned to every child segment
     (XTTS needs audio+text pairs; sub-ayah text splitting is
     not possible without forced-alignment tooling).
  5. Write clean zip: metadata.csv (LJSpeech 3-col) + wavs/*.wav

Usage:
    python repackage_dataset.py --zip en_gcp_forge.zip --lang en
    python repackage_dataset.py --zip ar_gcp_forge.zip --lang ar

Output:
    en_gcp_forge_v2.zip  /  ar_gcp_forge_v2.zip
============================================================
"""

import argparse
import csv
import io
import os
import shutil
import tempfile
import zipfile
from pathlib import Path

import numpy as np
import torch
import torchaudio
import torchaudio.transforms as T

# ── Config ─────────────────────────────────────────────────────────────────────
MIN_DUR_S  = 1.5    # discard segments shorter than this (likely silence/noise)
MAX_DUR_S  = 10.5   # XTTS max_wav_length is 11.6s; leave 1s headroom
TARGET_SR  = 22050  # XTTS native sample rate — resample everything to this
SILENCE_DB = -40.0  # energy threshold for silence detection (dBFS)
MIN_SILENCE_S = 0.3 # minimum silence gap to split on (seconds)

# ── Helpers ─────────────────────────────────────────────────────────────────────

def load_wav_from_bytes(data: bytes, target_sr: int) -> torch.Tensor:
    """Load WAV from bytes, convert to mono, resample to target_sr."""
    buf = io.BytesIO(data)
    wav, sr = torchaudio.load(buf)
    if wav.shape[0] > 1:
        wav = wav.mean(dim=0, keepdim=True)   # stereo -> mono
    if sr != target_sr:
        wav = T.Resample(sr, target_sr)(wav)
    return wav.squeeze(0)   # [T]


def find_silence_boundaries(wav: torch.Tensor, sr: int) -> list[tuple[int, int]]:
    """
    Return list of (start, end) sample indices of non-silent speech regions.
    Uses a simple frame-energy VAD — no extra dependencies needed.
    """
    frame_len  = int(sr * 0.02)   # 20ms frames
    hop_len    = frame_len // 2
    min_sil_frames = int(MIN_SILENCE_S * sr / hop_len)

    wav_np = wav.numpy()
    frames = []
    for i in range(0, len(wav_np) - frame_len, hop_len):
        frame = wav_np[i : i + frame_len]
        rms_db = 20 * np.log10(np.sqrt(np.mean(frame ** 2)) + 1e-9)
        frames.append(rms_db > SILENCE_DB)   # True = speech

    # Find speech regions (merge gaps < min_sil_frames)
    regions = []
    in_speech, start = False, 0
    silence_count = 0

    for fi, is_speech in enumerate(frames):
        if is_speech:
            if not in_speech:
                start = fi
                in_speech = True
            silence_count = 0
        else:
            if in_speech:
                silence_count += 1
                if silence_count >= min_sil_frames:
                    end = (fi - silence_count + 1) * hop_len
                    regions.append((start * hop_len, min(end, len(wav_np))))
                    in_speech = False
                    silence_count = 0
    if in_speech:
        regions.append((start * hop_len, len(wav_np)))

    return regions if regions else [(0, len(wav_np))]


def split_into_chunks(wav: torch.Tensor, sr: int) -> list[torch.Tensor]:
    """
    Split a waveform into chunks of MAX_DUR_S or less, cutting at silence.
    Returns list of chunk tensors (each within [MIN_DUR_S, MAX_DUR_S]).
    """
    total_dur = len(wav) / sr
    if total_dur <= MAX_DUR_S:
        return [wav] if total_dur >= MIN_DUR_S else []

    # Get speech regions, then greedily pack into MAX_DUR_S buckets
    regions = find_silence_boundaries(wav, sr)
    max_samples = int(MAX_DUR_S * sr)
    min_samples = int(MIN_DUR_S * sr)

    chunks = []
    current_start = None
    current_end   = None

    for (r_start, r_end) in regions:
        region_len = r_end - r_start

        if region_len > max_samples:
            # Region itself is too long — hard-slice it
            for slice_start in range(r_start, r_end, max_samples):
                chunk = wav[slice_start : slice_start + max_samples]
                if len(chunk) >= min_samples:
                    chunks.append(chunk)
            current_start = current_end = None
            continue

        if current_start is None:
            current_start = r_start
            current_end   = r_end
        elif (r_end - current_start) <= max_samples:
            # This region fits in the current bucket
            current_end = r_end
        else:
            # Flush current bucket and start a new one
            segment = wav[current_start:current_end]
            if len(segment) >= min_samples:
                chunks.append(segment)
            current_start = r_start
            current_end   = r_end

    if current_start is not None:
        segment = wav[current_start:current_end]
        if len(segment) >= min_samples:
            chunks.append(segment)

    return chunks


def save_wav(wav: torch.Tensor, path: Path, sr: int):
    try:
        # Prevent any Libsndfile system errors by converting NaN/Inf
        cleaned_wav = torch.nan_to_num(wav, nan=0.0, posinf=1.0, neginf=-1.0)
        torchaudio.save(str(path), cleaned_wav.unsqueeze(0), sr)
    except Exception as e:
        print(f"\n[ERROR] torchaudio.save failed on path: {path}")
        print(f"        wav shape: {wav.shape}, sr: {sr}")
        print(f"        error type: {type(e)}, message: {e}")
        raise e


# ── Main ────────────────────────────────────────────────────────────────────────

def repackage(zip_path: str, lang: str):
    zip_path = Path(zip_path)
    out_zip  = zip_path.with_name(zip_path.stem + "_v2.zip")

    print(f"\n{'='*60}")
    print(f"  REPACKAGING: {zip_path.name}  [{lang.upper()}]")
    print(f"  Output:      {out_zip.name}")
    print(f"{'='*60}\n")

    tmpdir = r"c:\Users\acer\Downloads\AI\temp_repackage"
    if os.path.exists(tmpdir):
        try:
            shutil.rmtree(tmpdir)
        except Exception:
            pass
    os.makedirs(tmpdir, exist_ok=True)
    
    try:
        tmp = Path(tmpdir)
        wav_out_dir = tmp / "wavs"
        wav_out_dir.mkdir(exist_ok=True)

        # ── Read source zip ───────────────────────────────────────────────────
        with zipfile.ZipFile(zip_path, "r") as zf:
            all_names = zf.namelist()

            # Load metadata
            meta_name = next((n for n in all_names if n == "metadata.csv"), None)
            if not meta_name:
                meta_name = next((n for n in all_names if n.endswith("metadata.csv")), None)
            assert meta_name, "metadata.csv not found in zip"

            with zf.open(meta_name) as mf:
                raw = mf.read().decode("utf-8", errors="replace")
            id_to_text = {}
            for row in csv.reader(raw.splitlines(), delimiter="|"):
                if row and len(row) >= 2:
                    id_to_text[row[0].strip()] = row[1].strip()

            # Process each WAV
            wav_names = sorted(n for n in all_names if n.startswith("wavs/") and n.endswith(".wav"))
            print(f"> Processing {len(wav_names)} source WAVs...")

            total_in, total_out, total_dropped = 0, 0, 0
            new_rows = []

            for i, wav_name in enumerate(wav_names):
                stem = Path(wav_name).stem
                text = id_to_text.get(stem, "")
                if not text:
                    total_dropped += 1
                    continue

                # Load
                raw_bytes = zf.read(wav_name)
                try:
                    wav = load_wav_from_bytes(raw_bytes, TARGET_SR)
                except Exception as e:
                    print(f"  [SKIP] Load error on {stem}: {e}")
                    total_dropped += 1
                    continue

                total_in += 1
                dur = len(wav) / TARGET_SR

                # Split if needed
                chunks = split_into_chunks(wav, TARGET_SR)
                if not chunks:
                    total_dropped += 1
                    continue

                try:
                    for ci, chunk in enumerate(chunks):
                        chunk_id   = f"{stem}" if len(chunks) == 1 else f"{stem}_s{ci+1:02d}"
                        chunk_path = wav_out_dir / f"{chunk_id}.wav"
                        save_wav(chunk, chunk_path, TARGET_SR)
                        new_rows.append([chunk_id, text, text])   # LJSpeech: id|text|norm_text
                        total_out += 1
                except Exception as e:
                    print(f"\n  [WARN] Failed to write segments for {stem} due to save error: {e}")
                    total_dropped += 1
                    continue

                if (i + 1) % 100 == 0:
                    print(f"  [{i+1}/{len(wav_names)}] produced {total_out} segments so far...")

        # ── Write output zip ──────────────────────────────────────────────────
        meta_out = tmp / "metadata.csv"
        with open(meta_out, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter="|")
            writer.writerows(new_rows)

        print(f"\n> Building output zip: {out_zip}...")
        with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf_out:
            zf_out.write(meta_out, "metadata.csv")
            for wav_file in sorted(wav_out_dir.iterdir()):
                zf_out.write(wav_file, f"wavs/{wav_file.name}")

        print(f"\n{'='*60}")
        print(f"  SOURCE :  {len(wav_names)} WAVs, {len(id_to_text)} text entries")
        print(f"  OUTPUT :  {total_out} segments (from {total_in} valid source clips)")
        print(f"  DROPPED:  {total_dropped} (missing text or load error)")
        print(f"  FILE   :  {out_zip}")
        print(f"  SIZE   :  {out_zip.stat().st_size / 1024 / 1024:.1f} MB")
        print(f"{'='*60}\n")

    finally:
        if os.path.exists(tmpdir):
            try:
                shutil.rmtree(tmpdir)
            except Exception:
                pass

    # Quick self-validation
    print("> Running self-validation on output zip...")
    ok = True
    dur_violations = 0
    with zipfile.ZipFile(out_zip, "r") as zf:
        for wav_name in [n for n in zf.namelist() if n.startswith("wavs/")]:
            raw = zf.read(wav_name)
            wav, sr = torchaudio.load(io.BytesIO(raw))
            dur = wav.shape[-1] / sr
            if dur > MAX_DUR_S + 0.5:   # 0.5s tolerance for rounding
                dur_violations += 1
    if dur_violations:
        print(f"  [WARN] {dur_violations} segments still exceed {MAX_DUR_S}s limit.")
        ok = False
    else:
        print(f"  [OK] All output segments are within XTTS duration limit.")
    return ok


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip",  required=True, help="Source zip path")
    parser.add_argument("--lang", required=True, choices=["en", "ar"])
    args = parser.parse_args()
    repackage(args.zip, args.lang)
