import urllib.request
import json
import csv
import os
import time
import logging
from pathlib import Path
import torch
import torchaudio

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("DatasetExtractor")

# Config
NUM_AYAHS = 3000  # Expanded to 3000 Ayahs for robust fine-tuning

DATASET_DIR = Path("ai_bridge/data/tts_dataset")

EDITIONS = {
    "en": {"audio": "en.walk", "text": "en.sahih"},
    "ar": {"audio": "ar.alafasy", "text": "quran-uthmani"}
}

def ensure_dirs():
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    for lang in EDITIONS.keys():
        (DATASET_DIR / f"wavs_{lang}").mkdir(exist_ok=True)

def convert_to_wav(input_path: Path, output_path: Path):
    """Converts audio to 22050Hz mono WAV for Coqui TTS."""
    try:
        waveform, sample_rate = torchaudio.load(str(input_path))
        # Resample to 22050Hz if needed
        if sample_rate != 22050:
            resampler = torchaudio.transforms.Resample(sample_rate, 22050)
            waveform = resampler(waveform)
        
        # Convert to mono if stereo
        if waveform.shape[0] > 1:
            waveform = torch.mean(waveform, dim=0, keepdim=True)
            
        torchaudio.save(str(output_path), waveform, 22050)
        return True
    except Exception as e:
        log.error(f"Conversion error for {input_path}: {e}")
        return False

def fetch_ayah_data(ayah_number: int, edition_audio: str, edition_text: str) -> dict:
    url_audio = f"http://api.alquran.cloud/v1/ayah/{ayah_number}/{edition_audio}"
    url_text = f"http://api.alquran.cloud/v1/ayah/{ayah_number}/{edition_text}"
    
    req_audio = urllib.request.Request(url_audio, headers={'User-Agent': 'Mozilla/5.0'})
    req_text = urllib.request.Request(url_text, headers={'User-Agent': 'Mozilla/5.0'})
    
    try:
        with urllib.request.urlopen(req_audio, timeout=10) as resp_a:
            data_audio = json.loads(resp_a.read())
        with urllib.request.urlopen(req_text, timeout=10) as resp_t:
            data_text = json.loads(resp_t.read())
            
        if data_audio['code'] == 200 and data_text['code'] == 200:
            return {
                'audio': data_audio['data']['audio'],
                'text': data_text['data']['text']
            }
    except Exception as e:
        log.error(f"Error fetching Ayah {ayah_number}: {e}")
    return None

def download_audio(url: str, output_path: Path):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            output_path.write_bytes(response.read())
            return True
    except Exception as e:
        log.error(f"Error downloading audio {url}: {e}")
        return False

def extract_dataset():
    ensure_dirs()
    
    for lang, config in EDITIONS.items():
        log.info(f"--- Starting Extraction for {config['audio']} ({lang.upper()}) ---")
        
        csv_path = DATASET_DIR / f"metadata_{lang}.csv"
        wavs_dir = DATASET_DIR / f"wavs_{lang}"
        
        # Open in append mode, but we'll use a set to avoid duplicates in metadata
        existing_files = set()
        if csv_path.exists():
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f, delimiter='|')
                for row in reader:
                    if row: existing_files.add(row[0])

        with open(csv_path, "a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter='|')
            
            for ayah_num in range(1, NUM_AYAHS + 1):
                base_name = f"{lang}_{ayah_num:04d}"
                wav_filename = f"{base_name}.wav"
                wav_path = wavs_dir / wav_filename
                mp3_path = wavs_dir / f"{base_name}.mp3"
                
                if wav_path.exists() and base_name in existing_files:
                    log.info(f"Skipping {wav_filename} (already exists)")
                    continue
                    
                data = fetch_ayah_data(ayah_num, config['audio'], config['text'])
                if not data:
                    time.sleep(1)
                    continue
                    
                text = data['text'].replace("\n", " ").strip()
                audio_url = data['audio']
                
                log.info(f"Downloading Ayah {ayah_num}...")
                if download_audio(audio_url, mp3_path):
                    if convert_to_wav(mp3_path, wav_path):
                        writer.writerow([base_name, text])
                        log.info(f"Saved & Converted {base_name}")
                        # Cleanup MP3 to save space
                        if mp3_path.exists():
                            os.remove(mp3_path)
                    else:
                        log.error(f"Failed to convert {base_name}")
                
                time.sleep(0.5)

if __name__ == "__main__":
    extract_dataset()
    log.info(f"Extraction complete. Check {DATASET_DIR}")
