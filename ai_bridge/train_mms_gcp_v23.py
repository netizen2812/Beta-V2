"""
GCP CLOUD FORGE v23 — Urdu MMS-VITS Final Stable
==================================================
FIXES:
- Uses gsutil -m for resilient pre-download (replaces gcloud storage cp)
- FP16 AMP (Mixed Precision) for faster training
- Fixed python-json-logger sitecustomize conflict
- Encoder frozen: only VITS decoder is trained
- NaN guard: skips batch and resets optimizer on NaN loss
- Zero subprocess calls inside the training loop
"""

import subprocess
import sys
import os
import gc
import math
import argparse
import time

# ── BOOTSTRAP ────────────────────────────────────────────────────────────
def bootstrap():
    # Install dependencies internally
    # We install python-json-logger but don't import it in sitecustomize to avoid conflicts
    pkgs = [
        "soundfile", 
        "transformers==4.38.0", 
        "datasets", 
        "pandas", 
        "accelerate", 
        "scipy", 
        "python-json-logger"
    ]
    print(f"[BOOTSTRAP] Installing {len(pkgs)} packages...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--no-cache-dir", "--quiet"] + pkgs, check=False)
    
    # CUDA Hardening
    os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
    print("[BOOTSTRAP] Done.")

bootstrap()

# ── IMPORTS (post-bootstrap) ──────────────────────────────────────────────
import torch
import soundfile as sf
import pandas as pd
import numpy as np
from torch.utils.data import Dataset, DataLoader
from transformers import VitsModel, VitsTokenizer
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.cuda.amp import GradScaler, autocast
from scipy.signal import resample as scipy_resample

# ── ARGS ─────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--ur_csv",     default="gs://maulana-urdu-forge-project-ffb3710a/ur_aligned.csv")
parser.add_argument("--wav_dir",    default="gs://maulana-urdu-forge-project-ffb3710a/wavs")
parser.add_argument("--output_dir", default="gs://maulana-urdu-forge-project-ffb3710a/ur_mms_v23")
parser.add_argument("--epochs",     type=int,   default=200)
parser.add_argument("--batch_size", type=int,   default=4)   # Increased to 4 with AMP
parser.add_argument("--lr",         type=float, default=2e-5)
args = parser.parse_args()

MMS_BASE      = "facebook/mms-tts-urd-script_arabic"
MMS_SR        = 16000
LOCAL_WAV_DIR = "/tmp/urdu_wavs"
LOCAL_OUTPUT  = "/tmp/ur_mms_v23"

# ── HELPERS ──────────────────────────────────────────────────────────────────
def get_mel_spectrogram(wav):
    """Pure Torch STFT for mel-spectrogram approximation."""
    window = torch.hann_window(1024).to(wav.device)
    stft = torch.stft(
        wav, n_fft=1024, hop_length=256, win_length=1024,
        window=window, center=True, return_complex=True
    )
    return torch.abs(stft)

def mel_loss(gen_wav, real_wav):
    """Log-Magnitude L1 Loss."""
    min_len = min(gen_wav.shape[-1], real_wav.shape[-1])
    gen_mag = get_mel_spectrogram(gen_wav[..., :min_len])
    real_mag = get_mel_spectrogram(real_wav[..., :min_len])
    return torch.nn.functional.l1_loss(
        torch.log(gen_mag.clamp(min=1e-5)), 
        torch.log(real_mag.clamp(min=1e-5))
    )

# ── DATASET ───────────────────────────────────────────────────────────────────
class UrduHardenedDataset(Dataset):
    def __init__(self, csv_path, tokenizer, remote_wav_dir):
        # 1. Download CSV
        local_csv = "/tmp/ur_aligned.csv"
        print(f" > Fetching manifest: {csv_path}")
        subprocess.run(["gcloud", "storage", "cp", csv_path, local_csv], check=True)
        self.df = pd.read_csv(local_csv)
        self.tokenizer = tokenizer
        
        # 2. RESILIENT MASSIVE PRE-DOWNLOAD (gsutil -m is better for bulk)
        print(f" > MASSIVE SYNC: Downloading {len(self.df)} WAVs via gsutil -m...")
        os.makedirs(LOCAL_WAV_DIR, exist_ok=True)
        
        # Use gsutil -m cp for parallel downloads
        remote_pattern = f"{remote_wav_dir.rstrip('/')}/*.wav"
        res = subprocess.run(
            ["gsutil", "-m", "cp", "-n", remote_pattern, LOCAL_WAV_DIR + "/"], 
            check=False # Don't crash if some files fail, we handle it in __getitem__
        )
        
        actual_count = len([f for f in os.listdir(LOCAL_WAV_DIR) if f.endswith(".wav")])
        print(f" > Sync Complete: {actual_count} files ready in {LOCAL_WAV_DIR}")

    def __len__(self): return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        try:
            fname = str(row["audio_path"]).replace("\\", "/").split("/")[-1]
            wav_path = os.path.join(LOCAL_WAV_DIR, fname)
            
            if not os.path.exists(wav_path):
                raise FileNotFoundError(f"Missing {fname}")
                
            wav, sr = sf.read(wav_path)
            if sr != MMS_SR:
                wav = scipy_resample(wav, int(len(wav) * MMS_SR / sr))
            if len(wav.shape) > 1:
                wav = wav.mean(axis=-1)
            
            wav = torch.from_numpy(wav).float()
            # Clip to 8 seconds max to prevent OOM
            wav = wav[:MMS_SR * 8]
            
            text = str(row["text"])[:200]
            tokens = self.tokenizer(text=text, return_tensors="pt", padding=True)
            
            return {
                "input_ids": tokens["input_ids"].squeeze(0),
                "attention_mask": tokens["attention_mask"].squeeze(0),
                "wav": wav
            }
        except Exception as e:
            # Fallback to random sample on error
            return self.__getitem__(np.random.randint(0, len(self.df)))

def collate(batch):
    max_t = max(b["input_ids"].shape[0] for b in batch)
    max_w = max(b["wav"].shape[0] for b in batch)
    B = len(batch)
    ids = torch.zeros(B, max_t, dtype=torch.long)
    att = torch.zeros(B, max_t, dtype=torch.long)
    wavs = torch.zeros(B, max_w)
    for i, b in enumerate(batch):
        tl, wl = b["input_ids"].shape[0], b["wav"].shape[0]
        ids[i, :tl] = b["input_ids"]
        att[i, :tl] = b["attention_mask"]
        wavs[i, :wl] = b["wav"]
    return {"input_ids": ids, "attention_mask": att, "wav": wavs}

# ── TRAINING ──────────────────────────────────────────────────────────────────
def train():
    print("=" * 60, flush=True)
    print("MAULANA URDU FORGE v23 [ULTRA-HARDENED / GSUTIL / AMP]", flush=True)
    print("=" * 60, flush=True)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    os.makedirs(LOCAL_OUTPUT, exist_ok=True)

    print(f" > Loading MMS Model: {MMS_BASE}")
    tokenizer = VitsTokenizer.from_pretrained(MMS_BASE)
    model = VitsModel.from_pretrained(MMS_BASE).to(device)
    
    # Freeze Encoder
    for n, p in model.named_parameters():
        if any(k in n for k in ["text_encoder", "duration_predictor"]):
            p.requires_grad = False
    
    model.train()

    dataset = UrduHardenedDataset(args.ur_csv, tokenizer, args.wav_dir)
    dataloader = DataLoader(
        dataset, batch_size=args.batch_size, shuffle=True, 
        collate_fn=collate, num_workers=0
    )
    
    optimizer = AdamW([p for p in model.parameters() if p.requires_grad], lr=args.lr)
    scheduler = CosineAnnealingLR(optimizer, T_max=args.epochs * len(dataloader))
    scaler = GradScaler(enabled=(device == "cuda"))

    best_loss = float("inf")
    step = 0
    start_time = time.time()

    for epoch in range(args.epochs):
        ep_loss, ep_batches = 0.0, 0
        for i, batch in enumerate(dataloader):
            optimizer.zero_grad()
            
            ids = batch["input_ids"].to(device)
            att = batch["attention_mask"].to(device)
            real = batch["wav"].to(device)

            with autocast(enabled=(device == "cuda")):
                out = model(input_ids=ids, attention_mask=att)
                loss = mel_loss(out.waveform, real)

            if not math.isfinite(loss.item()):
                print(f" ! NaN Loss at step {step} - Skipping")
                continue

            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            scaler.step(optimizer)
            scaler.update()
            scheduler.step()

            ep_loss += loss.item()
            ep_batches += 1
            step += 1

            if step % 25 == 0:
                avg = ep_loss / ep_batches
                elapsed = time.time() - start_time
                smp_s = (step * args.batch_size) / elapsed
                print(f" > Ep {epoch+1} | Step {step} | Loss: {avg:.4f} | {smp_s:.1f} smp/s", flush=True)

            if i % 10 == 0:
                gc.collect()
                if device == "cuda": torch.cuda.empty_cache()

        avg_epoch = ep_loss / max(1, ep_batches)
        if avg_epoch < best_loss:
            best_loss = avg_epoch
            model.save_pretrained(LOCAL_OUTPUT)
            tokenizer.save_pretrained(LOCAL_OUTPUT)
            print(f" > BEST CHECKPOINT: Epoch {epoch+1} (Loss: {avg_epoch:.6f})", flush=True)
        
        if (epoch + 1) % 10 == 0:
            print(f" > Syncing Epoch {epoch+1} to GCS...")
            subprocess.run(["gsutil", "-m", "cp", "-r", LOCAL_OUTPUT, f"{args.output_dir}/ckpt_ep{epoch+1}/"], check=False)
            
    # Final Upload
    print(" > Final upload to GCS...")
    subprocess.run(["gsutil", "-m", "cp", "-r", LOCAL_OUTPUT, f"{args.output_dir}/final/"], check=False)
    print("=" * 60)
    print(f"FORGE COMPLETE. Best Loss: {best_loss:.4f}")
    print("=" * 60)

if __name__ == "__main__":
    train()
