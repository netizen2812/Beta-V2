import os
import torch
import sys
from TTS.utils.synthesizer import Synthesizer
from pathlib import Path

def generate_samples():
    print("=== GENERATING AUDIO SAMPLES FROM FINE-TUNED XTTS MODELS ===")
    
    langs = ["en", "ar"]
    configs = {
        "en": {
            "dir": "ai_bridge/models/en_xtts_v74",
            "ref_wav": "ai_bridge/data/tts_dataset/wavs_en/en_0001.wav",
            "text": "My dear student, Taj-weed is the beautification of the Quran. Always remember to recite with a calm heart and clear articulation. May Allah bless your journey of learning.",
            "speaker_name": "maulana_en",
            "output_stable": "ai_bridge/samples/maulana_en_v74_stable.wav",
            "output_golden": "golden_samples/maulana_en_v74.wav"
        },
        "ar": {
            "dir": "ai_bridge/models/ar_xtts_v75",
            "ref_wav": "ai_bridge/data/tts_dataset/wavs_ar/ar_0001.wav",
            "text": "يا بني، التجويد هو تزيين القرآن. تذكر دائماً أن ترتل بقلب هادئ ونطق واضح. بارك الله في رحلتك العلمية.",
            "speaker_name": "maulana_ar",
            "output_stable": "ai_bridge/samples/maulana_ar_v75_stable.wav",
            "output_golden": "golden_samples/maulana_ar_v75.wav"
        }
    }
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device detected: {device.upper()}")
    
    os.makedirs("ai_bridge/samples", exist_ok=True)
    os.makedirs("golden_samples", exist_ok=True)
    
    for lang in langs:
        print(f"\n--- Processing {lang.upper()} ---")
        cfg = configs[lang]
        
        # Verify model directory and files
        if not os.path.exists(cfg["dir"]):
            print(f"[SKIP] Model directory {cfg['dir']} does not exist.")
            continue
            
        model_path = os.path.join(cfg["dir"], "model.pth")
        config_path = os.path.join(cfg["dir"], "config.json")
        
        if not os.path.exists(model_path) or not os.path.exists(config_path):
            print(f"[SKIP] Missing model.pth or config.json in {cfg['dir']}.")
            continue
            
        if not os.path.exists(cfg["ref_wav"]):
            print(f"[ERROR] Reference WAV not found at {cfg['ref_wav']}.")
            continue
            
        print(f" > Loading {lang.upper()} model from {cfg['dir']}...")
        try:
            # Ignite Synthesizer
            syn = Synthesizer(
                model_dir=cfg["dir"],
                use_cuda=(device == "cuda")
            )
            
            print(f" > Synthesizing (split_sentences=False): '{cfg['text']}'")
            wav = syn.tts(
                text=cfg["text"],
                speaker_name=cfg["speaker_name"],
                speaker_wav=cfg["ref_wav"],
                language_name=lang,
                temperature=0.65,
                repetition_penalty=10.0,
                split_sentences=False
            )
            
            # Save to both locations
            syn.save_wav(wav, cfg["output_stable"])
            syn.save_wav(wav, cfg["output_golden"])
            
            print(f"✅ SUCCESS: Saved samples to:")
            print(f"   - {cfg['output_stable']}")
            print(f"   - {cfg['output_golden']}")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"❌ ERROR during {lang.upper()} synthesis: {e}")

if __name__ == "__main__":
    generate_samples()
