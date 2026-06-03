import os
import sys
import shutil
import urllib.request
import concurrent.futures

import time

SURAH_VERSES = [
    7, 286, 200, 176, 120, 165, 206, 75, 129, 109, 123, 111, 43, 52, 99, 128, 111, 110, 98, 135,
    112, 78, 118, 64, 77, 227, 93, 88, 69, 60, 34, 30, 73, 54, 45, 83, 182, 88, 75, 85,
    54, 53, 89, 59, 37, 35, 38, 29, 18, 45, 60, 49, 62, 55, 78, 96, 29, 22, 24, 13,
    14, 11, 11, 18, 12, 12, 30, 52, 52, 44, 28, 28, 20, 56, 40, 31, 50, 40, 46, 42,
    29, 19, 36, 25, 22, 17, 19, 26, 30, 20, 15, 21, 11, 8, 8, 19, 5, 8, 8, 11,
    11, 8, 3, 9, 5, 4, 7, 3, 6, 3, 5, 4, 5, 6
]

BUCKET = "gs://imam-ai-seed-data/recitations"
LOCAL_DIR = "./tmp_recitations"

# Setup configuration
EDITIONS = {
    "en.walk": "https://cdn.islamic.network/quran/audio/192/en.walk",
    "ur.khan": "https://cdn.islamic.network/quran/audio/64/ur.khan"
}

def generate_tasks():
    tasks = []
    abs_id = 1
    for surah_idx, num_verses in enumerate(SURAH_VERSES):
        surah = surah_idx + 1
        for verse in range(1, num_verses + 1):
            for edition, base_url in EDITIONS.items():
                url = f"{base_url}/{abs_id}.mp3"
                dest_path = f"{LOCAL_DIR}/{edition}/{surah}_{verse}.mp3"
                tasks.append((url, dest_path, edition))
            abs_id += 1
    return tasks

def download_file(url, dest_path):
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    max_retries = 5
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                with open(dest_path, "wb") as f:
                    f.write(response.read())
            return True
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"Error downloading {url} to {dest_path}: {e}")
                return False
            time.sleep(1.5 ** attempt)
    return False

def main():
    print("Generating download tasks...")
    tasks = generate_tasks()
    print(f"Total tasks: {len(tasks)}")

    # Process in batches of 1000 tasks
    batch_size = 1000
    for i in range(0, len(tasks), batch_size):
        batch = tasks[i:i+batch_size]
        print(f"Processing batch {i//batch_size + 1}/{len(tasks)//batch_size + 1}...")

        with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
            futures = {executor.submit(download_file, task[0], task[1]): task for task in batch}
            for future in concurrent.futures.as_completed(futures):
                task = futures[future]
                if not future.result():
                    print(f"Failed: {task[0]}")

        # Upload the batch to GCS
        print("Uploading batch to GCS...")
        # Uploading individual edition folders directly
        for edition in EDITIONS.keys():
            edition_dir = os.path.abspath(f"{LOCAL_DIR}/{edition}")
            if os.path.exists(edition_dir) and os.listdir(edition_dir):
                # Upload all files in directory
                cmd = f'gcloud storage cp -r "{edition_dir}" "{BUCKET}/"'
                print(f"Running command: {cmd}")
                os.system(cmd)
        
        # Clean up local directory to save disk space
        shutil.rmtree(LOCAL_DIR, ignore_errors=True)

    print("Download and upload complete!")

if __name__ == "__main__":
    main()
