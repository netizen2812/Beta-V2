
import os
import torch
from TTS.api import TTS
from pathlib import Path

def generate_sample():
    print("--- GENERATING ENGLISH MAULANA SAMPLE ---")
    
    # 1. Setup Paths
    BUCKET_DIR = "gs://maulana-urdu-forge-project-ffb3710a/en_xtts_v70"
    LOCAL_DIR = "/tmp/en_weights"
    os.makedirs(LOCAL_DIR, exist_ok=True)
    
    # 2. Download Weights
    print(" > Downloading trained weights from GCS...")
    os.system(f"gcloud storage cp {BUCKET_DIR}/best_model.pth {LOCAL_DIR}/")
    os.system(f"gcloud storage cp {BUCKET_DIR}/config.json {LOCAL_DIR}/")
    
    # 3. Download Base Model Files (Vocab, DVAE)
    print(" > Downloading base model components...")
    os.system("curl -L https://coqui.gateway.scarf.sh/hf-coqui/XTTS-v2/main/vocab.json -o " + LOCAL_DIR + "/vocab.json")
    os.system("curl -L https://coqui.gateway.scarf.sh/hf-coqui/XTTS-v2/main/dvae.pth -o " + LOCAL_DIR + "/dvae.pth")
    os.system("curl -L https://coqui.gateway.scarf.sh/hf-coqui/XTTS-v2/main/mel_stats.pth -o " + LOCAL_DIR + "/mel_stats.pth")
    
    # 4. Reference Audio
    # We'll use one of the original English training samples as a reference
    REF_WAV = "/tmp/ref.wav"
    os.system("gcloud storage cp gs://maulana-urdu-forge-project-ffb3710a/en_gcp_forge.zip /tmp/data.zip")
    os.system("unzip -q /tmp/data.zip -d /tmp/data")
    # Pick a random wav
    wav_files = list(Path("/tmp/data/wavs").glob("*.wav"))
    ref_path = str(wav_files[0])
    
    # 5. Ignite TTS
    print(" > Loading Fine-Tuned Model...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tts = TTS(model_path=f"{LOCAL_DIR}/best_model.pth", config_path=f"{LOCAL_DIR}/config.json").to(device)
    
    # 6. Generate
    text = "Assalamu Alaikum. This is the Maulana English voice model, successfully fine tuned on the neural forge. May this service benefit the seekers of knowledge."
    output_path = "/tmp/maulana_en_sample.wav"
    
    print(f" > Synthesizing: '{text}'")
    tts.tts_to_file(
        text=text,
        speaker_wav=ref_path,
        language="en",
        file_path=output_path
    )
    
    # 7. Upload
    print(" > Uploading sample to GCS...")
    os.system(f"gcloud storage cp {output_path} gs://maulana-urdu-forge-project-ffb3710a/samples/maulana_en_v70_sample.wav")
    print("--- SAMPLE GENERATED SUCCESSFULLY ---")

if __name__ == "__main__":
    generate_sample()
