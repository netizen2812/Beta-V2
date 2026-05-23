import os
import torch
import scipy.io.wavfile as wavfile
import numpy as np
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts

SAMPLE_RATE = 24000
MODEL_DIR = "models/base_xtts"

def load_wav(path):
    rate, data = wavfile.read(path)
    if data.dtype == np.int16:
        data = data.astype(np.float32) / 32768.0
    return rate, data

def load_pillar(lang):
    path = f"C:/Maulana_Training_Forge/isolated_pillars/{lang}/model.pth"
    config = XttsConfig()
    config.load_json(os.path.join(MODEL_DIR, "config.json"))
    model = Xtts.init_from_config(config)
    model.load_checkpoint(config, checkpoint_dir=MODEL_DIR, use_deepspeed=False)
    model.load_state_dict(torch.load(path, map_location="cuda"), strict=False)
    model.cuda()
    return model

def generate_final_isolated_proofs():
    print("--- GENERATING FINAL ISOLATED PILLAR PROOFS ---")
    OUTPUT_DIR = "data/verification_final_isolated"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    test_cases = [
        {"lang": "en", "preface": "In the name of Allah. Let us listen to the translation:", "ref": "data/tts_dataset/wavs/en_0001.wav"},
        {"lang": "ar", "preface": "بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ. استمعوا إلى التلاوة:", "ref": "data/tts_dataset/wavs/ar_0001.wav"},
        {"lang": "ur", "preface": "بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ. اردو ترجمہ ملاحظہ فرمائیں:", "ref": "data/tts_dataset/wavs/ur_0001.wav"}
    ]

    for case in test_cases:
        lang = case["lang"]
        out_file = os.path.join(OUTPUT_DIR, f"maulana_isolated_{lang}_proof.wav")
        print(f" > Generating {lang.upper()} Isolated Proof...")
        
        # 1. Load the Dedicated Pillar
        model = load_pillar(lang)
        gpt, spk = model.get_conditioning_latents(audio_path=[case["ref"]])

        # 2. Generate Preface
        # For Urdu, we still use the hi pathway in XTTS but with the isolated UR model
        inference_lang = "hi" if lang == "ur" else lang
        out = model.inference(case["preface"], inference_lang, gpt, spk, temperature=0.6)
        wav_preface = out["wav"].cpu().numpy() if hasattr(out["wav"], "cpu") else out["wav"]
        wav_preface = wav_preface / np.abs(wav_preface).max() * 0.9

        # 3. Load REAL Golden Sample for Stitch
        g_rate, g_wav = load_wav(case["ref"])
        g_wav = g_wav / np.abs(g_wav).max() * 0.9
        pause = np.zeros(int(SAMPLE_RATE * 0.2), dtype=np.float32)

        # 4. Stitch
        full_wav = np.concatenate([wav_preface, pause, g_wav])
        wavfile.write(out_file, SAMPLE_RATE, full_wav)
        print(f"   -> READY: {out_file}")

    print("\n--- ISOLATED PILLAR PROOFS COMPLETE ---")

if __name__ == "__main__":
    try:
        generate_final_isolated_proofs()
    except Exception as e:
        print(f"ERROR: {e}")
