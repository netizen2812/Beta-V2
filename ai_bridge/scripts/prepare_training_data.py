import os
import csv
from pathlib import Path

def prepare_unified_metadata():
    master_metadata = Path("data/tts_dataset/metadata_unified.csv")
    languages = ["en", "ur", "ar"]
    
    print("Building Unified Multilingual Manifest...")
    
    with open(master_metadata, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter='|')
        
        for lang in languages:
            wav_dir = Path(f"data/tts_dataset/{lang}/wavs")
            if not wav_dir.exists():
                # Try fallback path
                wav_dir = Path(f"data/tts_dataset/wavs_{lang}")
                
            if wav_dir.exists():
                files = list(wav_dir.glob("*.wav"))
                print(f"  -> Found {len(files)} files for [{lang.upper()}]")
                for wav_path in files:
                    # LJSpeech expects just the ID (filename without extension)
                    # and looks in dataset_path/wavs/
                    writer.writerow([wav_path.stem, "Scholarly Maulana wisdom and Quranic text.", "Maulana"])

    print(f"DONE: Unified manifest saved to {master_metadata}")

if __name__ == "__main__":
    prepare_unified_metadata()
