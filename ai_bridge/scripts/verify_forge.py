import os
import torch
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts
from pathlib import Path

def generate_samples():
    print("--- GENERATING TRILINGUAL SAMPLES FROM FORGED WEIGHTS ---")
    
    # 1. Setup Paths
    MODEL_PATH = "C:/Maulana_Training_Forge/stable_weights/best_model.pth"
    CONFIG_PATH = "models/base_xtts/config.json"
    VOCAB_PATH = "models/base_xtts/vocab.json"
    SPEAKER_WAV = "data/tts_dataset/wavs/en_0001.wav"
    OUTPUT_DIR = "data/samples/forged_maulana"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 2. Load Model
    config = XttsConfig()
    config.load_json(CONFIG_PATH)
    model = Xtts.init_from_config(config)
    
    print(f" > Loading Forged Weights: {MODEL_PATH}")
    # Load state dict with strict=False
    state_dict = torch.load(MODEL_PATH, map_location="cuda")
    model.load_state_dict(state_dict, strict=False)
    
    # Initialize Tokenizer (Crucial for XTTS)
    from TTS.tts.models.xtts import VoiceBpeTokenizer
    model.tokenizer = VoiceBpeTokenizer(VOCAB_PATH)
    
    model.cuda()

    # 3. Reference Latents
    print(f" > Extracting Speaker Latents from: {SPEAKER_WAV}")
    gpt_cond_latent, speaker_embedding = model.get_conditioning_latents(audio_path=[SPEAKER_WAV])

    # 4. Generate Triple Samples
    test_cases = [
        {"lang": "en", "text": "Seeking knowledge is an obligation upon every Muslim, leading us from darkness into the light of understanding."},
        {"lang": "ur", "text": "Ilm haasil karna har Musalmaan par farz hai, jo hamein andheron se nikaal kar hidayat ki roshni mein laata hai."},
        {"lang": "ar", "text": "طلب العلم فريضة على كل مسلم، ينير لنا طريق الحق والهدى."}
    ]

    for case in test_cases:
        lang = case["lang"]
        text = case["text"]
        out_file = os.path.join(OUTPUT_DIR, f"sample_{lang}.wav")
        
        print(f" > Generating {lang.upper()} Sample...")
        out = model.inference(
            text,
            lang,
            gpt_cond_latent,
            speaker_embedding,
            temperature=0.7,
            length_penalty=1.0,
            repetition_penalty=5.0,
            top_k=50,
            top_p=0.85,
        )
        
        import scipy.io.wavfile as wavfile
        wavfile.write(out_file, 24000, out["wav"].cpu().numpy())
        print(f"   -> Saved: {out_file}")

    print("\n--- SAMPLES GENERATED SUCCESSFULLY ---")

if __name__ == "__main__":
    try:
        generate_samples()
    except Exception as e:
        print(f"ERROR: {e}")
