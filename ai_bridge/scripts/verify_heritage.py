import os
import torch
import scipy.io.wavfile as wavfile
import numpy as np
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts

SAMPLE_RATE = 24000
MODEL_DIR = "models/base_xtts"
HERITAGE_MODEL = "C:/Maulana_Training_Forge/stable_weights/best_model.pth"

def load_wav(path):
    rate, data = wavfile.read(path)
    if data.dtype == np.int16:
        data = data.astype(np.float32) / 32768.0
    return rate, data

def load_heritage_pillar():
    config = XttsConfig()
    config.load_json(os.path.join(MODEL_DIR, "config.json"))
    model = Xtts.init_from_config(config)
    model.load_checkpoint(config, checkpoint_dir=MODEL_DIR, use_deepspeed=False)
    # Load the Heritage Base
    model.load_state_dict(torch.load(HERITAGE_MODEL, map_location="cuda"), strict=False)
    model.cuda()
    return model

def generate_heritage_proofs():
    print("--- GENERATING HERITAGE PILLAR PROOFS [RESTORING IDENTITY] ---")
    OUTPUT_DIR = "data/verification_heritage"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    model = load_heritage_pillar()

    # Optimized Anchors for Tone
    anchors = {
        "en": "data/tts_dataset/wavs/en_0001.wav",
        "ar": "data/tts_dataset/wavs/ar_0010.wav", # More resonant sample for tone
        "ur": "data/tts_dataset/wavs/ur_0001.wav"
    }

    test_cases = [
        {"lang": "en", "text": "Assalamu Alaikum. This is the Maulana English voice, now restored to its full scholarly authority and resonance.", "ref": anchors["en"], "temp": 0.6},
        {"lang": "ar", "text": "بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ. اِقْـرَأْ بِـاِسْمِ رَبِّـكَ الَّـذِي خَـلَـقَ.", "ref": anchors["ar"], "temp": 0.7},
        {"lang": "ur", "text": "بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ. مولانا کی اردو آواز اب مکمل شناخت کے ساتھ تیار ہے۔", "ref": anchors["ur"], "temp": 0.55}
    ]

    for case in test_cases:
        lang = case["lang"]
        out_file = os.path.join(OUTPUT_DIR, f"maulana_heritage_{lang}.wav")
        print(f" > Generating {lang.upper()} Heritage Proof...")
        
        gpt, spk = model.get_conditioning_latents(audio_path=[case["ref"]])
        
        inference_lang = "hi" if lang == "ur" else lang
        out = model.inference(
            case["text"], 
            inference_lang, 
            gpt, 
            spk, 
            temperature=case["temp"],
            repetition_penalty=10.0,
            top_p=0.8
        )
        
        wav = out["wav"].cpu().numpy() if hasattr(out["wav"], "cpu") else out["wav"]
        wav = wav / np.abs(wav).max() * 0.9

        # Stitch with Golden Sample for Forensics
        g_rate, g_wav = load_wav(case["ref"])
        g_wav = g_wav / np.abs(g_wav).max() * 0.9
        pause = np.zeros(int(SAMPLE_RATE * 0.2), dtype=np.float32)
        
        full_wav = np.concatenate([wav, pause, g_wav])
        wavfile.write(out_file, SAMPLE_RATE, full_wav)
        print(f"   -> READY: {out_file}")

    print("\n--- HERITAGE PILLAR PROOFS COMPLETE ---")

if __name__ == "__main__":
    try:
        generate_heritage_proofs()
    except Exception as e:
        print(f"ERROR: {e}")
