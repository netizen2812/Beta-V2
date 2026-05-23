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
log = logging.getLogger("ParallelExtractorV2")

NUM_AYAHS = 3000
DATASET_DIR = Path("ai_bridge/data/tts_dataset")
CONCURRENCY = 3 # Conservative speed to avoid 429 rate limiting

EDITIONS = {
    "en": {"audio": "en.walk", "text": "en.sahih"},
    "ar": {"audio": "ar.alafasy", "text": "quran-uthmani"}
}

csv_locks = {
    "en": threading.Lock(),
    "ar": threading.Lock()
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

def fetch_url_with_retry(url, retries=5, backoff=2.0):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                return response.read()
        except urllib.error.HTTPError as e:
            if e.code == 429:
                log.warning(f"Rate limited (429) on {url}. Retrying in {backoff}s (attempt {attempt+1}/{retries})...")
                time.sleep(backoff)
                backoff *= 1.5
            else:
                log.error(f"HTTP error {e.code} on {url}: {e.reason}")
                break
        except Exception as e:
            log.error(f"Request failed on {url}: {e}")
            time.sleep(backoff)
            backoff *= 1.5
    return None

def fetch_ayah_data(ayah_number: int, edition_audio: str, edition_text: str) -> dict:
    url_audio = f"http://api.alquran.cloud/v1/ayah/{ayah_number}/{edition_audio}"
    url_text = f"http://api.alquran.cloud/v1/ayah/{ayah_number}/{edition_text}"
    
    # Add a small staggered delay to reduce parallel collision
    time.sleep(0.3)
    
    resp_a_bytes = fetch_url_with_retry(url_audio)
    if not resp_a_bytes: return None
    
    resp_t_bytes = fetch_url_with_retry(url_text)
    if not resp_t_bytes: return None
    
    try:
        data_audio = json.loads(resp_a_bytes)
        data_text = json.loads(resp_t_bytes)
        if data_audio['code'] == 200 and data_text['code'] == 200:
            return {
                'audio': data_audio['data']['audio'],
                'text': data_text['data']['text']
            }
    except Exception as e:
        log.error(f"JSON decode failed for Ayah {ayah_number}: {e}")
    return None

def download_audio(url: str, output_path: Path):
    resp_bytes = fetch_url_with_retry(url)
    if resp_bytes:
        output_path.write_bytes(resp_bytes)
        return True
    return False

def process_ayah(lang, config, ayah_num, existing_files):
    base_name = f"{lang}_{ayah_num:04d}"
    wav_filename = f"{base_name}.wav"
    wavs_dir = DATASET_DIR / f"wavs_{lang}"
    wav_path = wavs_dir / wav_filename
    mp3_path = wavs_dir / f"{base_name}.mp3"
    
    if wav_path.exists() and base_name in existing_files:
        return True
        
    data = fetch_ayah_data(ayah_num, config['audio'], config['text'])
    if not data:
        log.error(f"Failed to fetch data for {lang} Ayah {ayah_num}")
        return False
        
    text = data['text'].replace("\n", " ").strip()
    audio_url = data['audio']
    
    if download_audio(audio_url, mp3_path):
        if convert_to_wav(mp3_path, wav_path):
            csv_path = DATASET_DIR / f"metadata_{lang}.csv"
            with csv_locks[lang]:
                with open(csv_path, "a", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f, delimiter='|')
                    writer.writerow([base_name, text])
            log.info(f"Saved & Converted {base_name}")
            if mp3_path.exists():
                os.remove(mp3_path)
            return True
        else:
            log.error(f"Failed to convert {base_name}")
    return False

def run_extraction():
    ensure_dirs()
    
    # Read existing metadata to prevent duplicates
    existing = {"en": set(), "ar": set()}
    for lang in EDITIONS.keys():
        csv_path = DATASET_DIR / f"metadata_{lang}.csv"
        if csv_path.exists():
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f, delimiter='|')
                for row in reader:
                    if row:
                        existing[lang].add(row[0])
                        
    all_tasks = []
    # Interleave languages to balance requests
    for ayah_num in range(1, NUM_AYAHS + 1):
        for lang, config in EDITIONS.items():
            all_tasks.append((lang, config, ayah_num, existing[lang]))
            
    log.info(f"Starting parallel download with {CONCURRENCY} workers...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
        futures = [executor.submit(process_ayah, *task) for task in all_tasks]
        concurrent.futures.wait(futures)
    log.info("All downloads completed successfully.")

if __name__ == "__main__":
    run_extraction()
