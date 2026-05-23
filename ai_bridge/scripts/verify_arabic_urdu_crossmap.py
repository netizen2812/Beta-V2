import os
import torch
import scipy.io.wavfile as wavfile
import numpy as np
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts

SAMPLE_RATE = 24000
MODEL_DIR = "models/base_xtts"
REAL_AR_WEIGHTS = "C:/Maulana_Training_Forge/deep_pillars/ar/model_real.pth"

def verify_crossmap_urdu():
    print("--- VERIFYING SCHOLARLY ARABIC CROSS-MAPPED URDU ---")
    OUTPUT_DIR = "data/verification_sharp_urdu"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. Load Real Arabic (Uthmani) Weights
    # We use the Arabic-trained weights to maximize the Quranic/Scholarly resonance
    config = XttsConfig()
    config.load_json(os.path.join(MODEL_DIR, "config.json"))
    model = Xtts.init_from_config(config)
    model.load_checkpoint(config, checkpoint_dir=MODEL_DIR, use_deepspeed=False)
    
    print(" > Injecting Real Uthmani weights for maximum scholarly resonance...")
    model.load_state_dict(torch.load(REAL_AR_WEIGHTS, map_location="cuda"), strict=False)
    model.cuda()
    model.eval()

    # 2. Pick a SHARP Urdu Reference Anchor
    ur_ref = "data/tts_dataset/wavs_ur/ur_0001.wav"
    gpt, spk = model.get_conditioning_latents(audio_path=[ur_ref])
    
    # Text: Native Urdu Script. 
    ur_text = "اللہ کے نام سے شروع جو بڑا مہربان نہایت رحم والا ہے۔ کیا اب مولانا کی آواز بالکل صاف اور شفاف ہے؟"
    
    # We force the 'ar' language pathway so XTTSv2 reads the Urdu script using Arabic phonetics.
    print(" > Synthesizing Native Urdu Script via Arabic Phonemizer (lang='ar')...")
    with torch.no_grad():
        out = model.inference(
            ur_text, "ar", gpt, spk, 
            temperature=0.65,
            repetition_penalty=5.0,
            length_penalty=1.1 # Slight stretch for scholarly tone
        )
    
    wav = out["wav"].cpu().numpy() if hasattr(out["wav"], "cpu") else out["wav"]
    wav = wav / np.abs(wav).max() * 0.9
    
    out_file = os.path.join(OUTPUT_DIR, "maulana_ur_crossmapped_arabic.wav")
    wavfile.write(out_file, 24000, wav)
    print(f"   -> READY: {out_file}")

if __name__ == "__main__":
    try:
        verify_crossmap_urdu()
    except Exception as e:
        print(f"ERROR: {e}")
