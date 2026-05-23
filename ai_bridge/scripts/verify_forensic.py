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
EN_PILLAR_PATH = "C:/Maulana_Training_Forge/pillars/en/model.pth"
AR_PILLAR_PATH = "C:/Maulana_Training_Forge/pillars/ar/model.pth"
UR_PILLAR_PATH = "C:/Maulana_Training_Forge/mms_urdu_stable"

def load_wav(path):
    rate, data = wavfile.read(path)
    if data.dtype == np.int16:
        data = data.astype(np.float32) / 32768.0
    return rate, data

def load_xtts_pillar(path):
    config = XttsConfig()
    config.load_json(os.path.join(MODEL_DIR, "config.json"))
    model = Xtts.init_from_config(config)
    model.load_checkpoint(config, checkpoint_dir=MODEL_DIR, use_deepspeed=False)
    model.load_state_dict(torch.load(path, map_location="cuda"), strict=False)
    model.cuda()
    return model, config

def generate_forensic_continuity():
    print("--- GENERATING FORENSIC CONTINUITY TEST [MAULANA -> GOLDEN] ---")
    OUTPUT_DIR = "data/verification_forensic"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. Load Engines
    en_model, _ = load_xtts_pillar(EN_PILLAR_PATH)
    ar_model, _ = load_xtts_pillar(AR_PILLAR_PATH)
    ur_tokenizer = VitsTokenizer.from_pretrained(UR_PILLAR_PATH)
    ur_model = VitsModel.from_pretrained(UR_PILLAR_PATH)
    ur_model.cuda()
    
    en_ref = "data/tts_dataset/wavs/en_0001.wav"
    ar_ref = "data/tts_dataset/wavs/ar_0001.wav"
    ur_ref = "data/tts_dataset/wavs/ur_0001.wav"
    
    en_gpt, en_spk = en_model.get_conditioning_latents(audio_path=[en_ref])
    ar_gpt, ar_spk = ar_model.get_conditioning_latents(audio_path=[ar_ref])

    test_cases = [
        {
            "id": "english_continuity",
            "lang": "en",
            "preface": "In the name of Allah, the Most Gracious, the Most Merciful. Let us listen to the translation of the verse:",
            "golden": en_ref,
            "engine": "xtts"
        },
        {
            "id": "urdu_continuity",
            "lang": "ur",
            "preface": "بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ. قرآنِ پاک کا اردو ترجمہ ملاحظہ فرمائیں:",
            "golden": ur_ref,
            "engine": "mms"
        },
        {
            "id": "arabic_continuity",
            "lang": "ar",
            "preface": "بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ. استمعوا إلى تلاوة القرآن الكريم:",
            "golden": ar_ref,
            "engine": "xtts"
        }
    ]

    for case in test_cases:
        out_file = os.path.join(OUTPUT_DIR, f"maulana_to_golden_{case['lang']}.wav")
        print(f" > Generating {case['id']}...")
        
        # 1. Generate Maulana Preface
        if case["engine"] == "xtts":
            model = en_model if case["lang"] == "en" else ar_model
            gpt = en_gpt if case["lang"] == "en" else ar_gpt
            spk = en_spk if case["lang"] == "en" else ar_spk
            out = model.inference(case["preface"], case["lang"], gpt, spk, temperature=0.6)
            wav_preface = out["wav"].cpu().numpy() if hasattr(out["wav"], "cpu") else out["wav"]
            target_rate = 24000
        else:
            inputs = ur_tokenizer(text=case["preface"], return_tensors="pt").to("cuda")
            with torch.no_grad():
                output = ur_model(**inputs).waveform
            wav_preface = output[0].cpu().numpy()
            target_rate = 16000

        # 2. Load REAL Golden Sample
        g_rate, g_wav = load_wav(case["golden"])
        
        # 3. Normalize & Stitch
        wav_preface = wav_preface / np.abs(wav_preface).max() * 0.9
        g_wav = g_wav / np.abs(g_wav).max() * 0.9
        pause = np.zeros(int(target_rate * 0.2), dtype=np.float32)
        
        # Basic rate matching for the final file
        if g_rate != target_rate:
            import scipy.signal as signal
            secs = len(g_wav) / g_rate
            samps = int(secs * target_rate)
            g_wav = signal.resample(g_wav, samps)
            
        full_wav = np.concatenate([wav_preface, pause, g_wav])
        wavfile.write(out_file, target_rate, full_wav)
        print(f"   -> READY: {out_file}")

    print("\n--- FORENSIC CONTINUITY TEST COMPLETE ---")

if __name__ == "__main__":
    try:
        generate_forensic_continuity()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"ERROR: {e}")
