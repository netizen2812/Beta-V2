"""
validate_gcp_dataset.py
============================================================
Pre-flight validator for GCP training data zips.

Run this BEFORE launching any vertex_forge_*.yaml job to confirm that
load_tts_samples() will actually find your samples AND that clips are
within XTTS duration limits.

Usage:
    python validate_gcp_dataset.py --zip en_gcp_forge_v2.zip --lang en
    python validate_gcp_dataset.py --zip ar_gcp_forge_v2.zip --lang ar

Checks:
    1. Zip structure  -- metadata.csv at root, wavs/ adjacent
    2. Metadata format -- LJSpeech pipe-sep: id|text|normalized_text
    3. WAV coverage   -- every id has a matching wavs/<id>.wav
    4. Duration audit -- ALL WAVs checked (not just a sample)
                         Fails if >10% exceed XTTS 11.6s limit
============================================================
"""

import argparse
import csv
import os
import zipfile
from pathlib import Path

import torchaudio

MAX_DUR_S = 10.5   # XTTS max_wav_length=11.6s; 1s safety margin
MIN_DUR_S = 1.5    # Discard very short clips


def validate_zip(zip_path: str, lang: str) -> bool:
    zip_path = Path(zip_path)
    if not zip_path.exists():
        print(f"[ERROR] Zip not found: {zip_path}")
        return False

    print(f"\n{'='*60}")
    print(f"  VALIDATING: {zip_path.name}  [lang={lang.upper()}]")
    print(f"{'='*60}")

    ok = True

    with zipfile.ZipFile(zip_path, "r") as zf:
        all_names = zf.namelist()

        # -- Check 1: metadata.csv at root ------------------------------------
        meta_candidates = [n for n in all_names if n.endswith("metadata.csv")]
        root_meta = [n for n in meta_candidates if "/" not in n or n.count("/") == 0]

        if not root_meta:
            print(f"\n[FAIL] metadata.csv not found at zip root.")
            print(f"       Candidates found: {meta_candidates or 'NONE'}")
            print(f"       FIX: zip must contain metadata.csv at root + wavs/ subdir.")
            ok = False
            ids = set()
        else:
            meta_name = root_meta[0]
            print(f"\n[OK]   metadata.csv found at: {meta_name}")

            with zf.open(meta_name) as mf:
                raw = mf.read().decode("utf-8", errors="replace")
            rows = [r for r in csv.reader(raw.splitlines(), delimiter="|") if r]

            # -- Check 2: LJSpeech format (3 columns) ------------------------
            bad_cols = [i for i, r in enumerate(rows) if len(r) < 2]
            if bad_cols:
                print(f"[FAIL] {len(bad_cols)} rows have <2 columns (need id|text|norm_text).")
                print(f"       First bad row: {rows[bad_cols[0]]}")
                ok = False
            else:
                print(f"[OK]   {len(rows)} metadata rows, all have >=2 columns.")
                if any(len(r) < 3 for r in rows):
                    print(f"[WARN] Some rows have only 2 columns (LJSpeech expects 3).")
                    print(f"       FIX: add normalized_text column equal to text.")

            ids = {r[0].strip() for r in rows if r}

        # -- Check 3: wavs/ directory exists ----------------------------------
        wav_entries = sorted(n for n in all_names if n.startswith("wavs/") and n.endswith(".wav"))
        if not wav_entries:
            print(f"\n[FAIL] No wavs/ directory found at zip root.")
            print(f"       FIX: Zip must contain: metadata.csv + wavs/<id>.wav")
            ok = False
        else:
            print(f"\n[OK]   {len(wav_entries)} WAV files found under wavs/")

            # -- Check 4: ID coverage -----------------------------------------
            wav_ids = {Path(n).stem for n in wav_entries}
            missing = ids - wav_ids
            orphans = wav_ids - ids

            if missing:
                print(f"[FAIL] {len(missing)} metadata IDs have no matching WAV file.")
                print(f"       First 5 missing: {list(missing)[:5]}")
                ok = False
            else:
                print(f"[OK]   All {len(ids)} metadata IDs have a matching WAV.")

            if orphans:
                print(f"[WARN] {len(orphans)} WAV files have no metadata entry (orphans).")

            # -- Check 5: Full duration audit on ALL WAVs ---------------------
            print(f"\n[INFO] Full duration audit on all {len(wav_entries)} WAVs")
            print(f"       Usable range: {MIN_DUR_S:.1f}s - {MAX_DUR_S:.1f}s"
                  f"  (XTTS hard limit = 11.6s)")

            extract_dir = Path(os.environ.get("TEMP", "/tmp")) / f"validate_{lang}"
            extract_dir.mkdir(parents=True, exist_ok=True)

            bad_wavs    = []
            over_limit  = []
            under_limit = []

            for wi, wav_name in enumerate(wav_entries):
                zf.extract(wav_name, extract_dir)
                extracted = extract_dir / wav_name
                try:
                    info = torchaudio.info(str(extracted))
                    dur  = info.num_frames / info.sample_rate
                    if dur > MAX_DUR_S:
                        over_limit.append((wav_name, round(dur, 1)))
                    elif dur < MIN_DUR_S:
                        under_limit.append((wav_name, round(dur, 1)))
                except Exception as e:
                    bad_wavs.append((wav_name, str(e)))

                if (wi + 1) % 200 == 0:
                    print(f"       ... {wi+1}/{len(wav_entries)} checked")

            usable     = len(wav_entries) - len(over_limit) - len(under_limit) - len(bad_wavs)
            pct_usable = 100.0 * usable / max(len(wav_entries), 1)

            print(f"\n       Usable ({MIN_DUR_S:.1f}s-{MAX_DUR_S:.1f}s) : {usable}  ({pct_usable:.1f}%)")
            print(f"       Over limit (XTTS drops)   : {len(over_limit)}")
            print(f"       Under limit (noise/sil)   : {len(under_limit)}")
            print(f"       Load errors               : {len(bad_wavs)}")

            if bad_wavs:
                print(f"[FAIL] {len(bad_wavs)} WAVs failed to load:")
                for name, err in bad_wavs[:5]:
                    print(f"       {name}: {err}")
                ok = False

            if len(over_limit) > len(wav_entries) * 0.10:
                pct = 100.0 * len(over_limit) / len(wav_entries)
                print(f"[FAIL] {len(over_limit)} clips ({pct:.0f}%) exceed {MAX_DUR_S}s limit.")
                print(f"       XTTS will silently drop all of them.")
                print(f"       FIX: Run repackage_dataset.py, then re-validate.")
                if over_limit:
                    worst = sorted(over_limit, key=lambda x: -x[1])[:3]
                    for n, d in worst:
                        print(f"         {d:6.1f}s  {n}")
                ok = False
            elif over_limit:
                print(f"[WARN] {len(over_limit)} clips slightly over limit (< 10% -- acceptable).")
            else:
                print(f"[OK]   All WAVs are within XTTS duration limit.")

            if usable < 100:
                print(f"[FAIL] Only {usable} usable clips -- need >=100 for fine-tuning.")
                ok = False
            elif usable < 500:
                print(f"[WARN] Only {usable} usable clips -- 500+ recommended for best results.")
            else:
                print(f"[OK]   {usable} usable clips -- sufficient for fine-tuning.")

    # -- Final verdict --------------------------------------------------------
    print(f"\n{'='*60}")
    if ok:
        print(f"  VALIDATION PASSED -- Safe to launch vertex_forge_v6X_{lang}.yaml")
    else:
        print(f"  VALIDATION FAILED -- DO NOT launch GCP job yet.")
        print(f"     Fix issues above, re-package/repackage, and re-validate.")
    print(f"{'='*60}\n")
    return ok


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate GCP training zip before launch.")
    parser.add_argument("--zip",  required=True, help="Path to the .zip file")
    parser.add_argument("--lang", required=True, choices=["en", "ar", "ur"], help="Language")
    args = parser.parse_args()

    success = validate_zip(args.zip, args.lang)
    exit(0 if success else 1)
