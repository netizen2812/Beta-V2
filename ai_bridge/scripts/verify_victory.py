import os
import torch
import scipy.io.wavfile as wavfile
import numpy as np
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts
from transformers import VitsModel, VitsTokenizer

SAMPLE_RATE = 24000
MMS_SAMPLE_RATE = 16000
MODEL_DIR = "models/base_xtts"
HERITAGE_MODEL = "C:/Maulana_Training_Forge/stable_weights/best_model.pth"
UR_MMS_MODEL = "C:/Maulana_Training_Forge/mms_urdu_stable"

def load_wav(path):
    rate, data = wavfile.read(path)
    if data.dtype == np.int16:
        data = data.astype(np.float32) / 32768.0
    return rate, data

def load_heritage_xtts():
    config = XttsConfig()
    config.load_json(os.path.join(MODEL_DIR, "config.json"))
    model = Xtts.init_from_config(config)
    model.load_checkpoint(config, checkpoint_dir=MODEL_DIR, use_deepspeed=False)
    model.load_state_dict(torch.load(HERITAGE_MODEL, map_location="cuda"), strict=False)
    model.cuda()
    return model

def generate_hybrid_victory_set():
    print("--- GENERATING FINAL HYBRID VICTORY SET ---")
    OUTPUT_DIR = "data/verification_victory"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. Load Heritage XTTS (for EN and AR)
    print(" > Loading Heritage XTTS Tower (EN/AR)...")
    xtts_model = load_heritage_xtts()
    
    # 2. Load Meta MMS (for UR)
    print(" > Loading Meta MMS Native Tower (UR)...")
    ur_tokenizer = VitsTokenizer.from_pretrained(UR_MMS_MODEL)
    ur_model = VitsModel.from_pretrained(UR_MMS_MODEL)
    ur_model.cuda()

    test_cases = [
        {"lang": "en", "text": "Assalamu Alaikum. This is the Maulana English voice, on its Heritage Tower.", "ref": "data/tts_dataset/wavs/en_0001.wav", "engine": "xtts"},
        {"lang": "ar", "text": "بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ. اِقْـرَأْ بِـاِسْمِ رَبِّـكَ الَّـذِي خَـلَـقَ.", "ref": "data/tts_dataset/wavs/ar_0010.wav", "engine": "xtts"},
        {"lang": "ur", "text": "اسلام علیکم۔ مولانا کی اردو آواز اب اپنے اصلی لہجے میں تیار ہے۔", "ref": "data/tts_dataset/wavs/ur_0001.wav", "engine": "mms"}
    ]

    for case in test_cases:
        out_file = os.path.join(OUTPUT_DIR, f"maulana_victory_{case['lang']}.wav")
        print(f" > Generating {case['lang'].upper()} ({case['engine'].upper()} Tower)...")
        
        if case["engine"] == "xtts":
            gpt, spk = xtts_model.get_conditioning_latents(audio_path=[case["ref"]])
            out = xtts_model.inference(case["text"], case["lang"], gpt, spk, temperature=0.6, repetition_penalty=10.0)
            wav = out["wav"].cpu().numpy() if hasattr(out["wav"], "cpu") else out["wav"]
            rate = 24000
        else:
            inputs = ur_tokenizer(text=case["text"], return_tensors="pt").to("cuda")
            with torch.no_grad():
                output = ur_model(**inputs).waveform
            wav = output[0].cpu().numpy()
            rate = 16000

        wav = wav / np.abs(wav).max() * 0.9
        wavfile.write(out_file, rate, wav)
        print(f"   -> READY: {out_file}")

    print("\n--- HYBRID VICTORY SET COMPLETE ---")

if __name__ == "__main__":
    try:
        generate_hybrid_victory_set()
    except Exception as e:
        print(f"ERROR: {e}")
