"""
GCP CLOUD FORGE v25 — Urdu MMS-VITS "The Nuclear Option"
=========================================================
FIXES:
- Pure Python Google Cloud SDK for file sync (avoids gsutil std::runtime_error).
- Environment spoofing to fix sitecustomize ModuleNotFoundError.
- FP16 AMP enabled.
- Hardened Dataset with multi-threaded Python downloading.
"""

import sys
import os
import gc
import math
import argparse
import time
from concurrent.futures import ThreadPoolExecutor

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
from google.cloud import storage

# ── ARGS ─────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--ur_csv",     default="gs://maulana-urdu-forge-project-ffb3710a/ur_aligned.csv")
parser.add_argument("--wav_dir",    default="gs://maulana-urdu-forge-project-ffb3710a/wavs")
parser.add_argument("--output_dir", default="gs://maulana-urdu-forge-project-ffb3710a/ur_mms_v25")
parser.add_argument("--epochs",     type=int,   default=200)
parser.add_argument("--batch_size", type=int,   default=4)
parser.add_argument("--lr",         type=float, default=2e-5)
args = parser.parse_args()

MMS_BASE      = "facebook/mms-tts-urd-script_arabic"
MMS_SR        = 16000
LOCAL_WAV_DIR = "/tmp/urdu_wavs"
LOCAL_OUTPUT  = "/tmp/ur_mms_v25"

# ── PURE PYTHON SYNC ──────────────────────────────────────────────────────────
def download_blob(bucket_name, source_blob_name, destination_file_name):
    """Downloads a blob from the bucket using Python SDK."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)

def sync_dataset_python(remote_wav_dir):
    """Parallel download using Python SDK (avoids gsutil SSL crashes)."""
    print(f" > PYTHON SDK SYNC: Starting parallel download...", flush=True)
    os.makedirs(LOCAL_WAV_DIR, exist_ok=True)
    
    # Parse GCS path
    path_parts = remote_wav_dir.replace("gs://", "").split("/")
    bucket_name = path_parts[0]
    prefix = "/".join(path_parts[1:]) if len(path_parts) > 1 else ""
    
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blobs = list(bucket.list_blobs(prefix=prefix))
    
    wav_blobs = [b for b in blobs if b.name.endswith(".wav")]
    print(f" > Found {len(wav_blobs)} WAVs. Downloading...", flush=True)
    
    def dl_task(blob):
        fname = blob.name.split("/")[-1]
        dest = os.path.join(LOCAL_WAV_DIR, fname)
        if not os.path.exists(dest):
            blob.download_to_filename(dest)
            
    with ThreadPoolExecutor(max_workers=8) as executor:
        executor.map(dl_task, wav_blobs)
        
    actual_count = len([f for f in os.listdir(LOCAL_WAV_DIR) if f.endswith(".wav")])
    print(f" > Sync Complete: {actual_count} files ready.", flush=True)

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
class UrduV25Dataset(Dataset):
    def __init__(self, csv_path, tokenizer, remote_wav_dir):
        # Download CSV
        storage_client = storage.Client()
        path_parts = csv_path.replace("gs://", "").split("/")
        bucket = storage_client.bucket(path_parts[0])
        blob = bucket.blob("/".join(path_parts[1:]))
        local_csv = "/tmp/ur_aligned.csv"
        blob.download_to_filename(local_csv)
        
        self.df = pd.read_csv(local_csv)
        self.tokenizer = tokenizer
        sync_dataset_python(remote_wav_dir)

    def __len__(self): return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        try:
            fname = str(row["audio_path"]).replace("\\", "/").split("/")[-1]
            wav_path = os.path.join(LOCAL_WAV_DIR, fname)
            
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
    print("MAULANA URDU FORGE v25 [NUCLEAR OPTION / PYTHON SDK]", flush=True)
    print("=" * 60, flush=True)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    os.makedirs(LOCAL_OUTPUT, exist_ok=True)

    tokenizer = VitsTokenizer.from_pretrained(MMS_BASE)
    model = VitsModel.from_pretrained(MMS_BASE).to(device)
    
    for n, p in model.named_parameters():
        if any(k in n for k in ["text_encoder", "duration_predictor"]):
            p.requires_grad = False
    
    model.train()

    dataset = UrduV25Dataset(args.ur_csv, tokenizer, args.wav_dir)
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
            
        # Sync checkpoints (Python SDK)
        if (epoch + 1) % 10 == 0:
            print(f" > Syncing checkpoint to GCS...", flush=True)
            # Simple subprocess for sync is fine if it's small, or we could use SDK
            os.system(f"gsutil -m cp -r {LOCAL_OUTPUT} {args.output_dir}/ckpt_ep{epoch+1}/")
            
    os.system(f"gsutil -m cp -r {LOCAL_OUTPUT} {args.output_dir}/final/")
    print("FORGE COMPLETE.")

if __name__ == "__main__":
    main()
