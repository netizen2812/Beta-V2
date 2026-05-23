import os
import torch
import sys
from TTS.utils.synthesizer import Synthesizer

def generate_samples():
    print("=== FAITH-TECH AI BRIDGE: AUDIO SAMPLE GENERATION ===")
    
    # Models to scan
    models_to_check = [
        {
            "lang": "en",
            "version": "v70",
            "dir": "ai_bridge/models/en_xtts_v70",
            "ref_wav": "ai_bridge/data/tts_dataset/wavs_en/en_0001.wav",
            "text": "My dear student, Taj-weed is the beautification of the Quran. Always remember to recite with a calm heart and clear articulation. May Allah bless your journey of learning.",
            "speaker_name": "maulana_en",
            "output_stable": "ai_bridge/samples/maulana_en_v70_stable.wav",
            "output_golden": "golden_samples/maulana_en_v70.wav"
        },
        {
            "lang": "ar",
            "version": "v71",
            "dir": "ai_bridge/models/ar_xtts_v71",
            "ref_wav": "ai_bridge/data/tts_dataset/wavs_ar/ar_0001.wav",
            "text": "يا بني، التجويد هو تزيين القرآن. تذكر دائماً أن ترتل بقلب هادئ ونطق واضح. بارك الله في رحلتك العلمية.",
            "speaker_name": "maulana_ar",
            "output_stable": "ai_bridge/samples/maulana_ar_v71_stable.wav",
            "output_golden": "golden_samples/maulana_ar_v71.wav"
        },
        {
            "lang": "en",
            "version": "v74",
            "dir": "ai_bridge/models/en_xtts_v74",
            "ref_wav": "ai_bridge/data/tts_dataset/wavs_en/en_0001.wav",
            "text": "My dear student, Taj-weed is the beautification of the Quran. Always remember to recite with a calm heart and clear articulation. May Allah bless your journey of learning.",
            "speaker_name": "maulana_en",
            "output_stable": "ai_bridge/samples/maulana_en_v74_stable.wav",
            "output_golden": "golden_samples/maulana_en_v74.wav"
        },
        {
            "lang": "ar",
            "version": "v75",
            "dir": "ai_bridge/models/ar_xtts_v75",
            "ref_wav": "ai_bridge/data/tts_dataset/wavs_ar/ar_0001.wav",
            "text": "يا بني، التجويد هو تزيين القرآن. تذكر دائماً أن ترتل بقلب هادئ ونطق واضح. بارك الله في رحلتك العلمية.",
            "speaker_name": "maulana_ar",
            "output_stable": "ai_bridge/samples/maulana_ar_v75_stable.wav",
            "output_golden": "golden_samples/maulana_ar_v75.wav"
        }
    ]
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"CUDA status: {'AVAILABLE (using GPU)' if device == 'cuda' else 'NOT AVAILABLE (using CPU)'}")
    
    os.makedirs("ai_bridge/samples", exist_ok=True)
    os.makedirs("golden_samples", exist_ok=True)
    
    for cfg in models_to_check:
        print(f"\n--- Checking {cfg['lang'].upper()} {cfg['version']} ---")
        
        # Verify model directory exists
        if not os.path.exists(cfg["dir"]):
            print(f" > [SKIP] Directory {cfg['dir']} not found.")
            continue
            
        model_path = os.path.join(cfg["dir"], "model.pth")
        config_path = os.path.join(cfg["dir"], "config.json")
        vocab_path = os.path.join(cfg["dir"], "vocab.json")
        
        # Verify files exist and are not dynamic tmp files
        if not os.path.exists(model_path):
            print(f" > [SKIP] model.pth not found in {cfg['dir']}.")
            continue
        if not os.path.exists(config_path):
            print(f" > [SKIP] config.json not found in {cfg['dir']}.")
            continue
        if not os.path.exists(vocab_path):
            print(f" > [SKIP] vocab.json not found in {cfg['dir']}.")
            continue
            
        # Verify reference audio
        if not os.path.exists(cfg["ref_wav"]):
            print(f" > [ERROR] Reference wav not found at {cfg['ref_wav']}.")
            continue
            
        # Get model size to verify it is complete (e.g. should be > 1.5 GB)
        size_bytes = os.path.getsize(model_path)
        size_gb = size_bytes / (1024 * 1024 * 1024)
        if size_bytes < 1000 * 1024 * 1024:
            print(f" > [SKIP] model.pth seems incomplete ({size_gb:.2f} GB). Wait for download.")
            continue
            
        print(f" > Found complete model ({size_gb:.2f} GB). Loading into Synthesizer...")
        try:
            syn = Synthesizer(
                model_dir=cfg["dir"],
                use_cuda=(device == "cuda")
            )
            
            if cfg["lang"] == "en":
                print(f" > Synthesizing (split_sentences=False): '{cfg['text']}'")
            else:
                print(f" > Synthesizing (split_sentences=False): [Arabic Text]")
            wav = syn.tts(
                text=cfg["text"],
                speaker_name=cfg["speaker_name"],
                speaker_wav=cfg["ref_wav"],
                language_name=cfg["lang"],
                temperature=0.65,
                repetition_penalty=10.0,
                split_sentences=False
            )
            
            syn.save_wav(wav, cfg["output_stable"])
            syn.save_wav(wav, cfg["output_golden"])
            print(f" > [SUCCESS] Generated samples successfully for {cfg['lang'].upper()} {cfg['version']}:")
            print(f"   - {cfg['output_stable']}")
            print(f"   - {cfg['output_golden']}")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f" > [ERROR] Synthesis failed: {e}")

if __name__ == "__main__":
    generate_samples()
