
import os
import torch
from TTS.utils.synthesizer import Synthesizer
from pathlib import Path
import sys

def generate_maulana_samples():
    print("--- GENERATING FINAL MAULANA SAMPLES (STABLE + CONTINUOUS) ---")
    
    # 1. SETUP LANGUAGES
    langs = ["en", "ar"]
    
    for lang in langs:
        print(f"\n[Processing {lang.upper()}]")
        
        # Paths
        MODEL_DIR = f"ai_bridge/models/maulana_{lang}_v70_v71" if lang == "en" else "ai_bridge/models/ar_xtts_v71"
        # We'll normalize to a standard folder name later, but for now:
        if lang == "en":
            MODEL_DIR = "ai_bridge/models/en_xtts_v70"
        else:
            MODEL_DIR = "ai_bridge/models/ar_xtts_v71"
            
        # Ensure dir exists (we'll download Arabic soon)
        if not os.path.exists(MODEL_DIR):
            print(f"Skipping {lang} - weights not found yet.")
            continue
            
        # Ensure model.pth exists
        if not os.path.exists(os.path.join(MODEL_DIR, "model.pth")):
            if os.path.exists(os.path.join(MODEL_DIR, "best_model.pth")):
                os.rename(os.path.join(MODEL_DIR, "best_model.pth"), os.path.join(MODEL_DIR, "model.pth"))

        # 2. Reference Audio
        REF_WAV = f"ai_bridge/data/tts_dataset/wavs_{lang}/{lang}_0001.mp3"
        if not os.path.exists(REF_WAV):
            print(f"ERROR: Reference wav not found at {REF_WAV}")
            continue

        # 3. Ignite Synthesizer
        print(" > Loading Model...")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        
        try:
            syn = Synthesizer(
                model_dir=MODEL_DIR,
                use_cuda=(device == "cuda")
            )
            
            # 4. Generate
            texts = {
                "en": "My dear student, Tahj-weed is the beautification of the Quran. Always remember to recite with a calm heart and clear articulation. May Allah bless your journey of learning.",
                "ar": "يا بني، التجويد هو تزيين القرآن. تذكر دائماً أن ترتل بقلب هادئ ونطق واضح. بارك الله في رحلتك العلمية."
            }
            
            text = texts[lang]
            output_path = f"ai_bridge/samples/maulana_{lang}_final_stable.wav"
            os.makedirs("ai_bridge/samples", exist_ok=True)
            
            print(f" > Synthesizing: '{text}'")
            # split_sentences=False removes the hard 0.4s gaps between periods
            wav = syn.tts(
                text=text,
                speaker_name=f"maulana_{lang}",
                speaker_wav=REF_WAV,
                language_name=lang,
                temperature=0.65,
                repetition_penalty=10.0,
                split_sentences=False 
            )
            
            syn.save_wav(wav, output_path)
            print(f"SUCCESS: {lang.upper()} sample saved to {output_path}")
            
        except Exception as e:
            print(f"ERROR during {lang} synthesis: {e}")

if __name__ == "__main__":
    generate_maulana_samples()
