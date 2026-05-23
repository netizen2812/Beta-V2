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

def load_deep_pillar(lang):
    path = f"C:/Maulana_Training_Forge/deep_pillars/{lang}/model.pth"
    config = XttsConfig()
    config.load_json(os.path.join(MODEL_DIR, "config.json"))
    model = Xtts.init_from_config(config)
    model.load_checkpoint(config, checkpoint_dir=MODEL_DIR, use_deepspeed=False)
    model.load_state_dict(torch.load(path, map_location="cuda"), strict=False)
    model.cuda()
    return model

def generate_deep_master_proofs():
    print("--- GENERATING DEEP MASTER PILLAR PROOFS ---")
    OUTPUT_DIR = "data/verification_deep_master"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    test_cases = [
        {"id": "en_pure", "lang": "en", "text": "Assalamu Alaikum. This is the Maulana English voice, deeply converged on his authoritative identity.", "ref": "data/tts_dataset/wavs/en_0001.wav"},
        {"id": "ur_pure", "lang": "ur", "text": "بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ. مولانا کی اردو آواز اب مکمل گہرائی کے ساتھ تیار ہے۔", "ref": "data/tts_dataset/wavs/ur_0001.wav"},
        {"id": "ar_pure", "lang": "ar", "text": "بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ. استمعوا إلى تلاوة القرآن الكريم بصوت مولانا.", "ref": "data/tts_dataset/wavs/ar_0001.wav"},
        {"id": "en_ar_monotonous", "lang": "en", "text": "The Almighty says in the Quran: اقْرَأْ بِاسْمِ رَبِّكَ الَّذِي خَلَقَ which is the light of guidance.", "ref": "data/tts_dataset/wavs/en_0001.wav"},
        {"id": "ur_ar_monotonous", "lang": "ur", "text": "رسول اللہ نے فرمایا: طَلَبُ الْعِلْمِ فَرِيضَةٌ جس کا مطلب ہے کہ علم حاصل کرنا فرض ہے۔", "ref": "data/tts_dataset/wavs/ur_0001.wav"}
    ]

    for case in test_cases:
        lang = case["lang"]
        out_file = os.path.join(OUTPUT_DIR, f"maulana_deep_{case['id']}.wav")
        print(f" > Generating {case['id'].upper()}...")
        
        # Load the Dedicated Deep Pillar
        model = load_deep_pillar(lang)
        gpt, spk = model.get_conditioning_latents(audio_path=[case["ref"]])

        # Generate (With Forensic Stitch for Pure cases)
        inference_lang = "hi" if lang == "ur" else lang
        out = model.inference(case["text"], inference_lang, gpt, spk, temperature=0.6)
        wav = out["wav"].cpu().numpy() if hasattr(out["wav"], "cpu") else out["wav"]
        wav = wav / np.abs(wav).max() * 0.9

        if "monotonous" not in case["id"]:
            # Forensic Stitch with Golden Sample
            g_rate, g_wav = load_wav(case["ref"])
            g_wav = g_wav / np.abs(g_wav).max() * 0.9
            pause = np.zeros(int(SAMPLE_RATE * 0.2), dtype=np.float32)
            full_wav = np.concatenate([wav, pause, g_wav])
            wavfile.write(out_file, SAMPLE_RATE, full_wav)
        else:
            wavfile.write(out_file, SAMPLE_RATE, wav)
            
        print(f"   -> READY: {out_file}")

    print("\n--- DEEP MASTER PILLAR PROOFS COMPLETE ---")

if __name__ == "__main__":
    try:
        generate_deep_master_proofs()
    except Exception as e:
        print(f"ERROR: {e}")
