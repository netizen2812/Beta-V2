"""
GCP CLOUD FORGE v9 — Urdu MMS-VITS Hardened (SIGSEGV FIX)
========================================================
- Stability: num_workers=0 (prevents shared memory corruption).
- Precision: FP32 only (maximum stability, no GradScaler overhead).
- Environment: python-json-logger pre-installed in YAML.
"""

import subprocess
import sys
import os
import gc
import math
import argparse
import time

def bootstrap():
    pkgs = ["soundfile", "transformers==4.38.0", "datasets", "pandas", "accelerate", "scipy", "python-json-logger"]
    print(f"[BOOTSTRAP] Installing {len(pkgs)} packages...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--no-cache-dir", "--quiet"] + pkgs, check=False)

bootstrap()

import torch
import soundfile as sf
import pandas as pd
from torch.utils.data import Dataset, DataLoader
from transformers import VitsModel, VitsTokenizer
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from scipy.signal import resample as scipy_resample

parser = argparse.ArgumentParser()
parser.add_argument("--ur_csv",     default="gs://maulana-urdu-forge-project-ffb3710a/ur_aligned.csv")
parser.add_argument("--wav_dir",    default="gs://maulana-urdu-forge-project-ffb3710a/wavs")
parser.add_argument("--output_dir", default="gs://maulana-urdu-forge-project-ffb3710a/ur_mms_v9")
parser.add_argument("--epochs",     type=int,   default=200)
parser.add_argument("--batch_size", type=int,   default=2) # Conservative BS for stability
parser.add_argument("--lr",         type=float, default=2e-5)
args = parser.parse_args()

MMS_BASE, MMS_SR = "facebook/mms-tts-urd-script_arabic", 16000
LOCAL_WAV_DIR, LOCAL_OUTPUT = "/tmp/urdu_wavs", "/tmp/ur_mms_v9"

def get_mel_spectrogram(wav, n_fft=1024, hop_length=256, win_length=1024):
    window = torch.hann_window(win_length).to(wav.device)
    stft = torch.stft(wav, n_fft=n_fft, hop_length=hop_length, win_length=win_length, window=window, center=True, return_complex=True)
    return torch.abs(stft)

def mel_loss(gen_wav, real_wav):
    min_len = min(gen_wav.shape[-1], real_wav.shape[-1])
    gen_mag = get_mel_spectrogram(gen_wav[..., :min_len])
    real_mag = get_mel_spectrogram(real_wav[..., :min_len])
    return torch.nn.functional.l1_loss(torch.log(gen_mag.clamp(min=1e-5)), torch.log(real_mag.clamp(min=1e-5)))

class UrduDataset(Dataset):
    def __init__(self, csv_path, tokenizer, remote_wav_dir):
        local_csv = "/tmp/ur_aligned.csv"
        subprocess.run(["gcloud", "storage", "cp", csv_path, local_csv], check=True)
        self.df, self.tokenizer, self.remote_wav_dir = pd.read_csv(local_csv), tokenizer, remote_wav_dir
        os.makedirs(LOCAL_WAV_DIR, exist_ok=True)
        print(f" > Dataset Ready: {len(self.df)} pairs.", flush=True)

    def __len__(self): return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        try:
            fname = str(row["audio_path"]).replace("\\", "/").split("/")[-1]
            wav_path = os.path.join(LOCAL_WAV_DIR, fname)
            if not os.path.exists(wav_path):
                subprocess.run(["gcloud", "storage", "cp", f"{self.remote_wav_dir.rstrip('/')}/{fname}", wav_path], capture_output=True)
            wav, sr = sf.read(wav_path)
            if sr != MMS_SR: wav = scipy_resample(wav, int(len(wav) * MMS_SR / sr))
            if len(wav.shape) > 1: wav = wav.mean(axis=-1)
            wav = torch.from_numpy(wav).float()[:MMS_SR * 8]
            tokens = self.tokenizer(text=str(row["text"])[:200], return_tensors="pt", padding=True)
            return {"input_ids": tokens["input_ids"].squeeze(0), "attention_mask": tokens["attention_mask"].squeeze(0), "wav": wav}
        except Exception: return self.__getitem__((idx + 1) % len(self.df))

def collate(batch):
    max_t, max_w, B = max(b["input_ids"].shape[0] for b in batch), max(b["wav"].shape[0] for b in batch), len(batch)
    ids, att, wavs = torch.zeros(B, max_t, dtype=torch.long), torch.zeros(B, max_t, dtype=torch.long), torch.zeros(B, max_w)
    for i, b in enumerate(batch):
        tl, wl = b["input_ids"].shape[0], b["wav"].shape[0]
        ids[i, :tl], att[i, :tl], wavs[i, :wl] = b["input_ids"], b["attention_mask"], b["wav"]
    return {"input_ids": ids, "attention_mask": att, "wav": wavs}

def train():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f" > HARDENED MODE: device={device}, num_workers=0, precision=FP32", flush=True)

    os.makedirs(LOCAL_OUTPUT, exist_ok=True)
    tokenizer = VitsTokenizer.from_pretrained(MMS_BASE)
    model = VitsModel.from_pretrained(MMS_BASE).to(device)
    
    # Freeze encoder
    for n, p in model.named_parameters():
        if any(k in n for k in ["text_encoder", "duration_predictor"]): p.requires_grad = False
    model.train()

    # CRITICAL: num_workers=0 to prevent SIGSEGV
    dataloader = DataLoader(UrduDataset(args.ur_csv, tokenizer, args.wav_dir), batch_size=args.batch_size, shuffle=True, collate_fn=collate, num_workers=0)
    
    optimizer = AdamW([p for p in model.parameters() if p.requires_grad], lr=args.lr)
    scheduler = CosineAnnealingLR(optimizer, T_max=args.epochs * len(dataloader))

    best_loss, step, start_time = float("inf"), 0, time.time()
    for epoch in range(args.epochs):
        ep_loss, ep_batches = 0.0, 0
        for i, batch in enumerate(dataloader):
            optimizer.zero_grad()
            ids, att, real = batch["input_ids"].to(device), batch["attention_mask"].to(device), batch["wav"].to(device)
            
            # FP32 Forward
            loss = mel_loss(model(input_ids=ids, attention_mask=att).waveform, real)
            
            if not math.isfinite(loss.item()): continue
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()

            ep_loss, ep_batches, step = ep_loss + loss.item(), ep_batches + 1, step + 1
            if step % 25 == 0:
                print(f" > Ep {epoch+1} | Step {step} | Loss: {ep_loss/ep_batches:.4f} | {(step*args.batch_size)/(time.time()-start_time):.1f} smp/s", flush=True)
            
            if i % 10 == 0:
                gc.collect()
                if device == "cuda": torch.cuda.empty_cache()

        avg = ep_loss / max(1, ep_batches)
        if avg < best_loss:
            best_loss = avg
            model.save_pretrained(LOCAL_OUTPUT)
            tokenizer.save_pretrained(LOCAL_OUTPUT)
            print(f" > BEST SAVED (Avg: {avg:.6f})", flush=True)
        
        if (epoch + 1) % 10 == 0:
            subprocess.run(["gcloud", "storage", "cp", "-r", LOCAL_OUTPUT, f"{args.output_dir}/ckpt_ep{epoch+1}/"], check=False)
            
    subprocess.run(["gcloud", "storage", "cp", "-r", LOCAL_OUTPUT, f"{args.output_dir}/final/"], check=False)

if __name__ == "__main__": train()
