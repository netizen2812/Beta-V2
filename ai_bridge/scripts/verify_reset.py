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

def reset_to_simplicity():
    print("--- RESETTING TO SCHOLARLY SIMPLICITY ---")
    OUTPUT_DIR = "data/verification_reset"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. URDU RESET (Back to the Perfect Tone)
    print(" > Resetting URDU...")
    ur_model = load_deep_pillar("ur")
    ur_ref = "data/tts_dataset/wavs/ur_0001.wav"
    ur_gpt, ur_spk = ur_model.get_conditioning_latents(audio_path=[ur_ref])
    
    ur_text = "بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ. مولانا کی آواز اب اپنی اصلی اور سادہ حالت میں واپس آ گئی ہے۔"
    ur_out = ur_model.inference(
        ur_text, "hi", ur_gpt, ur_spk, 
        temperature=0.65, # Standard natural temperature
        repetition_penalty=2.0, # Standard penalty to allow natural flow
        top_k=50,
        top_p=0.85
    )
    ur_wav = ur_out["wav"].cpu().numpy() if hasattr(ur_out["wav"], "cpu") else ur_out["wav"]
    wavfile.write(os.path.join(OUTPUT_DIR, "maulana_ur_reset.wav"), 24000, ur_wav / np.abs(ur_wav).max() * 0.9)

    # 2. ARABIC RESET (Natural Nuance)
    print(" > Resetting ARABIC...")
    ar_model = load_deep_pillar("ar")
    ar_ref = "data/tts_dataset/wavs/ar_0001.wav"
    ar_gpt, ar_spk = ar_model.get_conditioning_latents(audio_path=[ar_ref])
    
    # Pure script, no tatweels
    ar_text = "بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ. اقْرَأْ بِاسْمِ رَبِّكَ الَّذِي خَلَقَ."
    ar_out = ar_model.inference(
        ar_text, "ar", ar_gpt, ar_spk, 
        temperature=0.7, # Natural scholarly temperature
        repetition_penalty=2.0,
        top_k=50,
        top_p=0.85
    )
    ar_wav = ar_out["wav"].cpu().numpy() if hasattr(ar_out["wav"], "cpu") else ar_out["wav"]
    wavfile.write(os.path.join(OUTPUT_DIR, "maulana_ar_reset.wav"), 24000, ar_wav / np.abs(ar_wav).max() * 0.9)

    print("\n--- RESET SAMPLES READY ---")

if __name__ == "__main__":
    try:
        reset_to_simplicity()
    except Exception as e:
        print(f"ERROR: {e}")
