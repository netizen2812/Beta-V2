import os
import torch
import scipy.io.wavfile as wavfile
import numpy as np
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts

SAMPLE_RATE = 24000
MODEL_DIR = "models/base_xtts"
REAL_AR_WEIGHTS = "C:/Maulana_Training_Forge/deep_pillars/ar/model_real.pth"

def verify_real_arabic():
    print("--- VERIFYING REAL ARABIC PILLAR (UTHMANI ALIGNMENT) ---")
    OUTPUT_DIR = "data/verification_real_al_quran"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. Load Real Weights
    config = XttsConfig()
    config.load_json(os.path.join(MODEL_DIR, "config.json"))
    model = Xtts.init_from_config(config)
    model.load_checkpoint(config, checkpoint_dir=MODEL_DIR, use_deepspeed=False)
    
    print(" > Injecting Real Uthmani weights...")
    model.load_state_dict(torch.load(REAL_AR_WEIGHTS, map_location="cuda"), strict=False)
    model.cuda()
    model.eval()

    # 2. Generate with Full Harakaat
    ar_ref = "data/tts_dataset/ar/wavs/ar_0001.wav"
    gpt, spk = model.get_conditioning_latents(audio_path=[ar_ref])
    
    # Official Uthmani Text for Surah Al-Ikhlas
    ar_text = "قُلْ هُوَ اللَّهُ أَحَدٌ، اللَّهُ الصَّمَدُ، لَمْ يَلِدْ وَلَمْ يُولَدْ، وَلَمْ يَكُن لَّهُ كُفُوًا أَحَدٌ."
    
    print(" > Synthesizing Surah Al-Ikhlas (Real Nuance)...")
    with torch.no_grad():
        out = model.inference(
            ar_text, "ar", gpt, spk, 
            temperature=0.65,
            repetition_penalty=5.0,
            length_penalty=1.2 # Slight scholarly stretch
        )
    
    wav = out["wav"].cpu().numpy() if hasattr(out["wav"], "cpu") else out["wav"]
    wav = wav / np.abs(wav).max() * 0.9
    
    out_file = os.path.join(OUTPUT_DIR, "maulana_ar_real_uthmani.wav")
    wavfile.write(out_file, 24000, wav)
    print(f"   -> READY: {out_file}")

if __name__ == "__main__":
    try:
        verify_real_arabic()
    except Exception as e:
        print(f"ERROR: {e}")
