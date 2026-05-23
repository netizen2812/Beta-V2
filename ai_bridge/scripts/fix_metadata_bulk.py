import urllib.request
import urllib.error
import json
import csv
import os
import concurrent.futures
import logging
from pathlib import Path
import torch
import torchaudio
import time
import threading

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("FixMetadataBulk")

NUM_AYAHS = 3000
DATASET_DIR = Path("ai_bridge/data/tts_dataset")
DOWNLOAD_CONCURRENCY = 20

EDITIONS = {
    "en": {"audio": "en.walk", "text": "en.sahih"},
    "ar": {"audio": "ar.alafasy", "text": "quran-uthmani"}
}

def ensure_dirs():
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    for lang in EDITIONS.keys():
        (DATASET_DIR / f"wavs_{lang}").mkdir(parents=True, exist_ok=True)

def convert_to_wav(input_path: Path, output_path: Path):
    try:
        waveform, sample_rate = torchaudio.load(str(input_path))
        if sample_rate != 22050:
            resampler = torchaudio.transforms.Resample(sample_rate, 22050)
            waveform = resampler(waveform)
        if waveform.shape[0] > 1:
            waveform = torch.mean(waveform, dim=0, keepdim=True)
        torchaudio.save(str(output_path), waveform, 22050)
        return True
    except Exception as e:
        log.error(f"Conversion error for {input_path}: {e}")
        return False

def fetch_url(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.read()
    except Exception as e:
        log.error(f"Failed to fetch {url}: {e}")
        return None

def get_edition_data(text_edition, audio_edition):
    log.info(f"Fetching text edition {text_edition}...")
    text_data_bytes = fetch_url(f"http://api.alquran.cloud/v1/quran/{text_edition}")
    if not text_data_bytes:
        return None
        
    log.info(f"Fetching audio edition {audio_edition}...")
    audio_data_bytes = fetch_url(f"http://api.alquran.cloud/v1/quran/{audio_edition}")
    if not audio_data_bytes:
        return None
        
    try:
        text_json = json.loads(text_data_bytes)
        audio_json = json.loads(audio_data_bytes)
        
        # Build maps of global ayah number to text and audio url
        ayah_map = {}
        
        # Parse text
        for surah in text_json['data']['surahs']:
            for ayah in surah['ayahs']:
                global_num = ayah['number']
                text = ayah['text'].replace("\n", " ").strip()
                ayah_map[global_num] = {"text": text}
                
        # Parse audio
        for surah in audio_json['data']['surahs']:
            for ayah in surah['ayahs']:
                global_num = ayah['number']
                if global_num in ayah_map:
                    ayah_map[global_num]["audio_url"] = ayah['audio']
                    
        return ayah_map
    except Exception as e:
        log.error(f"Error parsing bulk data: {e}")
        return None

def download_audio(url: str, output_path: Path):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            output_path.write_bytes(response.read())
            return True
    except Exception as e:
        log.error(f"Error downloading audio {url}: {e}")
        return False

def process_ayah_download(lang, base_name, audio_url, wav_path, mp3_path):
    if download_audio(audio_url, mp3_path):
        if convert_to_wav(mp3_path, wav_path):
            log.info(f"[Downloaded & Converted] {base_name}")
            if mp3_path.exists():
                os.remove(mp3_path)
            return True
    return False

def run_fix():
    ensure_dirs()
    
    # We will build correct metadata per language
    corrected_metadata = {"en": [], "ar": []}
    
    for lang, config in EDITIONS.items():
        log.info(f"=== Loading Bulk Data for {lang.upper()} ===")
        ayah_map = get_edition_data(config['text'], config['audio'])
        if not ayah_map:
            log.error(f"Could not load data for {lang}")
            return
            
        log.info(f"Loaded {len(ayah_map)} ayahs for {lang}")
        
        wavs_dir = DATASET_DIR / f"wavs_{lang}"
        missing_tasks = []
        
        for ayah_num in range(1, NUM_AYAHS + 1):
            base_name = f"{lang}_{ayah_num:04d}"
            wav_path = wavs_dir / f"{base_name}.wav"
            mp3_path = wavs_dir / f"{base_name}.mp3"
            
            data = ayah_map.get(ayah_num)
            if not data:
                log.error(f"No data for {base_name} in map")
                continue
                
            text = data['text']
            audio_url = data['audio_url']
            
            # Store in corrected metadata
            corrected_metadata[lang].append((base_name, text))
            
            # Check if wav file exists
            if wav_path.exists() and wav_path.stat().st_size > 44:
                continue
                
            # Queue download task if missing
            missing_tasks.append((lang, base_name, audio_url, wav_path, mp3_path))
            
        log.info(f"{lang.upper()} has {len(missing_tasks)} missing wav files.")
        
        if missing_tasks:
            log.info(f"Downloading missing audio files with concurrency={DOWNLOAD_CONCURRENCY}...")
            with concurrent.futures.ThreadPoolExecutor(max_workers=DOWNLOAD_CONCURRENCY) as executor:
                futures = [executor.submit(process_ayah_download, *task) for task in missing_tasks]
                concurrent.futures.wait(futures)
                
        # Write fresh corrected metadata
        csv_path = DATASET_DIR / f"metadata_{lang}.csv"
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter='|')
            for base_name, text in corrected_metadata[lang]:
                writer.writerow([base_name, text])
        log.info(f"Wrote metadata file to {csv_path}")

if __name__ == "__main__":
    run_fix()
