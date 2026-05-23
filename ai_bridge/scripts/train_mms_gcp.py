"""
GCP CLOUD FORGE v2: Native Urdu MMS-VITS Fine-Tuning
=====================================================
KEY FIX: Uses Mel-Spectrogram L1 loss instead of raw waveform MSE.
Raw MSE on waveforms produces white noise because phase misalignment
makes any non-silent output look "maximally wrong" to the optimizer.
Mel-Spectrogram loss is perceptually aligned and trains the voice correctly.

Hardware Target: Vertex AI T4 GPU (16GB VRAM)
"""

import os
import gc
import argparse
import torch
import torchaudio
import pandas as pd
from torch.utils.data import Dataset, DataLoader
from transformers import VitsModel, VitsTokenizer
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR

# ── ARGS ─────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--ur_csv",     default="gs://maulana-urdu-forge-project-ffb3710a/ur_aligned.csv")
parser.add_argument("--wav_dir",    default="gs://maulana-urdu-forge-project-ffb3710a/wavs")
parser.add_argument("--output_dir", default="gs://maulana-urdu-forge-project-ffb3710a/ur_mms_v2")
parser.add_argument("--epochs",     type=int, default=200)
parser.add_argument("--batch_size", type=int, default=8)
parser.add_argument("--lr",         type=float, default=2e-5)
args = parser.parse_args()

MMS_BASE = "facebook/mms-tts-urd-script_arabic"
MMS_SR   = 16000
LOCAL_WAV_DIR = "/tmp/urdu_wavs"
LOCAL_OUTPUT  = "/tmp/ur_mms_v2"

# ── MEL-SPECTROGRAM LOSS (THE CORE FIX) ──────────────────────────────────────
mel_transform = torchaudio.transforms.MelSpectrogram(
    sample_rate=MMS_SR,
    n_fft=1024,
    hop_length=256,
    n_mels=80,
    f_min=0.0,
    f_max=8000.0,
).cuda()

def mel_loss(gen_wav, real_wav):
    """
    Compute L1 loss on Mel-Spectrograms.
    This is perceptually meaningful — unlike raw MSE, it doesn't
    penalize phase misalignment, so the model learns actual voice
    characteristics instead of collapsing to silence/noise.
    """
    min_len = min(gen_wav.shape[-1], real_wav.shape[-1])
    gen_mel  = mel_transform(gen_wav[..., :min_len])
    real_mel = mel_transform(real_wav[..., :min_len])
    # Log-mel for better dynamic range
    gen_mel  = torch.log(gen_mel.clamp(min=1e-5))
    real_mel = torch.log(real_mel.clamp(min=1e-5))
    return torch.nn.functional.l1_loss(gen_mel, real_mel)

# ── DATASET ───────────────────────────────────────────────────────────────────
class UrduGCSDataset(Dataset):
    def __init__(self, csv_path, tokenizer, local_wav_dir):
        # Download CSV from GCS
        local_csv = "/tmp/ur_aligned.csv"
        os.system(f"gsutil cp {csv_path} {local_csv}")
        self.df = pd.read_csv(local_csv)
        self.tokenizer = tokenizer
        self.local_wav_dir = local_wav_dir
        print(f" > Loaded {len(self.df)} aligned Urdu pairs.")

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        try:
            # Handle Windows paths originating from the local CSV on a Linux container
            wav_filename = str(row["audio_path"]).replace("\\", "/").split("/")[-1]
            local_wav = os.path.join(self.local_wav_dir, wav_filename)

            wav, sr = torchaudio.load(local_wav)
            if sr != MMS_SR:
                wav = torchaudio.functional.resample(wav, sr, MMS_SR)
            wav = wav.mean(0)

            # Clip to max 8 seconds
            max_samples = MMS_SR * 8
            if wav.shape[0] > max_samples:
                wav = wav[:max_samples]

            text = str(row["text"])[:200]  # Cap text length
            inputs = self.tokenizer(text=text, return_tensors="pt", padding=True)
            return {
                "input_ids":      inputs["input_ids"].squeeze(0),
                "attention_mask": inputs["attention_mask"].squeeze(0),
                "wav":            wav,
            }
        except Exception as e:
            print(f" ! Skipping idx {idx}: {e}")
            return self.__getitem__((idx + 1) % len(self.df))


def collate_fn(batch):
    max_text = max(b["input_ids"].shape[0] for b in batch)
    max_wav  = max(b["wav"].shape[0] for b in batch)
    B = len(batch)
    input_ids  = torch.zeros(B, max_text, dtype=torch.long)
    attn_mask  = torch.zeros(B, max_text, dtype=torch.long)
    wavs       = torch.zeros(B, max_wav)
    for i, b in enumerate(batch):
        tl = b["input_ids"].shape[0]
        wl = b["wav"].shape[0]
        input_ids[i, :tl] = b["input_ids"]
        attn_mask[i, :tl] = b["attention_mask"]
        wavs[i, :wl]      = b["wav"]
    return {"input_ids": input_ids, "attention_mask": attn_mask, "wav": wavs}


# ── MAIN FORGE ────────────────────────────────────────────────────────────────
def cloud_forge():
    print("=" * 60)
    print("MAULANA URDU FORGE v2 [GCP / T4 GPU]")
    print("Loss: Log-Mel Spectrogram L1")
    print("=" * 60)

    # 1. Pre-download all WAVs at job start (much faster than per-sample gsutil)
    os.makedirs(LOCAL_WAV_DIR, exist_ok=True)
    os.makedirs(LOCAL_OUTPUT,  exist_ok=True)
    print(f" > Pre-downloading all WAVs from {args.wav_dir}...")
    os.system(f"gsutil -m cp -r '{args.wav_dir}/*' {LOCAL_WAV_DIR}/")
    print(f" > WAVs ready in {LOCAL_WAV_DIR}")

    # 2. Load model
    print(f" > Loading MMS base: {MMS_BASE}")
    tokenizer = VitsTokenizer.from_pretrained(MMS_BASE)
    model     = VitsModel.from_pretrained(MMS_BASE).cuda()
    model.gradient_checkpointing_enable()
    model.train()

    # 3. Dataset
    dataset    = UrduGCSDataset(args.ur_csv, tokenizer, LOCAL_WAV_DIR)
    dataloader = DataLoader(dataset, batch_size=args.batch_size,
                            shuffle=True, collate_fn=collate_fn,
                            num_workers=0, pin_memory=True)

    # 4. Optimizer + LR Scheduler
    optimizer = AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = CosineAnnealingLR(optimizer, T_max=args.epochs * len(dataloader))

    best_loss   = float("inf")
    global_step = 0

    for epoch in range(args.epochs):
        epoch_loss = 0.0
        for i, batch in enumerate(dataloader):
            optimizer.zero_grad()
            gc.collect()
            torch.cuda.empty_cache()

            ids  = batch["input_ids"].cuda()
            att  = batch["attention_mask"].cuda()
            real = batch["wav"].cuda()

            # Forward pass
            outputs = model(input_ids=ids, attention_mask=att)
            gen     = outputs.waveform  # [B, T_gen]

            # --- MEL-SPECTROGRAM LOSS (not raw MSE) ---
            loss = mel_loss(gen, real)

            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()

            epoch_loss  += loss.item()
            global_step += 1

            if global_step % 25 == 0:
                avg = epoch_loss / (i + 1)
                print(f" > Epoch {epoch+1}/{args.epochs} | Step {global_step} | Loss: {avg:.6f}")

        avg_epoch = epoch_loss / len(dataloader)
        print(f" > Epoch {epoch+1} COMPLETE | Avg Loss: {avg_epoch:.6f}")

        # Save best model + upload to GCS every epoch
        if avg_epoch < best_loss:
            best_loss = avg_epoch
            model.save_pretrained(LOCAL_OUTPUT)
            tokenizer.save_pretrained(LOCAL_OUTPUT)
            print(f"   -> BEST MODEL SAVED (Loss: {best_loss:.6f})")

        # Always sync to GCS every 10 epochs
        if (epoch + 1) % 10 == 0:
            print(f"   -> Syncing to GCS: {args.output_dir}")
            os.system(f"gsutil -m cp -r {LOCAL_OUTPUT}/* {args.output_dir}/checkpoint_epoch_{epoch+1}/")

    # Final upload
    print(" > Final upload to GCS...")
    os.system(f"gsutil -m cp -r {LOCAL_OUTPUT}/* {args.output_dir}/final/")
    print("=" * 60)
    print(f"FORGE COMPLETE. Best Loss: {best_loss:.6f}")
    print(f"Weights: {args.output_dir}/final/")
    print("=" * 60)


if __name__ == "__main__":
    cloud_forge()
