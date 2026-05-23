import os
import torch
import torchaudio
import scipy.io.wavfile as wavfile
import numpy as np
from transformers import VitsModel, VitsTokenizer

# 1. Paths and Config
MMS_DIR = "C:/Maulana_Training_Forge/deep_pillars/ur_real_50epoch" # Will use the 50-epoch weights
if not os.path.exists(os.path.join(MMS_DIR, "config.json")):
    MMS_DIR = "C:/Maulana_Training_Forge/deep_pillars/ur_real" # Fallback to epoch 1 if 50 isn't done yet

OUTPUT_DIR = "data/verification_upscaled_urdu"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def verify_upscaled_urdu():
    print("--- VERIFYING NATIVE URDU (DSP UPSCALED) ---")
    
    # 2. Load Native MMS Engine
    print(f" > Injecting Native Urdu weights from {MMS_DIR}...")
    tokenizer = VitsTokenizer.from_pretrained(MMS_DIR)
    model = VitsModel.from_pretrained(MMS_DIR)
    model.cuda()
    model.eval()

    # 3. Generate Native 16kHz Audio
    ur_text = "اللہ کے نام سے شروع جو بڑا مہربان نہایت رحم والا ہے۔ یہ آواز اب بالکل دیسی اور صاف ہے۔"
    print(" > Synthesizing (Native 16kHz)...")
    inputs = tokenizer(text=ur_text, return_tensors="pt").to("cuda")
    with torch.no_grad():
        out = model(**inputs)
    
    wav_16k = out.waveform.cpu() # shape [1, T]

    # 4. DSP Pipeline: Upsample to 24kHz
    print(" > DSP: Upsampling mathematically to 24kHz...")
    resampler = torchaudio.transforms.Resample(orig_freq=16000, new_freq=24000)
    wav_24k = resampler(wav_16k)

    # 5. DSP Pipeline: High-Shelf EQ (Treble Boost)
    # We add a 6dB boost to frequencies above 4000Hz to restore the missing "crispness" of the consonants.
    print(" > DSP: Applying High-Shelf Exciter (Treble Boost)...")
    wav_crisp = torchaudio.functional.treble_biquad(
        wav_24k, 
        sample_rate=24000, 
        gain=6.0, 
        central_freq=4000.0, 
        Q=0.707
    )

    # 6. Normalize and Save
    wav_final = wav_crisp.squeeze().numpy()
    wav_final = wav_final / np.abs(wav_final).max() * 0.9
    
    out_file = os.path.join(OUTPUT_DIR, "maulana_ur_native_upscaled.wav")
    wavfile.write(out_file, 24000, wav_final)
    print(f"   -> READY: {out_file}")

if __name__ == "__main__":
    try:
        verify_upscaled_urdu()
    except Exception as e:
        print(f"ERROR: {e}")
