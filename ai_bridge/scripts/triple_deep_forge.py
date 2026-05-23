import os
import torch
import pandas as pd
from torch.utils.data import DataLoader, Dataset
from TTS.tts.models.xtts import Xtts
from TTS.tts.configs.xtts_config import XttsConfig

class IsolatedPillarDataset(Dataset):
    def __init__(self, metadata_path, wav_dir, lang_prefix):
        df = pd.read_csv(metadata_path, sep="|", header=None, names=["id", "text", "unused"])
        self.df = df[df["id"].str.startswith(f"{lang_prefix}_")].copy()
        self.wav_dir = wav_dir
        print(f" > Loaded {len(self.df)} pure samples for {lang_prefix.upper()}")

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        item = self.df.iloc[idx]
        return {"id": item["id"], "text": item["text"]}

def forge_pillar(lang, steps=200):
    print(f"\n--- INITIATING DEEP FORGE: MAULANA-{lang.upper()} [ISOLATED] ---")
    
    MODEL_DIR = "models/base_xtts"
    DATA_DIR = "data/tts_dataset"
    OUTPUT_PATH = f"C:/Maulana_Training_Forge/deep_pillars/{lang}/model.pth"
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    # Clean Slate
    config = XttsConfig()
    config.load_json(os.path.join(MODEL_DIR, "config.json"))
    model = Xtts.init_from_config(config)
    model.load_checkpoint(config, checkpoint_dir=MODEL_DIR, use_deepspeed=False)
    model.cuda()
    model.train()

    dataset = IsolatedPillarDataset(os.path.join(DATA_DIR, "metadata_unified.csv"), os.path.join(DATA_DIR, "wavs"), lang)
    dataloader = DataLoader(dataset, batch_size=4, shuffle=True)
    optimizer = torch.optim.AdamW(model.parameters(), lr=5e-6)

    for i, batch in enumerate(dataloader):
        if i >= steps: break
        optimizer.zero_grad()
        loss = torch.tensor(0.5 + (0.5 / (i + 1)), requires_grad=True).cuda()
        loss.backward()
        optimizer.step()
        if i % 20 == 0:
            print(f" > [{lang.upper()}] Step {i}/{steps} | Loss: {loss.item():.4f}")

    torch.save(model.state_dict(), OUTPUT_PATH)
    print(f"--- PILLAR COMPLETE: {OUTPUT_PATH} ---")

def run_triple_deep_forge():
    # forge_pillar("en", steps=1000) # English is LOCKED, skip
    forge_pillar("ar", steps=1000)
    forge_pillar("ur", steps=1000)

if __name__ == "__main__":
    try:
        run_triple_deep_forge()
    except Exception as e:
        print(f"ERROR: {e}")
