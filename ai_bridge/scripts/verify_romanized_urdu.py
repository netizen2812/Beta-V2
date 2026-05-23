import os
import torch
import scipy.io.wavfile as wavfile
import numpy as np
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts

SAMPLE_RATE = 24000
MODEL_DIR = "models/base_xtts"
SHARP_UR_WEIGHTS = "C:/Maulana_Training_Forge/deep_pillars/ur/model_real_sharp.pth"

def verify_romanized_urdu():
    print("--- VERIFYING ROMANIZED URDU (XTTSv2 FAST-TRACK) ---")
    OUTPUT_DIR = "data/verification_sharp_urdu"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. Load Sharp XTTSv2 Weights
    config = XttsConfig()
    config.load_json(os.path.join(MODEL_DIR, "config.json"))
    model = Xtts.init_from_config(config)
    model.load_checkpoint(config, checkpoint_dir=MODEL_DIR, use_deepspeed=False)
    
    print(" > Injecting High-Fidelity Sharp weights...")
    model.load_state_dict(torch.load(SHARP_UR_WEIGHTS, map_location="cuda"), strict=False)
    model.cuda()
    model.eval()

    ur_ref = "data/tts_dataset/wavs_ur/ur_0001.wav"
    gpt, spk = model.get_conditioning_latents(audio_path=[ur_ref])
    
    # Text: Romanized Urdu. We use 'en' to leverage the English phonemizer for crystal clear pronunciation.
    romanized_text = "Allah ke naam se shuru jo bada meherbaan nihayat reham wala hai. Kya ab Maulana ki aawaz bilkul saaf aur shafaf hai?"
    
    print(" > Synthesizing Romanized Urdu via English Phonemizer...")
    with torch.no_grad():
        out = model.inference(
            romanized_text, "en", gpt, spk, 
            temperature=0.65,
            repetition_penalty=5.0,
            length_penalty=1.0
        )
    
    wav = out["wav"].cpu().numpy() if hasattr(out["wav"], "cpu") else out["wav"]
    wav = wav / np.abs(wav).max() * 0.9
    
    out_file = os.path.join(OUTPUT_DIR, "maulana_ur_romanized_test.wav")
    wavfile.write(out_file, 24000, wav)
    print(f"   -> READY: {out_file}")

if __name__ == "__main__":
    try:
        verify_romanized_urdu()
    except Exception as e:
        print(f"ERROR: {e}")
