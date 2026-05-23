import os
import torch
import scipy.io.wavfile as wavfile
import numpy as np
from transformers import VitsModel, VitsTokenizer

HYBRID_DIR = "C:/Maulana_Training_Forge/deep_pillars/ur_hybrid"
OUTPUT_DIR = "data/verification_hybrid_urdu"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def verify_hybrid_urdu():
    print("--- VERIFYING HYBRID STABLE URDU ---")
    
    # 1. Load Hybrid Weights
    print(f" > Injecting Hybrid Stable weights from {HYBRID_DIR}...")
    tokenizer = VitsTokenizer.from_pretrained(HYBRID_DIR)
    model = VitsModel.from_pretrained(HYBRID_DIR)
    model.cuda()
    model.eval()

    # 2. Generate Sample
    ur_text = "اللہ کے نام سے شروع جو بڑا مہربان نہایت رحم والا ہے۔ کیا اب مولانا کی آواز بالکل صاف اور سامنے ہے؟"
    print(" > Synthesizing (Hybrid Stability)...")
    inputs = tokenizer(text=ur_text, return_tensors="pt").to("cuda")
    with torch.no_grad():
        out = model(**inputs)
    
    wav = out.waveform.cpu().numpy().squeeze()
    
    # Normalize
    wav = wav / np.abs(wav).max() * 0.9
    
    out_file = os.path.join(OUTPUT_DIR, "maulana_ur_hybrid_stable.wav")
    wavfile.write(out_file, 16000, wav)
    print(f"   -> READY: {out_file}")

if __name__ == "__main__":
    try:
        verify_hybrid_urdu()
    except Exception as e:
        print(f"ERROR: {e}")
