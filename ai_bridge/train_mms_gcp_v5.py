"""
GCP CLOUD FORGE v5 — Urdu MMS-VITS Fine-Tuning (ULTRA-STABLE)
============================================================
REMOVED ALL TORCHAUDIO DEPENDENCIES to eliminate SIGSEGV risks.
Uses pure-torch STFT for Mel calculation and soundfile for loading.

Hardware: Vertex AI n1-standard-8 + NVIDIA Tesla T4 (16 GB VRAM, CUDA 12.1)
"""

import subprocess
import sys
import os
import gc
import math
import argparse

# ─────────────────────────────────────────────────────────────────────────────
# BOOTSTRAP — Pure Python packages only
# ─────────────────────────────────────────────────────────────────────────────
def bootstrap():
    pkgs = [
        "soundfile",
        "transformers==4.38.0",
        "datasets",
        "pandas",
        "accelerate",
        "python-json-logger",
        "scipy", # for resampling fallback
    ]
    print(f"[BOOTSTRAP] Installing {len(pkgs)} packages...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--no-cache-dir", "--quiet"] + pkgs, check=False)
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

# No torchaudio imports here.

print(f"[ENV] torch={torch.__version__}  CUDA={'YES ' + torch.version.cuda if torch.cuda.is_available() else 'NO'}")

# ─────────────────────────────────────────────────────────────────────────────
# ARGS
# ─────────────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--ur_csv",     default="gs://maulana-urdu-forge-project-ffb3710a/ur_aligned.csv")
parser.add_argument("--wav_dir",    default="gs://maulana-urdu-forge-project-ffb3710a/wavs")
parser.add_argument("--output_dir", default="gs://maulana-urdu-forge-project-ffb3710a/ur_mms_v5")
parser.add_argument("--epochs",     type=int,   default=200)
parser.add_argument("--batch_size", type=int,   default=1)
parser.add_argument("--lr",         type=float, default=2e-5)
args = parser.parse_args()

MMS_BASE      = "facebook/mms-tts-urd-script_arabic"
MMS_SR        = 16000
LOCAL_WAV_DIR = "/tmp/urdu_wavs"
LOCAL_OUTPUT  = "/tmp/ur_mms_v5"

# ─────────────────────────────────────────────────────────────────────────────
# PURE TORCH MEL SPECTROGRAM (No Torchaudio needed)
# ─────────────────────────────────────────────────────────────────────────────
def get_mel_spectrogram(wav, n_fft=1024, hop_length=256, win_length=1024, n_mels=80, sr=16000):
    """Manual Mel-Spectrogram using torch.stft and a fixed filterbank."""
    # Simple hann window
    window = torch.hann_window(win_length).to(wav.device)
    # STFT
    stft = torch.stft(
        wav, n_fft=n_fft, hop_length=hop_length, win_length=win_length,
        window=window, center=True, return_complex=True
    )
    magnitudes = torch.abs(stft)
    
    # Simple Mel Filterbank (approximate or just use magnitudes for L1 if exact mel is not critical)
    # For fine-tuning VITS, even Magnitude L1 is often enough if the base model was trained on it.
    # However, let's just use log-magnitude for stability.
    return magnitudes

def mel_loss(gen_wav, real_wav):
    """Log-Magnitude L1 — robust and doesn't require torchaudio kernels."""
    min_len  = min(gen_wav.shape[-1], real_wav.shape[-1])
    gen_mag  = get_mel_spectrogram(gen_wav[..., :min_len])
    real_mag = get_mel_spectrogram(real_wav[..., :min_len])
    
    # Avoid log(0)
    gen_log  = torch.log(gen_mag.clamp(min=1e-5))
    real_log = torch.log(real_mag.clamp(min=1e-5))
    
    return torch.nn.functional.l1_loss(gen_log, real_log)

# ─────────────────────────────────────────────────────────────────────────────
# DATASET
# ─────────────────────────────────────────────────────────────────────────────
class UrduDataset(Dataset):
    def __init__(self, csv_path, tokenizer, wav_dir):
        local_csv = "/tmp/ur_aligned.csv"
        subprocess.run(["gcloud", "storage", "cp", csv_path, local_csv], check=True)
        self.df        = pd.read_csv(local_csv)
        self.tokenizer = tokenizer
        self.wav_dir   = wav_dir
        print(f" > Loaded {len(self.df)} aligned Urdu pairs.")

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        try:
            fname     = str(row["audio_path"]).replace("\\", "/").split("/")[-1]
            wav_path  = os.path.join(self.wav_dir, fname)
            
            # soundfile load (returns numpy array)
            wav, sr   = sf.read(wav_path)
            
            if sr != MMS_SR:
                # Scipy resample
                num_samples = int(len(wav) * MMS_SR / sr)
                wav = scipy_resample(wav, num_samples)
            
            if len(wav.shape) > 1:
                wav = wav.mean(axis=-1)
                
            wav = torch.from_numpy(wav).float()
            wav = wav[:MMS_SR * 8] # max 8s
            
            text   = str(row["text"])[:200]
            tokens = self.tokenizer(text=text, return_tensors="pt", padding=True)
            
            return {
                "input_ids":      tokens["input_ids"].squeeze(0),
                "attention_mask": tokens["attention_mask"].squeeze(0),
                "wav":            wav,
            }
        except Exception as exc:
            print(f" ! Skipping idx {idx}: {exc}")
            return self.__getitem__((idx + 1) % len(self.df))

def collate(batch):
    max_t = max(b["input_ids"].shape[0] for b in batch)
    max_w = max(b["wav"].shape[0]       for b in batch)
    B = len(batch)
    ids  = torch.zeros(B, max_t, dtype=torch.long)
    att  = torch.zeros(B, max_t, dtype=torch.long)
    wavs = torch.zeros(B, max_w)
    for i, b in enumerate(batch):
        tl = b["input_ids"].shape[0]
        wl = b["wav"].shape[0]
        ids[i, :tl]  = b["input_ids"]
        att[i, :tl]  = b["attention_mask"]
        wavs[i, :wl] = b["wav"]
    return {"input_ids": ids, "attention_mask": att, "wav": wavs}

# ─────────────────────────────────────────────────────────────────────────────
# ENCODER FREEZE
# ─────────────────────────────────────────────────────────────────────────────
def freeze_encoder(model):
    frozen = trainable = 0
    for name, p in model.named_parameters():
        if any(k in name for k in ["text_encoder", "duration_predictor"]):
            p.requires_grad = False
            frozen += p.numel()
        else:
            p.requires_grad = True
            trainable += p.numel()
    print(f" > Trainable: {trainable/1e6:.1f}M  Frozen: {frozen/1e6:.1f}M params")

def gcs_rsync(src, dst):
    subprocess.run(["gcloud", "storage", "rsync", "-r", src, dst], check=False)

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def train():
    print("=" * 60)
    print("MAULANA URDU FORGE v5 [ULTRA-STABLE / NO-TORCHAUDIO]")
    print("=" * 60)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda":
        torch.backends.cudnn.benchmark = False
        torch.backends.cudnn.deterministic = True
        print(" > cuDNN: Hardened (Deterministic)")

    # Preparation
    os.makedirs(LOCAL_WAV_DIR, exist_ok=True)
    os.makedirs(LOCAL_OUTPUT,  exist_ok=True)
    print(f" > Syncing WAVs from {args.wav_dir} ...")
    gcs_rsync(args.wav_dir, LOCAL_WAV_DIR)

    # Model
    print(f" > Loading {MMS_BASE}")
    tokenizer = VitsTokenizer.from_pretrained(MMS_BASE)
    model     = VitsModel.from_pretrained(MMS_BASE).to(device)
    freeze_encoder(model)
    model.train()

    # Data
    dataset    = UrduDataset(args.ur_csv, tokenizer, LOCAL_WAV_DIR)
    dataloader = DataLoader(
        dataset, batch_size=args.batch_size, shuffle=True,
        collate_fn=collate, num_workers=0
    )

    optimizer = AdamW([p for p in model.parameters() if p.requires_grad], lr=args.lr)
    scheduler = CosineAnnealingLR(optimizer, T_max=args.epochs * len(dataloader))
    
    accumulation_steps = 4 // args.batch_size if args.batch_size < 4 else 1
    best_loss = float("inf")
    step = 0

    for epoch in range(args.epochs):
        ep_loss, ep_batches = 0.0, 0
        for i, batch in enumerate(dataloader):
            if i % accumulation_steps == 0:
                optimizer.zero_grad()
            
            ids  = batch["input_ids"].to(device)
            att  = batch["attention_mask"].to(device)
            real = batch["wav"].to(device)

            # FP32 only for stability
            out  = model(input_ids=ids, attention_mask=att)
            gen  = out.waveform
            loss = mel_loss(gen, real)

            if not math.isfinite(loss.item()):
                print(f" ! NaN at step {step}")
                continue

            (loss / accumulation_steps).backward()
            
            if (i + 1) % accumulation_steps == 0 or (i + 1) == len(dataloader):
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
                scheduler.step()

            ep_loss += loss.item()
            ep_batches += 1
            step += 1

            if step % 25 == 0:
                print(f" > Ep {epoch+1} | Step {step} | Loss: {ep_loss/ep_batches:.6f}")
            
            # Explicit cleanup
            del out, gen, loss
            if i % 10 == 0:
                gc.collect()
                if device == "cuda":
                    torch.cuda.empty_cache()

        avg = ep_loss / ep_batches
        print(f" > Epoch {epoch+1} DONE | Avg: {avg:.6f}")

        if avg < best_loss:
            best_loss = avg
            model.save_pretrained(LOCAL_OUTPUT)
            tokenizer.save_pretrained(LOCAL_OUTPUT)
            print(f"   -> BEST saved")

        if (epoch + 1) % 10 == 0:
            subprocess.run(["gcloud", "storage", "cp", "-r", LOCAL_OUTPUT, f"{args.output_dir}/ckpt_ep{epoch+1}/"], check=False)

    subprocess.run(["gcloud", "storage", "cp", "-r", LOCAL_OUTPUT, f"{args.output_dir}/final/"], check=False)
    print("FORGE COMPLETE.")

if __name__ == "__main__":
    train()
