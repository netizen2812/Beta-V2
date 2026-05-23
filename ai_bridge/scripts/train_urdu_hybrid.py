"""
Phase 2 (Hybrid): Real Urdu Fine-Tuning with Gradient Accumulation
- Fixes 'noise' and 'mumbling' on 4GB GPUs
- Simulates Batch Size 16 via Gradient Accumulation
- Runs Locally: No GCP Quota required.
"""

import os
import torch
import pandas as pd
import torchaudio
import gc
from torch.utils.data import Dataset, DataLoader
from transformers import VitsModel, VitsTokenizer
from torch.optim import AdamW

UR_CSV       = "data/tts_dataset_aligned/ur_aligned.csv"
MMS_BASE     = "C:/Maulana_Training_Forge/deep_pillars/ur_real"
if not os.path.exists(os.path.join(MMS_BASE, "config.json")):
    MMS_BASE = "facebook/mms-tts-urd-script_arabic"

OUTPUT_DIR   = "C:/Maulana_Training_Forge/deep_pillars/ur_hybrid"
EPOCHS       = 30
ACCUMULATION_STEPS = 16 # Simulate Batch Size 16
LR           = 1e-5
MMS_SR       = 16000

os.makedirs(OUTPUT_DIR, exist_ok=True)
torch.cuda.empty_cache()

class UrduHybridDataset(Dataset):
    def __init__(self, csv_path, tokenizer):
        self.df = pd.read_csv(csv_path, encoding="utf-8-sig")
        self.tokenizer = tokenizer
        print(f" > Hybrid Dataset: {len(self.df)} aligned pairs.")

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        try:
            wav, sr = torchaudio.load(row["audio_path"])
            if wav.shape[-1] / sr > 8.0: # Shorter clips for stability
                return self.__getitem__((idx + 1) % len(self.df))
            if sr != MMS_SR:
                wav = torchaudio.functional.resample(wav, sr, MMS_SR)
            wav = wav.mean(0)
            inputs = self.tokenizer(text=row["text"], return_tensors="pt", padding=True)
            return {"input_ids": inputs["input_ids"].squeeze(0), "attn": inputs["attention_mask"].squeeze(0), "wav": wav}
        except:
            return self.__getitem__((idx + 1) % len(self.df))

def collate_fn(batch):
    max_len = max(b["input_ids"].shape[0] for b in batch)
    input_ids = torch.zeros(len(batch), max_len, dtype=torch.long)
    attn = torch.zeros(len(batch), max_len, dtype=torch.long)
    for i, b in enumerate(batch):
        l = b["input_ids"].shape[0]
        input_ids[i, :l] = b["input_ids"]
        attn[i, :l] = b["attn"]
    return {"input_ids": input_ids, "attn": attn, "wav": [b["wav"] for b in batch]}

def train_hybrid():
    print("=== STARTING LOCAL GRADIENT ACCUMULATION FORGE ===")
    tokenizer = VitsTokenizer.from_pretrained(MMS_BASE)
    model = VitsModel.from_pretrained(MMS_BASE).cuda()
    model.gradient_checkpointing_enable()
    model.train()

    dataset = UrduHybridDataset(UR_CSV, tokenizer)
    dataloader = DataLoader(dataset, batch_size=1, shuffle=True, collate_fn=collate_fn)
    optimizer = AdamW(model.parameters(), lr=LR)

    for epoch in range(EPOCHS):
        epoch_loss = 0
        optimizer.zero_grad()
        for i, batch in enumerate(dataloader):
            gc.collect()
            torch.cuda.empty_cache()

            ids = batch["input_ids"].cuda()
            att = batch["attn"].cuda()
            real = batch["wav"][0].cuda()

            outputs = model(input_ids=ids, attention_mask=att)
            gen = outputs.waveform.squeeze()

            min_len = min(gen.shape[-1], real.shape[-1])
            loss = torch.nn.functional.mse_loss(gen[:min_len], real[:min_len])
            
            # Normalize loss for accumulation
            loss = loss / ACCUMULATION_STEPS
            loss.backward()

            if (i + 1) % ACCUMULATION_STEPS == 0:
                optimizer.step()
                optimizer.zero_grad()
                print(f" > [UR-HYBRID] Epoch {epoch+1} | Step {i} | Loss: {loss.item()*ACCUMULATION_STEPS:.6f}")

        model.save_pretrained(OUTPUT_DIR)
        tokenizer.save_pretrained(OUTPUT_DIR)

if __name__ == "__main__":
    train_hybrid()
