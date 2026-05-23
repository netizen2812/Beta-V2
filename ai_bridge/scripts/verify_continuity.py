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

def generate_continuity_test():
    print("--- GENERATING SCHOLARLY CONTINUITY TEST ---")
    OUTPUT_DIR = "data/verification_continuity"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. Load Pillars
    en_model, _ = load_xtts_pillar(EN_PILLAR_PATH)
    ar_model, _ = load_xtts_pillar(AR_PILLAR_PATH)
    
    en_ref = "data/tts_dataset/wavs/en_0001.wav"
    ar_ref = "data/tts_dataset/wavs/ar_0001.wav"
    
    en_gpt, en_spk = en_model.get_conditioning_latents(audio_path=[en_ref])
    ar_gpt, ar_spk = ar_model.get_conditioning_latents(audio_path=[ar_ref])

    # 2. Test Cases: Maulana Intro -> Golden Sample Citation
    # Note: We simulate the transition by generating the Maulana intro and 
    # then appending a segment that sounds like the Golden Sample (same voice).
    
    cases = [
        {
            "id": "en_continuity",
            "model": en_model,
            "gpt": en_gpt,
            "spk": en_spk,
            "lang": "en",
            "preface": "In the name of Allah, the Most Gracious, the Most Merciful. The Almighty says in the Quran:",
            "verse": "Read! In the name of your Lord who created."
        },
        {
            "id": "ar_continuity",
            "model": ar_model,
            "gpt": ar_gpt,
            "spk": ar_spk,
            "lang": "ar",
            "preface": "بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ. يَقُولُ اللَّهُ تَعَالَى فِي الْقُرْآنِ الْكَرِيمِ:",
            "verse": "اقْرَأْ بِاسْمِ رَبِّكَ الَّذِي خَلَقَ."
        }
    ]

    for case in cases:
        out_file = os.path.join(OUTPUT_DIR, f"maulana_{case['id']}.wav")
        print(f" > Generating {case['id']}...")
        
        # Preface (Normal speech tone)
        out_preface = case["model"].inference(case["preface"], case["lang"], case["gpt"], case["spk"], temperature=0.6)
        wav_preface = out_preface["wav"].cpu().numpy() if hasattr(out_preface["wav"], "cpu") else out_preface["wav"]
        
        # Verse (Mimicking the recitation tone of the Golden Sample)
        out_verse = case["model"].inference(case["verse"], case["lang"], case["gpt"], case["spk"], temperature=0.75)
        wav_verse = out_verse["wav"].cpu().numpy() if hasattr(out_verse["wav"], "cpu") else out_verse["wav"]
        
        # Normalize and Stitch
        wav_preface = wav_preface / np.abs(wav_preface).max() * 0.9
        wav_verse = wav_verse / np.abs(wav_verse).max() * 0.9
        pause = np.zeros(int(SAMPLE_RATE * 0.2), dtype=np.float32) # 200ms scholarly pause
        
        full_wav = np.concatenate([wav_preface, pause, wav_verse])
        wavfile.write(out_file, 24000, full_wav)
        print(f"   -> READY: {out_file}")

    print("\n--- CONTINUITY TEST COMPLETE ---")

if __name__ == "__main__":
    try:
        generate_continuity_test()
    except Exception as e:
        print(f"ERROR: {e}")
