"""
Phase 2B: Real Urdu Fine-Tuning using Meta MMS-VITS
- Uses aligned audio-transcript CSV from build_aligned_dataset.py
- Runs REAL HuggingFace VITS fine-tuning with actual audio loading
- Urdu text from AlQuran API (ur.jalandhry — scholarly translation)
- Isolated: ONLY Urdu data, zero cross-contamination
"""

import os
import torch
import pandas as pd
import torchaudio
import numpy as np
from torch.utils.data import Dataset, DataLoader
from transformers import VitsModel, VitsTokenizer
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR

UR_CSV       = "data/tts_dataset_aligned/ur_aligned.csv"
MMS_BASE     = "facebook/mms-tts-urd-script_arabic"
OUTPUT_DIR   = "C:/Maulana_Training_Forge/deep_pillars/ur_real"
EPOCHS       = 10
BATCH_SIZE   = 1  # Reduced for 4GB GPU stability
LR           = 1e-5
MMS_SR       = 16000

os.makedirs(OUTPUT_DIR, exist_ok=True)
torch.cuda.empty_cache() # Clear residual memory

class UrduTranslationDataset(Dataset):
    def __init__(self, csv_path, tokenizer):
        self.df = pd.read_csv(csv_path, encoding="utf-8-sig")
        self.tokenizer = tokenizer
        print(f" > Urdu Dataset: {len(self.df)} real audio-transcript pairs loaded.")

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        try:
            # Load and resample real audio
            wav, sr = torchaudio.load(row["audio_path"])
            if wav.shape[-1] / sr > 10.0: # Skip clips > 10 seconds for 4GB GPU
                return self.__getitem__((idx + 1) % len(self.df))
                
            if sr != MMS_SR:
                wav = torchaudio.functional.resample(wav, sr, MMS_SR)
            if wav.shape[0] > 1:
                wav = wav.mean(0, keepdim=True)
            wav = wav.squeeze(0)

            # Tokenize Urdu text
            inputs = self.tokenizer(
                text=row["text"],
                return_tensors="pt",
                padding=True
            )
            return {
                "input_ids": inputs["input_ids"].squeeze(0),
                "attention_mask": inputs["attention_mask"].squeeze(0),
                "wav": wav,
                "text": row["text"]
            }
        except:
            return self.__getitem__((idx + 1) % len(self.df))

def collate_fn(batch):
    # Pad input_ids and attention_masks
    max_len = max(b["input_ids"].shape[0] for b in batch)
    input_ids = torch.zeros(len(batch), max_len, dtype=torch.long)
    attn_masks = torch.zeros(len(batch), max_len, dtype=torch.long)
    for i, b in enumerate(batch):
        l = b["input_ids"].shape[0]
        input_ids[i, :l] = b["input_ids"]
        attn_masks[i, :l] = b["attention_mask"]
    return {
        "input_ids": input_ids,
        "attention_mask": attn_masks,
        "wav": [b["wav"] for b in batch],
        "text": [b["text"] for b in batch]
    }

def train_urdu_pillar():
    import gc
    print("=" * 60)
    print("REAL URDU MMS FINE-TUNING [ISOLATED PILLAR]")
    print("=" * 60)

    # 1. Load MMS tokenizer & model
    print(f" > Loading MMS base: {MMS_BASE}")
    tokenizer = VitsTokenizer.from_pretrained(MMS_BASE)
    model = VitsModel.from_pretrained(MMS_BASE)
    model.cuda()
    
    # Enable gradient checkpointing for memory efficiency
    model.gradient_checkpointing_enable()
    model.train()

    # 2. Load REAL dataset
    dataset = UrduTranslationDataset(UR_CSV, tokenizer)
    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True,
                            collate_fn=collate_fn, num_workers=0)

    optimizer = AdamW(model.parameters(), lr=LR)
    scheduler = CosineAnnealingLR(optimizer, T_max=EPOCHS * len(dataloader))

    best_loss = float("inf")
    global_step = 0

    for epoch in range(EPOCHS):
        epoch_loss = 0.0
        for i, batch in enumerate(dataloader):
            optimizer.zero_grad()
            gc.collect()
            torch.cuda.empty_cache()

            input_ids = batch["input_ids"].cuda()
            attn_mask = batch["attention_mask"].cuda()

            # Real forward pass — VITS generates waveform from text
            outputs = model(
                input_ids=input_ids,
                attention_mask=attn_mask
            )

            # Waveform reconstruction loss against real audio
            gen_wav = outputs.waveform  # [B, T_gen]
            real_wavs = batch["wav"]

            # Align lengths for MSE loss
            loss_total = torch.tensor(0.0, requires_grad=True).cuda()
            for j, (gen, real) in enumerate(zip(gen_wav, real_wavs)):
                real = real.cuda()
                min_len = min(gen.shape[-1], real.shape[-1])
                mse = torch.nn.functional.mse_loss(
                    gen[..., :min_len], real[..., :min_len]
                )
                loss_total = loss_total + mse

            loss = loss_total / len(real_wavs)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()

            epoch_loss += loss.item()
            global_step += 1

            if global_step % 25 == 0:
                avg = epoch_loss / (i + 1)
                print(f" > [UR] Epoch {epoch+1}/{EPOCHS} | Step {global_step} | Loss: {avg:.6f}")

        avg_epoch = epoch_loss / len(dataloader)
        print(f" > [UR] Epoch {epoch+1} COMPLETE | Avg Loss: {avg_epoch:.6f}")

        if avg_epoch < best_loss:
            best_loss = avg_epoch
            model.save_pretrained(OUTPUT_DIR)
            tokenizer.save_pretrained(OUTPUT_DIR)
            print(f"   -> BEST MODEL SAVED (Loss: {best_loss:.6f})")

    print("\n" + "=" * 60)
    print("URDU PILLAR FORGE COMPLETE")
    print(f" > Best Loss: {best_loss:.6f}")
    print(f" > Weights:   {OUTPUT_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    try:
        train_urdu_pillar()
    except Exception as e:
        import traceback
        traceback.print_exc()
