"""
GCP CLOUD FORGE v26 — Urdu MMS-VITS "The One-Shot"
===================================================
FIXES:
- Single ZIP download + local unzip (avoids std::runtime_error from multi-file sync).
- Enhanced Dummy module with JsonFormatter to fix sitecustomize.
- FP16 AMP enabled.
- Pure Python logic once unzipped.
"""

import sys
import os
import gc
import math
import argparse
import time
import subprocess
import zipfile

# ── IMPORTS ──────────────────────────────────────────────────────────────
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
parser.add_argument("--zip_path",   default="gs://maulana-urdu-forge-project-ffb3710a/urdu_gcp_forge.zip")
parser.add_argument("--output_dir", default="gs://maulana-urdu-forge-project-ffb3710a/ur_mms_v26")
parser.add_argument("--epochs",     type=int,   default=200)
parser.add_argument("--batch_size", type=int,   default=4)
parser.add_argument("--lr",         type=float, default=2e-5)
args = parser.parse_args()

MMS_BASE      = "facebook/mms-tts-urd-script_arabic"
MMS_SR        = 16000
LOCAL_WAV_DIR = "/tmp/urdu_wavs"
LOCAL_ZIP     = "/tmp/data.zip"
LOCAL_OUTPUT  = "/tmp/ur_mms_v26"

# ── ZIP SYNC ──────────────────────────────────────────────────────────────────
def sync_dataset_zip():
    """Download one large zip and extract. Extremely stable."""
    print(f" > ONE-SHOT SYNC: Downloading {args.zip_path}...", flush=True)
    subprocess.run(["gcloud", "storage", "cp", args.zip_path, LOCAL_ZIP], check=True)
    
    print(f" > Extracting to {LOCAL_WAV_DIR}...", flush=True)
    os.makedirs(LOCAL_WAV_DIR, exist_ok=True)
    with zipfile.ZipFile(LOCAL_ZIP, 'r') as zip_ref:
        zip_ref.extractall(LOCAL_WAV_DIR)
        
    # Check content: some zips have a nested folder
    # Find where the WAVs actually are
    for root, dirs, files in os.walk(LOCAL_WAV_DIR):
        wavs = [f for f in files if f.endswith(".wav")]
        if len(wavs) > 10:
            print(f" > Found {len(wavs)} WAVs in {root}", flush=True)
            return root
    return LOCAL_WAV_DIR

# ── HELPERS ──────────────────────────────────────────────────────────────────
def get_mel_spectrogram(wav):
    window = torch.hann_window(1024).to(wav.device)
    stft = torch.stft(
        wav, n_fft=1024, hop_length=256, win_length=1024,
        window=window, center=True, return_complex=True
    )
    return torch.abs(stft)

def mel_loss(gen_wav, real_wav):
    min_len = min(gen_wav.shape[-1], real_wav.shape[-1])
    gen_mag = get_mel_spectrogram(gen_wav[..., :min_len])
    real_mag = get_mel_spectrogram(real_wav[..., :min_len])
    return torch.nn.functional.l1_loss(
        torch.log(gen_mag.clamp(min=1e-5)), 
        torch.log(real_mag.clamp(min=1e-5))
    )

# ── DATASET ───────────────────────────────────────────────────────────────────
class UrduV26Dataset(Dataset):
    def __init__(self, csv_path, tokenizer, active_wav_dir):
        local_csv = "/tmp/ur_aligned.csv"
        subprocess.run(["gcloud", "storage", "cp", csv_path, local_csv], check=True)
        self.df = pd.read_csv(local_csv)
        self.tokenizer = tokenizer
        self.active_wav_dir = active_wav_dir

    def __len__(self): return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        try:
            fname = str(row["audio_path"]).replace("\\", "/").split("/")[-1]
            wav_path = os.path.join(self.active_wav_dir, fname)
            
            wav, sr = sf.read(wav_path)
            if sr != MMS_SR:
                wav = scipy_resample(wav, int(len(wav) * MMS_SR / sr))
            if len(wav.shape) > 1:
                wav = wav.mean(axis=-1)
            
            wav = torch.from_numpy(wav).float()[:MMS_SR * 8]
            tokens = self.tokenizer(text=str(row["text"])[:200], return_tensors="pt", padding=True)
            
            return {
                "input_ids": tokens["input_ids"].squeeze(0),
                "attention_mask": tokens["attention_mask"].squeeze(0),
                "wav": wav
            }
        except Exception:
            return self.__getitem__(np.random.randint(0, len(self.df)))

def collate(batch):
    max_t = max(b["input_ids"].shape[0] for b in batch)
    max_w = max(b["wav"].shape[0] for b in batch)
    B = len(batch)
    ids, att, wavs = torch.zeros(B, max_t, dtype=torch.long), torch.zeros(B, max_t, dtype=torch.long), torch.zeros(B, max_w)
    for i, b in enumerate(batch):
        tl, wl = b["input_ids"].shape[0], b["wav"].shape[0]
        ids[i, :tl], att[i, :tl], wavs[i, :wl] = b["input_ids"], b["attention_mask"], b["wav"]
    return {"input_ids": ids, "attention_mask": att, "wav": wavs}

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60, flush=True)
    print("MAULANA URDU FORGE v26 [ONE-SHOT ZIP / HARDENED]", flush=True)
    print("=" * 60, flush=True)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    os.makedirs(LOCAL_OUTPUT, exist_ok=True)

    tokenizer = VitsTokenizer.from_pretrained(MMS_BASE)
    model = VitsModel.from_pretrained(MMS_BASE).to(device)
    
    for n, p in model.named_parameters():
        if any(k in n for k in ["text_encoder", "duration_predictor"]):
            p.requires_grad = False
    
    model.train()

    active_wav_dir = sync_dataset_zip()
    dataset = UrduV26Dataset(args.ur_csv, tokenizer, active_wav_dir)
    dataloader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True, collate_fn=collate, num_workers=0)
    
    optimizer = AdamW([p for p in model.parameters() if p.requires_grad], lr=args.lr)
    scheduler = CosineAnnealingLR(optimizer, T_max=args.epochs * len(dataloader))
    scaler = GradScaler(enabled=(device == "cuda"))

    best_loss = float("inf")
    step, start_time = 0, time.time()

    for epoch in range(args.epochs):
        ep_loss, ep_batches = 0.0, 0
        for i, batch in enumerate(dataloader):
            optimizer.zero_grad()
            ids, att, real = batch["input_ids"].to(device), batch["attention_mask"].to(device), batch["wav"].to(device)

            with autocast(enabled=(device == "cuda")):
                loss = mel_loss(model(input_ids=ids, attention_mask=att).waveform, real)

            if not math.isfinite(loss.item()): continue

            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            scaler.step(optimizer)
            scaler.update()
            scheduler.step()

            ep_loss, ep_batches, step = ep_loss + loss.item(), ep_batches + 1, step + 1
            if step % 25 == 0:
                avg = ep_loss / ep_batches
                print(f" > Ep {epoch+1} | Step {step} | Loss: {avg:.4f} | {(step*args.batch_size)/(time.time()-start_time):.1f} smp/s", flush=True)

            if i % 10 == 0:
                gc.collect()
                if device == "cuda": torch.cuda.empty_cache()

        avg = ep_loss / max(1, ep_batches)
        if avg < best_loss:
            best_loss = avg
            model.save_pretrained(LOCAL_OUTPUT)
            tokenizer.save_pretrained(LOCAL_OUTPUT)
            print(f" > BEST CHECKPOINT: {avg:.6f}", flush=True)
            
        if (epoch + 1) % 10 == 0:
            os.system(f"gsutil -m cp -r {LOCAL_OUTPUT} {args.output_dir}/ckpt_ep{epoch+1}/")
            
    os.system(f"gsutil -m cp -r {LOCAL_OUTPUT} {args.output_dir}/final/")
    print("FORGE COMPLETE.")

if __name__ == "__main__":
    main()
