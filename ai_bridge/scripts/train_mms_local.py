
"""
LOCAL GPU FORGE: Native Urdu MMS-VITS
- Optimized for RTX 3050 (4GB VRAM)
- Uses Local Data (data/urdu_forge)
- Memory Optimization: Gradient Checkpointing + Accumulation + AMP
"""

import os
import torch
import pandas as pd
import torchaudio
from torch.utils.data import Dataset, DataLoader
from transformers import VitsModel, VitsTokenizer
from torch.optim import AdamW
import argparse

# --- CONFIG ---
DATA_DIR    = "data/urdu_forge"
CSV_PATH    = os.path.join(DATA_DIR, "ur_aligned.csv")
WAV_DIR     = os.path.join(DATA_DIR, "wavs")
OUTPUT_DIR  = "models/ur_mms_local"
MMS_BASE    = "facebook/mms-tts-urd-script_arabic"

EPOCHS       = 200
BATCH_SIZE   = 1 # Critical for 4GB VRAM
GRAD_ACC     = 8 # Effective Batch Size = 8
LR           = 2e-5
MMS_SR       = 16000

class UrduLocalDataset(Dataset):
    def __init__(self, csv_path, tokenizer):
        self.df = pd.read_csv(csv_path)
        self.tokenizer = tokenizer
        print(f" > Loaded {len(self.df)} aligned pairs for Local GPU Forge.")

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        wav_path = os.path.join(WAV_DIR, os.path.basename(row["audio_path"]))
        
        try:
            wav, sr = torchaudio.load(wav_path)
            if sr != MMS_SR:
                wav = torchaudio.functional.resample(wav, sr, MMS_SR)
            wav = wav.mean(0)
            
            # --- MEMORY FIX: Truncate to 3 seconds ---
            if wav.shape[0] > MMS_SR * 3:
                wav = wav[:MMS_SR * 3]
            
            # --- MEMORY FIX: Truncate text ---
            text = row["text"]
            if len(text) > 150:
                text = text[:150]
                
            inputs = self.tokenizer(text=text, return_tensors="pt", padding=True)
            return {"input_ids": inputs["input_ids"].squeeze(0), "attn": inputs["attention_mask"].squeeze(0), "wav": wav}
        except Exception as e:
            print(f" ! Skipping {wav_path} due to error: {e}")
            return self.__getitem__((idx + 1) % len(self.df))

def collate_fn(batch):
    max_text = max(b["input_ids"].shape[0] for b in batch)
    max_wav  = max(b["wav"].shape[0] for b in batch)
    input_ids = torch.zeros(len(batch), max_text, dtype=torch.long)
    attn_mask = torch.zeros(len(batch), max_text, dtype=torch.long)
    wavs      = torch.zeros(len(batch), max_wav)
    for i, b in enumerate(batch):
        input_ids[i, :b["input_ids"].shape[0]] = b["input_ids"]
        attn_mask[i, :b["attn"].shape[0]] = b["attn"]
        wavs[i, :b["wav"].shape[0]] = b["wav"]
    return {"input_ids": input_ids, "attn": attn_mask, "wav": wavs}

def local_forge():
    print("=== STARTING LOCAL GPU FORGE (RTX 3050) ===")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    tokenizer = VitsTokenizer.from_pretrained(MMS_BASE)
    model = VitsModel.from_pretrained(MMS_BASE).cuda()
    
    # --- MEMORY OPTIMIZATIONS ---
    model.gradient_checkpointing_enable()
    scaler = torch.amp.GradScaler('cuda') # Modern AMP
    
    for param in model.text_encoder.parameters():
        param.requires_grad = False
    for param in model.duration_predictor.parameters():
        param.requires_grad = False
    for param in model.posterior_encoder.parameters():
        param.requires_grad = False
    for param in model.flow.parameters():
        param.requires_grad = False
        
    print(" > Frozen text_encoder, duration_predictor, posterior_encoder, flow. Only training Decoder.")
    
    # --- RESUME LOGIC ---
    start_epoch = 0
    if os.path.exists(OUTPUT_DIR):
        checkpoints = [d for d in os.listdir(OUTPUT_DIR) if d.startswith("checkpoint_epoch_")]
        if checkpoints:
            latest_ckpt = max(checkpoints, key=lambda x: int(x.split("_")[-1]))
            ckpt_path = os.path.join(OUTPUT_DIR, latest_ckpt)
            print(f" -> Resuming from {ckpt_path}!")
            model = VitsModel.from_pretrained(ckpt_path).cuda()
            start_epoch = int(latest_ckpt.split("_")[-1])

    # Re-apply freezing after loading
    for param in model.text_encoder.parameters():
        param.requires_grad = False
    for param in model.duration_predictor.parameters():
        param.requires_grad = False
    for param in model.posterior_encoder.parameters():
        param.requires_grad = False
    for param in model.flow.parameters():
        param.requires_grad = False

    model.train()
    
    dataset = UrduLocalDataset(CSV_PATH, tokenizer)
    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True, collate_fn=collate_fn)
    
    optimizer = AdamW(model.parameters(), lr=LR)

    for epoch in range(start_epoch, EPOCHS):
        total_loss = 0
        for i, batch in enumerate(dataloader):
            ids = batch["input_ids"].cuda()
            att = batch["attn"].cuda()
            real = batch["wav"].cuda()
            
            with torch.amp.autocast('cuda'): # Modern AMP
                outputs = model(input_ids=ids, attention_mask=att)
                gen = outputs.waveform.squeeze(1)
                min_len = min(gen.shape[-1], real.shape[-1])
                loss = torch.nn.functional.mse_loss(gen[:, :min_len], real[:, :min_len])
                loss = loss / GRAD_ACC # Normalize for accumulation
            
            scaler.scale(loss).backward()
            
            if (i + 1) % GRAD_ACC == 0:
                scaler.step(optimizer)
                scaler.update()
                optimizer.zero_grad()
                torch.cuda.empty_cache() # Aggressive cleanup
                
            total_loss += loss.item() * GRAD_ACC
            if i % 20 == 0:
                print(f" > Epoch {epoch+1} | Step {i} | Loss: {loss.item() * GRAD_ACC:.6f}")

        print(f" -> Saving Checkpoint (Epoch {epoch+1})...")
        model.save_pretrained(os.path.join(OUTPUT_DIR, f"checkpoint_epoch_{epoch+1}"))
        tokenizer.save_pretrained(os.path.join(OUTPUT_DIR, f"checkpoint_epoch_{epoch+1}"))

if __name__ == "__main__":
    local_forge()
