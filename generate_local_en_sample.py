
import os
import torch
from TTS.utils.synthesizer import Synthesizer
from pathlib import Path
import sys

def generate_local_sample():
    print("--- GENERATING LOCAL ENGLISH MAULANA SAMPLE ---")
    
    # 1. Setup Paths
    # We use the DIRECTORY for the model, as XTTS expects a checkpoint_dir
    MODEL_DIR = "ai_bridge/models/en_xtts_v70"
    
    # Ensure vocab.json and model.pth exist in the dir
    # model.pth should be the best_model.pth we downloaded
    if not os.path.exists(os.path.join(MODEL_DIR, "model.pth")):
        if os.path.exists(os.path.join(MODEL_DIR, "best_model.pth")):
            os.rename(os.path.join(MODEL_DIR, "best_model.pth"), os.path.join(MODEL_DIR, "model.pth"))
    
    # 2. Reference Audio
    REF_WAV = "ai_bridge/data/tts_dataset/wavs_en/en_0001.mp3" 
    
    if not os.path.exists(REF_WAV):
        print(f"ERROR: Reference wav not found at {REF_WAV}")
        return

    # 3. Ignite Synthesizer (Better than the high-level TTS wrapper for custom paths)
    print(" > Loading Fine-Tuned Model into Synthesizer...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    try:
        # Using model_dir instead of tts_checkpoint avoids the XTTS 'file vs dir' error
        syn = Synthesizer(
            model_dir=MODEL_DIR,
            use_cuda=(device == "cuda")
        )
        
        # 4. Generate
        text = "Assalamu Alaikum. This is a stability test of the Maulana English voice model. We are verifying the neural forge convergence."
        output_path = "ai_bridge/samples/maulana_en_v70_stable.wav"
        os.makedirs("ai_bridge/samples", exist_ok=True)
        
        print(f" > Synthesizing (Stable Mode): '{text}'")
        # Synthesizer.tts returns a list of audio samples
        wav = syn.tts(
            text=text,
            speaker_name="maulana_v70",
            speaker_wav=REF_WAV,
            language_name="en",
            temperature=0.65,      # Lower temperature for less randomness
            repetition_penalty=10.0 # High penalty to stop mumbling/hallucinations
        )
        
        # Save
        syn.save_wav(wav, output_path)
        
        print(f"--- SUCCESS: Audio saved to {output_path} ---")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"ERROR during synthesis: {e}")

if __name__ == "__main__":
    generate_local_sample()
