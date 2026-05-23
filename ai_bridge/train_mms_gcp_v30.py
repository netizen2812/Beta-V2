"""
GCP CLOUD FORGE v30 — Urdu MMS-VITS "The Reconstruction"
=====================================================
FIXES:
- Replaces unaligned inference loss with VAE Reconstruction Loss.
- Uses Posterior Encoder -> Decoder path for perfectly aligned gradients.
- Freezes Text Encoder and Flow to stabilize voice adaptation.
- Proper Linear Spectrogram calculation for VITS.
"""

import os
import gc
import math
import argparse
import time
import subprocess
import zipfile
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
parser.add_argument("--output_dir", default="gs://maulana-urdu-forge-project-ffb3710a/ur_mms_v30")
parser.add_argument("--epochs",     type=int,   default=200)
parser.add_argument("--batch_size", type=int,   default=4)
parser.add_argument("--lr",         type=float, default=2e-5)
args = parser.parse_args()

MMS_BASE      = "facebook/mms-tts-urd-script_arabic"
MMS_SR        = 16000
LOCAL_WAV_DIR = "/tmp/urdu_wavs"
LOCAL_ZIP     = "/tmp/data.zip"
LOCAL_OUTPUT  = "/tmp/ur_mms_v30"

# ── AUDIO HELPERS ─────────────────────────────────────────────────────────────
def get_spectrogram(wav):
    """Calculate linear spectrogram as expected by VITS posterior encoder."""
    # wav: [batch, samples]
    # returns: [batch, 513, frames]
    window = torch.hann_window(1024).to(wav.device)
    stft = torch.stft(
        wav, n_fft=1024, hop_length=256, win_length=1024,
        window=window, center=True, return_complex=True
    )
    return torch.abs(stft)

def get_mel_spectrogram(wav):
    """For the loss function."""
    # We use a similar STFT but usually log-mel is better. 
    # For simplicity and consistency with v26's intended fix, we use log-magnitude.
    mag = get_spectrogram(wav)
    return torch.log(mag.clamp(min=1e-5))

# ── DATASET ───────────────────────────────────────────────────────────────────
class UrduV30Dataset(Dataset):
    def __init__(self, csv_path, tokenizer, active_wav_dir):
        local_csv = "/tmp/ur_aligned.csv"
        if not os.path.exists(local_csv):
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
            
            # Max 5 seconds to avoid OOM
            wav = torch.from_numpy(wav).float()[:MMS_SR * 5]
            
            return {"wav": wav}
        except Exception:
            return self.__getitem__(np.random.randint(0, len(self.df)))

def collate(batch):
    max_w = max(b["wav"].shape[0] for b in batch)
    B = len(batch)
    wavs = torch.zeros(B, max_w)
    lengths = torch.LongTensor(B)
    for i, b in enumerate(batch):
        wl = b["wav"].shape[0]
        wavs[i, :wl] = b["wav"]
        lengths[i] = wl
    return {"wav": wavs, "lengths": lengths}

# ── SYNC ──────────────────────────────────────────────────────────────────────
def sync_dataset_zip():
    if not os.path.exists(LOCAL_ZIP):
        print(f" > Downloading {args.zip_path}...", flush=True)
        subprocess.run(["gcloud", "storage", "cp", args.zip_path, LOCAL_ZIP], check=True)
    
    if not os.path.exists(LOCAL_WAV_DIR) or len(os.listdir(LOCAL_WAV_DIR)) < 10:
        print(f" > Extracting to {LOCAL_WAV_DIR}...", flush=True)
        os.makedirs(LOCAL_WAV_DIR, exist_ok=True)
        with zipfile.ZipFile(LOCAL_ZIP, 'r') as zip_ref:
            zip_ref.extractall(LOCAL_WAV_DIR)
            
    for root, dirs, files in os.walk(LOCAL_WAV_DIR):
        wavs = [f for f in files if f.endswith(".wav")]
        if len(wavs) > 10: return root
    return LOCAL_WAV_DIR

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60, flush=True)
    print("MAULANA URDU FORGE v30 [VAE RECONSTRUCTION]", flush=True)
    print("=" * 60, flush=True)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    os.makedirs(LOCAL_OUTPUT, exist_ok=True)

    tokenizer = VitsTokenizer.from_pretrained(MMS_BASE)
    model = VitsModel.from_pretrained(MMS_BASE).to(device)
    
    # FREEZE EVERYTHING except Decoder and Posterior Encoder
    # This forces the model to learn the NEW VOICE using the EXISTING ALIGNMENT logic.
    for n, p in model.named_parameters():
        if not any(k in n for k in ["decoder", "posterior_encoder"]):
            p.requires_grad = False
    
    print(f" > Trainable Params: {sum(p.numel() for p in model.parameters() if p.requires_grad):,}")
    model.train()

    active_wav_dir = sync_dataset_zip()
    dataset = UrduV30Dataset(args.ur_csv, tokenizer, active_wav_dir)
    dataloader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True, collate_fn=collate, num_workers=0)
    
    optimizer = AdamW([p for p in model.parameters() if p.requires_grad], lr=args.lr)
    scheduler = CosineAnnealingLR(optimizer, T_max=args.epochs * len(dataloader))
    scaler = GradScaler(enabled=(device == "cuda"))

    start_time = time.time()
    step = 0

    for epoch in range(args.epochs):
        ep_loss, ep_batches = 0.0, 0
        for i, batch in enumerate(dataloader):
            optimizer.zero_grad()
            real_wav = batch["wav"].to(device) # [B, T]
            
            with autocast(enabled=(device == "cuda")):
                # 1. Get Linear Spectrogram
                spec = get_spectrogram(real_wav) # [B, 513, frames]
                spec_lengths = torch.LongTensor([spec.shape[-1]] * spec.shape[0]).to(device)
                
                # 2. VAE Path: Posterior Encoder -> Decoder
                # Accessing internal modules directly because forward() doesn't support training
                z, m_q, logs_q, y_mask = model.posterior_encoder(spec, spec_lengths)
                
                # MMS-VITS is single speaker, so g=None
                # Decoder output is [B, 1, T]
                wav_hat = model.decoder(z * y_mask, g=None) 
                
                # 3. Reconstruction Loss (Mel-space)
                # Comparing perfectly aligned signals!
                gen_mel = get_mel_spectrogram(wav_hat.squeeze(1))
                real_mel = get_mel_spectrogram(real_wav)
                
                min_len = min(gen_mel.shape[-1], real_mel.shape[-1])
                loss = torch.nn.functional.l1_loss(gen_mel[..., :min_len], real_mel[..., :min_len])
                
                # Optional: KL divergence to keep latents near prior (MMS default)
                # We skip for pure voice adaptation stability, or keep it tiny.
                # loss += 0.01 * kl_loss

            if not math.isfinite(loss.item()): continue

            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            scaler.step(optimizer)
            scaler.update()
            scheduler.step()

            ep_loss, ep_batches, step = ep_loss + loss.item(), ep_batches + 1, step + 1
            if step % 25 == 0:
                print(f" > Ep {epoch+1} | Step {step} | Loss: {ep_loss/ep_batches:.4f} | {(step*args.batch_size)/(time.time()-start_time):.1f} smp/s", flush=True)

        # Periodic Save & Sync
        if (epoch + 1) % 10 == 0:
            model.save_pretrained(LOCAL_OUTPUT)
            tokenizer.save_pretrained(LOCAL_OUTPUT)
            os.system(f"gsutil -m cp -r {LOCAL_OUTPUT} {args.output_dir}/ckpt_ep{epoch+1}/")
            print(f" > Checkpoint Ep {epoch+1} synced to GCS.", flush=True)

    model.save_pretrained(LOCAL_OUTPUT)
    tokenizer.save_pretrained(LOCAL_OUTPUT)
    os.system(f"gsutil -m cp -r {LOCAL_OUTPUT} {args.output_dir}/final/")
    print("FORGE COMPLETE.")

if __name__ == "__main__":
    main()
