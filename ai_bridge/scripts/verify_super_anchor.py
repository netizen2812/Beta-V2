import os
import torch
import scipy.io.wavfile as wavfile
import numpy as np
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts

SAMPLE_RATE = 24000
MODEL_DIR = "models/base_xtts"

def load_deep_pillar(lang):
    path = f"C:/Maulana_Training_Forge/deep_pillars/{lang}/model.pth"
    config = XttsConfig()
    config.load_json(os.path.join(MODEL_DIR, "config.json"))
    model = Xtts.init_from_config(config)
    model.load_checkpoint(config, checkpoint_dir=MODEL_DIR, use_deepspeed=False)
    model.load_state_dict(torch.load(path, map_location="cuda"), strict=False)
    model.cuda()
    return model

def super_anchor_calibration():
    print("--- INITIATING SUPER-ANCHOR CALIBRATION ---")
    OUTPUT_DIR = "data/verification_super_anchor"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. URDU SUPER-ANCHOR (5 Stable Samples)
    print(" > Forging URDU Super-Anchor...")
    ur_model = load_deep_pillar("ur")
    ur_refs = [f"data/tts_dataset/wavs/ur_{i:04d}.wav" for i in range(1, 6)]
    ur_gpt, ur_spk = ur_model.get_conditioning_latents(audio_path=ur_refs)
    
    ur_text = "بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ. مولانا کی آواز اب بالکل صاف اور شفاف ہونی چاہیے۔"
    ur_out = ur_model.inference(
        ur_text, "hi", ur_gpt, ur_spk, 
        temperature=0.5, # Ultra-stable
        repetition_penalty=15.0, # Maximum mumble suppression
        top_k=100, # Wider safe-token search
        top_p=0.8
    )
    ur_wav = ur_out["wav"].cpu().numpy() if hasattr(ur_out["wav"], "cpu") else ur_out["wav"]
    wavfile.write(os.path.join(OUTPUT_DIR, "maulana_ur_super_anchor.wav"), 24000, ur_wav / np.abs(ur_wav).max() * 0.9)

    # 2. ARABIC VOCAL FLOW (Linear Expansion)
    print(" > Forging ARABIC Vocal Flow...")
    ar_model = load_deep_pillar("ar")
    ar_refs = [f"data/tts_dataset/wavs/ar_{i:04d}.wav" for i in range(1, 6)]
    ar_gpt, ar_spk = ar_model.get_conditioning_latents(audio_path=ar_refs)
    
    # Adding Tatweel and Micro-Pauses (,) for Vocal Flow
    ar_text = "بِسْـمِ اللَّـهِ، الـرَّحْمَـنِ، الـرَّحِيـمِ، اِقْـرَأْ بِـاِسْمِ رَبِّـكَ الَّـذِي خَـلَـقَ."
    ar_out = ar_model.inference(
        ar_text, "ar", ar_gpt, ar_spk, 
        temperature=0.8, # Higher for nuanced flow
        length_penalty=1.5, # Stronger vowel expansion
        top_k=50,
        top_p=0.95 # Full vocal character
    )
    ar_wav = ar_out["wav"].cpu().numpy() if hasattr(ar_out["wav"], "cpu") else ar_out["wav"]
    wavfile.write(os.path.join(OUTPUT_DIR, "maulana_ar_vocal_flow.wav"), 24000, ar_wav / np.abs(ar_wav).max() * 0.9)

    print("\n--- SUPER-ANCHOR PROOFS READY ---")

if __name__ == "__main__":
    try:
        super_anchor_calibration()
    except Exception as e:
        print(f"ERROR: {e}")
