import os
import zipfile
import pandas as pd
from tqdm import tqdm

def package_urdu_dataset():
    print("--- PACKAGING URDU DATASET FOR GCP FORGE ---")
    CSV_PATH = "data/tts_dataset_aligned/ur_aligned.csv"
    OUTPUT_ZIP = "urdu_gcp_forge.zip"
    
    if not os.path.exists(CSV_PATH):
        print(f"ERROR: {CSV_PATH} not found. Run dataset alignment first.")
        return

    df = pd.read_csv(CSV_PATH)
    print(f" > Found {len(df)} aligned Urdu pairs.")

    with zipfile.ZipFile(OUTPUT_ZIP, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 1. Add the CSV
        zipf.write(CSV_PATH, arcname="ur_aligned.csv")
        
        # 2. Add the audio files
        print(" > Compressing audio files...")
        for i, row in tqdm(df.iterrows(), total=len(df)):
            audio_path = row["audio_path"]
            if os.path.exists(audio_path):
                # We put them all in a 'wavs' folder in the zip
                zipf.write(audio_path, arcname=f"wavs/{os.path.basename(audio_path)}")
            else:
                print(f"   -> WARNING: File missing: {audio_path}")

    print(f"\n--- SUCCESS: {OUTPUT_ZIP} CREATED ---")
    print(f" > Size: {os.path.getsize(OUTPUT_ZIP) / (1024*1024):.2f} MB")

if __name__ == "__main__":
    package_urdu_dataset()
