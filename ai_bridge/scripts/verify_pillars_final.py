import os
import torch
import scipy.io.wavfile as wavfile
import numpy as np
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts
from transformers import VitsModel, VitsTokenizer
import scipy.signal as signal

SAMPLE_RATE = 24000
MMS_SAMPLE_RATE = 16000
MODEL_DIR = "models/base_xtts"
EN_PILLAR_PATH = "C:/Maulana_Training_Forge/pillars/en/model.pth"
AR_PILLAR_PATH = "C:/Maulana_Training_Forge/pillars/ar/model.pth"
UR_PILLAR_PATH = "C:/Maulana_Training_Forge/mms_urdu_stable"

def load_xtts_pillar(path):
    config = XttsConfig()
    config.load_json(os.path.join(MODEL_DIR, "config.json"))
    model = Xtts.init_from_config(config)
    # Prime with base checkpoint first to ensure structure is initialized
    model.load_checkpoint(config, checkpoint_dir=MODEL_DIR, use_deepspeed=False)
    # Then swap in fine-tuned weights
    model.load_state_dict(torch.load(path, map_location="cuda"), strict=False)
    
    model.cuda()
    return model, config

def generate_pillar_samples():
    print("--- GENERATING DEFINITIVE PILLAR SAMPLES ---")
    OUTPUT_DIR = "data/verification_pillars"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. EN PILLAR (English + Eng/Ar Hybrid)
    print(" > Loading Maulana-English Pillar...")
    en_model, en_config = load_xtts_pillar(EN_PILLAR_PATH)
    en_ref = "data/tts_dataset/wavs/en_0001.wav"
    en_gpt, en_spk = en_model.get_conditioning_latents(audio_path=[en_ref])

    # 2. AR PILLAR
    print(" > Loading Maulana-Arabic Pillar...")
    ar_model, ar_config = load_xtts_pillar(AR_PILLAR_PATH)
    ar_ref = "data/tts_dataset/wavs/ar_0001.wav"
    ar_gpt, ar_spk = ar_model.get_conditioning_latents(audio_path=[ar_ref])

    # 3. UR PILLAR
    print(" > Loading Maulana-Urdu Pillar (MMS)...")
    ur_tokenizer = VitsTokenizer.from_pretrained(UR_PILLAR_PATH)
    ur_model = VitsModel.from_pretrained(UR_PILLAR_PATH)
    ur_model.cuda()

    test_cases = [
        {"id": "en_pure", "model": "en", "text": "Assalamu Alaikum. This is the Maulana English voice, fully consistent and authoritative."},
        {"id": "ur_pure", "model": "ur", "text": "اسلام علیکم۔ یہ مولانا کی خالص اردو آواز ہے۔ علم حاصل کرنا ہر مسلمان پر فرض ہے۔"},
        {"id": "ar_pure", "model": "ar", "text": "السلام عليكم. هذا هو صوت مولانا العربي الأصيل. اقرأ باسم ربك الذي خلق."},
        {"id": "en_ar_monotonous", "model": "en", "text": "The Prophet said: طَلَبُ الْعِلْمِ فَرِيضَةٌ which means seeking knowledge is obligatory."},
        {"id": "ur_ar_monotonous", "model": "ur", "text": "رسول اللہ نے فرمایا: طَلَبُ الْعِلْمِ فَرِيضَةٌ جس کا مطلب ہے کہ علم حاصل کرنا فرض ہے۔"}
    ]

    for case in test_cases:
        out_file = os.path.join(OUTPUT_DIR, f"maulana_{case['id']}.wav")
        print(f" > Generating {case['id']}...")
        
        if case["model"] == "en":
            out = en_model.inference(case["text"], "en", en_gpt, en_spk, temperature=0.6, repetition_penalty=10.0)
            wav = out["wav"]
            if hasattr(wav, "cpu"): wav = wav.cpu().numpy()
            wavfile.write(out_file, 24000, wav)
            
        elif case["model"] == "ar":
            out = ar_model.inference(case["text"], "ar", ar_gpt, ar_spk, temperature=0.7)
            wav = out["wav"]
            if hasattr(wav, "cpu"): wav = wav.cpu().numpy()
            wavfile.write(out_file, 24000, wav)
            
        elif case["model"] == "ur":
            inputs = ur_tokenizer(text=case["text"], return_tensors="pt").to("cuda")
            with torch.no_grad():
                output = ur_model(**inputs).waveform
            wav = output[0].cpu().numpy()
            # No resampling for pure speed in verification
            wavfile.write(out_file, 16000, wav)

    print("\n--- PILLAR SAMPLES READY ---")

if __name__ == "__main__":
    try:
        generate_pillar_samples()
    except Exception as e:
        print(f"ERROR: {e}")
