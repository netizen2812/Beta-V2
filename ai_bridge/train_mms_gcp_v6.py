"""
GCP CLOUD FORGE v6 — Urdu MMS-VITS Fine-Tuning (LAZY-LOAD)
=========================================================
- Removed global rsync (failed with SIGSEGV in v17).
- Implemented lazy-downloading of WAVs in Dataset.__getitem__.
- Added CUDA allocation hardening.
- No torchaudio dependency.
"""

import subprocess
import sys
import os
import gc
import math
import argparse
import time

# ─────────────────────────────────────────────────────────────────────────────
# BOOTSTRAP
# ─────────────────────────────────────────────────────────────────────────────
def bootstrap():
    pkgs = [
        "soundfile",
        "transformers==4.38.0",
        "datasets",
        "pandas",
        "accelerate",
        "scipy",
    ]
    print(f"[BOOTSTRAP] Installing {len(pkgs)} packages...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--no-cache-dir", "--quiet"] + pkgs, check=False)
    
    # CUDA Hardening
    os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
    print("[BOOTSTRAP] Done.")

bootstrap()

import torch
import soundfile as sf
import pandas as pd
import numpy as np
from torch.utils.data import Dataset, DataLoader
from transformers import VitsModel, VitsTokenizer
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from scipy.signal import resample as scipy_resample

# ─────────────────────────────────────────────────────────────────────────────
# ARGS
# ─────────────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--ur_csv",     default="gs://maulana-urdu-forge-project-ffb3710a/ur_aligned.csv")
parser.add_argument("--wav_dir",    default="gs://maulana-urdu-forge-project-ffb3710a/wavs")
parser.add_argument("--output_dir", default="gs://maulana-urdu-forge-project-ffb3710a/ur_mms_v6")
parser.add_argument("--epochs",     type=int,   default=200)
parser.add_argument("--batch_size", type=int,   default=1)
parser.add_argument("--lr",         type=float, default=2e-5)
args = parser.parse_args()

MMS_BASE      = "facebook/mms-tts-urd-script_arabic"
MMS_SR        = 16000
LOCAL_WAV_DIR = "/tmp/urdu_wavs"
LOCAL_OUTPUT  = "/tmp/ur_mms_v6"

# ─────────────────────────────────────────────────────────────────────────────
# LOSS
# ─────────────────────────────────────────────────────────────────────────────
def get_mel_spectrogram(wav, n_fft=1024, hop_length=256, win_length=1024, n_mels=80, sr=16000):
    window = torch.hann_window(win_length).to(wav.device)
    stft = torch.stft(
        wav, n_fft=n_fft, hop_length=hop_length, win_length=win_length,
        window=window, center=True, return_complex=True
    )
    return torch.abs(stft)

def mel_loss(gen_wav, real_wav):
    min_len  = min(gen_wav.shape[-1], real_wav.shape[-1])
    gen_mag  = get_mel_spectrogram(gen_wav[..., :min_len])
    real_mag = get_mel_spectrogram(real_wav[..., :min_len])
    return torch.nn.functional.l1_loss(torch.log(gen_mag.clamp(min=1e-5)), torch.log(real_mag.clamp(min=1e-5)))

# ─────────────────────────────────────────────────────────────────────────────
# DATASET (LAZY LOAD)
# ─────────────────────────────────────────────────────────────────────────────
class UrduDataset(Dataset):
    def __init__(self, csv_path, tokenizer, remote_wav_dir):
        local_csv = "/tmp/ur_aligned.csv"
        subprocess.run(["gcloud", "storage", "cp", csv_path, local_csv], check=True)
        self.df             = pd.read_csv(local_csv)
        self.tokenizer      = tokenizer
        self.remote_wav_dir = remote_wav_dir
        os.makedirs(LOCAL_WAV_DIR, exist_ok=True)
        print(f" > Dataset: {len(self.df)} pairs ready for lazy-loading.", flush=True)

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        try:
            fname     = str(row["audio_path"]).replace("\\", "/").split("/")[-1]
            wav_path  = os.path.join(LOCAL_WAV_DIR, fname)
            
            # Lazy download
            if not os.path.exists(wav_path):
                # FIXED: gs:// path joining
                bucket_base = self.remote_wav_dir.rstrip("/")
                remote_path = f"{bucket_base}/{fname}"
                
                print(f" > Downloading {fname} ...", flush=True)
                res = subprocess.run(["gcloud", "storage", "cp", remote_path, wav_path], capture_output=True, text=True)
                if res.returncode != 0:
                    print(f" ! Download failed for {fname}: {res.stderr}", flush=True)
                    raise FileNotFoundError(f"Failed to download {remote_path}")

            if not os.path.exists(wav_path):
                raise FileNotFoundError(f"Could not download {fname}")

            wav, sr = sf.read(wav_path)
            if sr != MMS_SR:
                num_samples = int(len(wav) * MMS_SR / sr)
                wav = scipy_resample(wav, num_samples)
            if len(wav.shape) > 1:
                wav = wav.mean(axis=-1)
                
            wav = torch.from_numpy(wav).float()
            wav = wav[:MMS_SR * 8]
            
            tokens = self.tokenizer(text=str(row["text"])[:200], return_tensors="pt", padding=True)
            return {
                "input_ids":      tokens["input_ids"].squeeze(0),
                "attention_mask": tokens["attention_mask"].squeeze(0),
                "wav":            wav,
            }
        except Exception as exc:
            # Skip corrupt or missing files
            return self.__getitem__((idx + 1) % len(self.df))

def collate(batch):
    max_t = max(b["input_ids"].shape[0] for b in batch)
    max_w = max(b["wav"].shape[0]       for b in batch)
    B = len(batch)
    ids  = torch.zeros(B, max_t, dtype=torch.long)
    att  = torch.zeros(B, max_t, dtype=torch.long)
    wavs = torch.zeros(B, max_w)
    for i, b in enumerate(batch):
        tl, wl = b["input_ids"].shape[0], b["wav"].shape[0]
        ids[i, :tl]  = b["input_ids"]
        att[i, :tl]  = b["attention_mask"]
        wavs[i, :wl] = b["wav"]
    return {"input_ids": ids, "attention_mask": att, "wav": wavs}

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def train():
    print("=" * 60, flush=True)
    print("MAULANA URDU FORGE v6 [LAZY-LOAD / NO-RSYNC]", flush=True)
    print("=" * 60, flush=True)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda":
        torch.backends.cudnn.benchmark = False
        torch.backends.cudnn.deterministic = True

    os.makedirs(LOCAL_OUTPUT,  exist_ok=True)

    print(f" > Loading {MMS_BASE}", flush=True)
    tokenizer = VitsTokenizer.from_pretrained(MMS_BASE)
    model     = VitsModel.from_pretrained(MMS_BASE).to(device)
    
    # Freeze Encoder
    for name, p in model.named_parameters():
        if any(k in name for k in ["text_encoder", "duration_predictor"]):
            p.requires_grad = False
    
    model.train()

    dataset    = UrduDataset(args.ur_csv, tokenizer, args.wav_dir)
    dataloader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True, collate_fn=collate, num_workers=0)

    optimizer = AdamW([p for p in model.parameters() if p.requires_grad], lr=args.lr)
    scheduler = CosineAnnealingLR(optimizer, T_max=args.epochs * len(dataloader))
    
    acc_steps = 4 // args.batch_size if args.batch_size < 4 else 1
    best_loss = float("inf")
    step = 0

    for epoch in range(args.epochs):
        ep_loss, ep_batches = 0.0, 0
        for i, batch in enumerate(dataloader):
            if i % acc_steps == 0:
                optimizer.zero_grad()
            
            ids, att, real = batch["input_ids"].to(device), batch["attention_mask"].to(device), batch["wav"].to(device)

            out  = model(input_ids=ids, attention_mask=att)
            loss = mel_loss(out.waveform, real) / acc_steps

            if not math.isfinite(loss.item()): continue

            loss.backward()
            
            if (i + 1) % acc_steps == 0:
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
                scheduler.step()

            ep_loss += loss.item() * acc_steps
            ep_batches += 1
            step += 1

            if step % 25 == 0:
                print(f" > Ep {epoch+1} | Step {step} | Loss: {ep_loss/ep_batches:.6f}", flush=True)
            
            del out, loss
            if i % 10 == 0:
                gc.collect()
                if device == "cuda": torch.cuda.empty_cache()

        avg = ep_loss / max(1, ep_batches)
        print(f" > Epoch {epoch+1} DONE | Avg: {avg:.6f}", flush=True)

        if avg < best_loss:
            best_loss = avg
            model.save_pretrained(LOCAL_OUTPUT)
            tokenizer.save_pretrained(LOCAL_OUTPUT)
            print(f"   -> BEST saved", flush=True)

        if (epoch + 1) % 10 == 0:
            subprocess.run(["gcloud", "storage", "cp", "-r", LOCAL_OUTPUT, f"{args.output_dir}/ckpt_ep{epoch+1}/"], check=False)

    subprocess.run(["gcloud", "storage", "cp", "-r", LOCAL_OUTPUT, f"{args.output_dir}/final/"], check=False)
    print("FORGE COMPLETE.")

if __name__ == "__main__":
    train()
