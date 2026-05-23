import os
import torch
import scipy.io.wavfile as wavfile
import numpy as np
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts
from transformers import VitsModel, VitsTokenizer

SAMPLE_RATE_XTTS = 24000
SAMPLE_RATE_MMS  = 16000
MODEL_DIR_XTTS   = "models/base_xtts"
REAL_AR_WEIGHTS  = "C:/Maulana_Training_Forge/deep_pillars/ar/model_real.pth"
REAL_UR_DIR      = "C:/Maulana_Training_Forge/deep_pillars/ur_real"

def generate_real_master_proofs():
    print("--- GENERATING REAL MASTER PROOFS (ALQURAN ALIGNMENT) ---")
    OUTPUT_DIR = "data/verification_real_al_quran"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. REAL ARABIC (XTTSv2 + Uthmani)
    print(" > Synthesizing REAL ARABIC (Surah Al-Fatihah)...")
    config = XttsConfig()
    config.load_json(os.path.join(MODEL_DIR_XTTS, "config.json"))
    ar_model = Xtts.init_from_config(config)
    ar_model.load_checkpoint(config, checkpoint_dir=MODEL_DIR_XTTS, use_deepspeed=False)
    ar_model.load_state_dict(torch.load(REAL_AR_WEIGHTS, map_location="cuda"), strict=False)
    ar_model.cuda()
    
    ar_ref = "data/tts_dataset/ar/wavs/ar_0001.wav"
    gpt, spk = ar_model.get_conditioning_latents(audio_path=[ar_ref])
    ar_text = "بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ. الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ."
    out_ar = ar_model.inference(ar_text, "ar", gpt, spk, temperature=0.65)
    wav_ar = out_ar["wav"].cpu().numpy() if hasattr(out_ar["wav"], "cpu") else out_ar["wav"]
    wav_ar = wav_ar / np.abs(wav_ar).max() * 0.9
    wavfile.write(os.path.join(OUTPUT_DIR, "maulana_ar_real_fatihah.wav"), 24000, wav_ar)
    
    # 2. REAL URDU (MMS-VITS + Jalandhry)
    print(" > Synthesizing REAL URDU (Scholarly Translation)...")
    ur_tokenizer = VitsTokenizer.from_pretrained(REAL_UR_DIR)
    ur_model = VitsModel.from_pretrained(REAL_UR_DIR)
    ur_model.cuda()
    
    ur_text = "اللہ کے نام سے شروع جو بڑا مہربان نہایت رحم والا ہے۔ سب تعریفیں اللہ ہی کے لیے ہیں جو تمام جہانوں کا پالنے والا ہے۔"
    inputs = ur_tokenizer(text=ur_text, return_tensors="pt").to("cuda")
    with torch.no_grad():
        out_ur = ur_model(**inputs)
    wav_ur = out_ur.waveform.cpu().numpy().squeeze()
    wav_ur = wav_ur / np.abs(wav_ur).max() * 0.9
    wavfile.write(os.path.join(OUTPUT_DIR, "maulana_ur_real_jalandhry.wav"), 16000, wav_ur)

    print("\n--- REAL MASTER PROOFS READY ---")

if __name__ == "__main__":
    try:
        generate_real_master_proofs()
    except Exception as e:
        print(f"ERROR: {e}")
