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

def calibrate_delivery():
    print("--- CALIBRATING URDU FLUENCY & ARABIC NUANCE ---")
    OUTPUT_DIR = "data/verification_calibrated_v2"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. URDU CALIBRATION (Anti-Mumble)
    print(" > Calibrating URDU (Fluency Patch)...")
    ur_model = load_deep_pillar("ur")
    ur_ref = "data/tts_dataset/wavs/ur_0001.wav"
    ur_gpt, ur_spk = ur_model.get_conditioning_latents(audio_path=[ur_ref])
    
    ur_text = "بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ. مولانا کی آواز اب بالکل رواں ہونی چاہیے، بغیر کسی ہچکچاہٹ کے۔"
    ur_out = ur_model.inference(
        ur_text, "hi", ur_gpt, ur_spk, 
        temperature=0.55, # Lower for maximum stability
        repetition_penalty=12.0, # Increased to stop mumbles
        length_penalty=1.0,
        top_k=50,
        top_p=0.8
    )
    ur_wav = ur_out["wav"].cpu().numpy() if hasattr(ur_out["wav"], "cpu") else ur_out["wav"]
    wavfile.write(os.path.join(OUTPUT_DIR, "maulana_ur_calibrated_final.wav"), 24000, ur_wav / np.abs(ur_wav).max() * 0.9)

    # 2. ARABIC CALIBRATION (Nuance Injection)
    print(" > Calibrating ARABIC (Nuance Injection)...")
    ar_model = load_deep_pillar("ar")
    ar_ref = "data/tts_dataset/wavs/ar_0001.wav"
    ar_gpt, ar_spk = ar_model.get_conditioning_latents(audio_path=[ar_ref])
    
    # Adding breath marks (,) and Tatweel for nuance
    ar_text = "بِسْـمِ اللَّـهِ الرَّحْمَـنِ الرَّحِيـمِ، اِقْـرَأْ بِـاِسْمِ رَبِّـكَ الَّـذِي خَـلَـقَ."
    ar_out = ar_model.inference(
        ar_text, "ar", ar_gpt, ar_spk, 
        temperature=0.75, # Slightly higher for nuance
        repetition_penalty=5.0,
        length_penalty=1.2, # Stretching vowels for scholarly nuance
        top_k=50,
        top_p=0.9 # More vocal character allowed
    )
    ar_wav = ar_out["wav"].cpu().numpy() if hasattr(ar_out["wav"], "cpu") else ar_out["wav"]
    wavfile.write(os.path.join(OUTPUT_DIR, "maulana_ar_calibrated_final.wav"), 24000, ar_wav / np.abs(ar_wav).max() * 0.9)

    print("\n--- CALIBRATION PROOFS READY ---")

if __name__ == "__main__":
    try:
        calibrate_delivery()
    except Exception as e:
        print(f"ERROR: {e}")
