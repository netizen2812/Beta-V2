import urllib.request
import json
import os
import concurrent.futures
import logging
from pathlib import Path
import torch
import torchaudio

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("ParallelExtractor")

NUM_AYAHS = 1000
DATASET_DIR = Path("data/tts_dataset")
import time
CONCURRENCY = 5 # Sprint mode

EDITIONS = {
    "en": {"audio": "en.walk", "text": "en.sahih"},
    "ur": {"audio": "ur.khan", "text": "ur.jalandhry"},
    "ar": {"audio": "ar.alafasy", "text": "quran-uthmani"}
}

def ensure_dirs():
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    for lang in EDITIONS.keys():
        (DATASET_DIR / lang / "wavs").mkdir(parents=True, exist_ok=True)

def convert_and_save(temp_path, final_path):
    try:
        waveform, sample_rate = torchaudio.load(str(temp_path))
        if sample_rate != 22050:
            waveform = torchaudio.transforms.Resample(sample_rate, 22050)(waveform)
        if waveform.shape[0] > 1:
            waveform = torch.mean(waveform, dim=0, keepdim=True)
        torchaudio.save(str(final_path), waveform, 22050)
        return True
    except Exception as e:
        log.error(f"Conversion error: {e}")
        return False

def process_ayah(lang, config, ayah_num):
    time.sleep(0.3) # Sprint pause
    final_path = DATASET_DIR / lang / "wavs" / f"{lang}_{str(ayah_num).zfill(4)}.wav"
    if final_path.exists():
        return True

    url_audio = f"http://api.alquran.cloud/v1/ayah/{ayah_num}/{config['audio']}"
    try:
        with urllib.request.urlopen(url_audio, timeout=10) as resp:
            data = json.loads(resp.read())
            audio_url = data['data']['audio']
            
            temp_file = Path(f"temp_{lang}_{ayah_num}.mp3")
            with urllib.request.urlopen(audio_url, timeout=10) as audio_resp:
                temp_file.write_bytes(audio_resp.read())
            
            success = convert_and_save(temp_file, final_path)
            if temp_file.exists(): os.remove(temp_file)
            if success:
                log.info(f"  [OK] {lang.upper()} Ayah {ayah_num}")
            return success
    except Exception as e:
        log.error(f"  [FAIL] {lang} {ayah_num}: {e}")
        return False

def run_extraction():
    ensure_dirs()
    import random
    all_tasks = []
    for lang, config in EDITIONS.items():
        for ayah_num in range(1, NUM_AYAHS + 1):
            all_tasks.append((lang, config, ayah_num))
    
    # SHUFFLE to ensure we get samples from all languages simultaneously
    random.shuffle(all_tasks)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
        futures = [executor.submit(process_ayah, *task) for task in all_tasks]
        concurrent.futures.wait(futures)

if __name__ == "__main__":
    run_extraction()
