import os
import torch
import scipy.io.wavfile as wavfile
import numpy as np
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts

SAMPLE_RATE = 24000
MODEL_DIR = "models/base_xtts"
EN_PILLAR_PATH = "C:/Maulana_Training_Forge/pillars/en/model.pth"
AR_PILLAR_PATH = "C:/Maulana_Training_Forge/pillars/ar/model.pth"

def load_xtts_pillar(path):
    config = XttsConfig()
    config.load_json(os.path.join(MODEL_DIR, "config.json"))
    model = Xtts.init_from_config(config)
    model.load_checkpoint(config, checkpoint_dir=MODEL_DIR, use_deepspeed=False)
    model.load_state_dict(torch.load(path, map_location="cuda"), strict=False)
    model.cuda()
    return model, config

def generate_hand_in_hand_samples():
    print("--- GENERATING HAND-IN-HAND CALIBRATED SAMPLES ---")
    OUTPUT_DIR = "data/verification_calibrated"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Load English and Arabic pillars (Arabic will also handle Urdu for resonance)
    en_model, _ = load_xtts_pillar(EN_PILLAR_PATH)
    ar_model, _ = load_xtts_pillar(AR_PILLAR_PATH)
    
    # Anchors
    en_ref = "data/tts_dataset/wavs/en_0001.wav"
    ar_ref = "data/tts_dataset/wavs/ar_0001.wav"
    ur_ref = "data/tts_dataset/wavs/ur_0001.wav" # Using the native Urdu anchor for identity
    
    en_gpt, en_spk = en_model.get_conditioning_latents(audio_path=[en_ref])
    ar_gpt, ar_spk = ar_model.get_conditioning_latents(audio_path=[ar_ref])
    ur_gpt, ur_spk = ar_model.get_conditioning_latents(audio_path=[ur_ref]) # Use AR model for UR for better resonance

    test_cases = [
        {
            "id": "ur_calibrated",
            "model": ar_model,
            "gpt": ur_gpt,
            "spk": ur_spk,
            "lang": "hi", # Using the hi pathway for resonance but with UR anchor
            "text": "اسلام علیکم۔ مولانا کی آواز اب بالکل اصلی محسوس ہونی چاہیے۔ علم کی شمع روشن رہے گی۔",
            "temp": 0.55
        },
        {
            "id": "ar_calibrated",
            "model": ar_model,
            "gpt": ar_gpt,
            "spk": ar_spk,
            "lang": "ar",
            "text": "بِسْـمِ اللَّـهِ الرَّحْمَـنِ الرَّحِيـمِ. اِقْـرَأْ بِـاِسْمِ رَبِّـكَ الَّـذِي خَـلَـقَ.", # Using Tatweel for stretching
            "temp": 0.75 # Higher temperature for more "emotion/stretch"
        }
    ]

    for case in test_cases:
        out_file = os.path.join(OUTPUT_DIR, f"maulana_{case['id']}.wav")
        print(f" > Generating {case['id']} with Prosody Guidance...")
        
        out = case["model"].inference(
            case["text"], 
            case["lang"], 
            case["gpt"], 
            case["spk"], 
            temperature=case["temp"],
            length_penalty=1.2, # Stretching the words slightly
            repetition_penalty=10.0,
            top_k=50,
            top_p=0.8
        )
        
        wav = out["wav"].cpu().numpy() if hasattr(out["wav"], "cpu") else out["wav"]
        wav = wav / np.abs(wav).max() * 0.9
        wavfile.write(out_file, 24000, wav)
        print(f"   -> READY: {out_file}")

    print("\n--- CALIBRATED SAMPLES READY ---")

if __name__ == "__main__":
    try:
        generate_hand_in_hand_samples()
    except Exception as e:
        print(f"ERROR: {e}")
