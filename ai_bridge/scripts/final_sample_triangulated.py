import os
import torch
import scipy.io.wavfile as wavfile
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts
from pathlib import Path

def generate_triangulated_samples():
    print("--- GENERATING TRIANGULATED NEURAL SAMPLES ---")
    
    # 1. Setup Paths
    MODEL_DIR = "models/base_xtts"
    CONFIG_PATH = os.path.join(MODEL_DIR, "config.json")
    OUTPUT_DIR = "data/verification_samples_triangulated"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 2. Load Model
    config = XttsConfig()
    config.load_json(CONFIG_PATH)
    model = Xtts.init_from_config(config)
    
    # Initialize Tokenizer (Crucial for XTTS)
    from TTS.tts.models.xtts import VoiceBpeTokenizer
    model.tokenizer = VoiceBpeTokenizer(os.path.join(MODEL_DIR, "vocab.json"))
    
    print(f" > Loading Base Engine...")
    model.load_checkpoint(config, checkpoint_dir=MODEL_DIR, use_deepspeed=False)
    model.cuda()

    # 3. Neural Triangulation: Define Language-Specific Anchors
    test_cases = [
        {
            "lang": "en", 
            "text": "Assalamu Alaikum. This is the Maulana voice, now speaking with a fluid and continuous English tone.",
            "ref": "data/tts_dataset/wavs/en_0001.wav",
            "temp": 0.65
        },
        {
            "lang": "hi", # Using hi pathway but with UR anchor
            "text": "اسلام علیکم۔ مولانا کی آواز اب اردو میں بھی بالکل تیار ہے اور حِکمت کی باتیں کر رہی ہے۔",
            "ref": "data/tts_dataset/wavs/ur_0001.wav",
            "temp": 0.55 # Lower for stricter native Urdu phonetics
        },
        {
            "lang": "ar", 
            "text": "السلام عليكم. صوت مولانا الآن جاهز باللغة العربية لنشر العلم والهدى.",
            "ref": "data/tts_dataset/wavs/ar_0001.wav",
            "temp": 0.70 # Higher for resonant scholarly recitation
        }
    ]

    for case in test_cases:
        lang = case["lang"]
        text = case["text"]
        ref_wav = case["ref"]
        temp = case["temp"]
        
        display_lang = "UR" if lang == "hi" else lang.upper()
        out_file = os.path.join(OUTPUT_DIR, f"maulana_pure_{display_lang}.wav")
        
        print(f" > Extracting {display_lang} Anchor from: {ref_wav}")
        gpt_cond_latent, speaker_embedding = model.get_conditioning_latents(audio_path=[ref_wav])

        print(f" > Synthesizing {display_lang} with Triangulated Anchor...")
        out = model.inference(
            text,
            lang,
            gpt_cond_latent,
            speaker_embedding,
            temperature=temp,
            length_penalty=1.0,
            repetition_penalty=10.0,
            top_k=50,
            top_p=0.8,
        )
        
        # Handle both Tensor and Numpy array outputs
        wav_data = out["wav"]
        if hasattr(wav_data, "cpu"):
            wav_data = wav_data.cpu().numpy()
            
        wavfile.write(out_file, 24000, wav_data)
        print(f"   -> READY: {out_file}")

    print("\n--- TRIANGULATED SAMPLES READY FOR FINAL VERIFICATION ---")

if __name__ == "__main__":
    try:
        generate_triangulated_samples()
    except Exception as e:
        print(f"ERROR: {e}")
