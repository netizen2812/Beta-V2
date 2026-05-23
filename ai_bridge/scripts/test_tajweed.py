import os
import torch
import scipy.io.wavfile as wavfile
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts
import sys

def test_pronunciation():
    print("--- TESTING TAJWEED PRONUNCIATION ---")
    
    MODEL_DIR = "ai_bridge/models/base_xtts"
    CONFIG_PATH = os.path.join(MODEL_DIR, "config.json")
    SPEAKER_WAV = "ai_bridge/data/tts_dataset/wavs/en_0001.wav"
    OUTPUT_DIR = "ai_bridge/samples/test_pronunciation"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if not os.path.exists(SPEAKER_WAV):
        # Try finding the wav elsewhere if not in data
        print(f"Warning: {SPEAKER_WAV} not found, checking alternate locations...")
        # Check if we have any wav in data/tts_dataset
        if os.path.exists("data/tts_dataset/wavs/en_0001.wav"):
            SPEAKER_WAV = "data/tts_dataset/wavs/en_0001.wav"
        else:
            print("Error: Could not find speaker reference wav.")
            return

    # Load Model
    print(f" > Loading Model from {MODEL_DIR}...")
    config = XttsConfig()
    config.load_json(CONFIG_PATH)
    model = Xtts.init_from_config(config)
    model.load_checkpoint(config, checkpoint_dir=MODEL_DIR, use_deepspeed=False)
    
    if torch.cuda.is_available():
        model.cuda()
    else:
        print(" > CUDA not available, using CPU (will be slow)")

    # Extract Latents
    print(f" > Extracting Speaker Embedding...")
    gpt_cond_latent, speaker_embedding = model.get_conditioning_latents(audio_path=[SPEAKER_WAV])

    # Test Variations
    variations = [
        {"name": "original", "text": "The science of Tajweed is essential for Quranic recitation."},
        {"name": "phonetic_1", "text": "The science of Tah-jweed is essential for Quranic recitation."},
        {"name": "phonetic_2", "text": "The science of Ta-jweed is essential for Quranic recitation."},
        {"name": "phonetic_3", "text": "The science of Tahj-weed is essential for Quranic recitation."},
        {"name": "phonetic_4", "text": "The science of Tudj-weed is essential for Quranic recitation."},
    ]

    for v in variations:
        name = v["name"]
        text = v["text"]
        out_file = os.path.join(OUTPUT_DIR, f"tajweed_{name}.wav")
        
        print(f" > Synthesizing: {name} ('{text}')")
        out = model.inference(
            text,
            "en",
            gpt_cond_latent,
            speaker_embedding,
            temperature=0.7,
        )
        
        wav_data = out["wav"]
        if hasattr(wav_data, "cpu"):
            wav_data = wav_data.cpu().numpy()
            
        wavfile.write(out_file, 24000, wav_data)
        print(f"   -> Saved: {out_file}")

    print("\n--- PRONUNCIATION TESTS COMPLETE ---")

if __name__ == "__main__":
    test_pronunciation()
