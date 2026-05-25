import requests
import json
import os

AI_BRIDGE_URL = "http://127.0.0.1:8000"

print("1. Querying /api/health...")
try:
    res = requests.get(f"{AI_BRIDGE_URL}/api/health", timeout=5)
    print("Status:", res.status_code)
    print("Response:", json.dumps(res.json(), indent=2))
except Exception as e:
    print("Failed to reach health endpoint:", e)

print("\n2. Testing /api/tajweed-check with a silence/empty file...")
# Let's generate a tiny dummy audio file or use one of the test audios
audio_path = "test_ar_soothing.wav"
if not os.path.exists(audio_path):
    print(f"Warning: {audio_path} not found. Creating a 1-second silent WAV file.")
    import numpy as np
    import soundfile as sf
    # 1 second of silence at 16kHz
    silent_data = np.zeros(16000, dtype=np.int16)
    sf.write(audio_path, silent_data, 16000)

try:
    with open(audio_path, "rb") as f:
        files = {"audio_file": (os.path.basename(audio_path), f, "audio/wav")}
        data = {"ayah_id": "1:1", "madhab": "shafi"}
        res = requests.post(f"{AI_BRIDGE_URL}/api/tajweed-check", files=files, data=data, timeout=90)
        print("Status:", res.status_code)
        try:
            print("Response:", json.dumps(res.json(), indent=2))
        except:
            print("Response (Raw):", res.text[:500])
except Exception as e:
    print("Failed to perform Tajweed check:", e)

print("\n3. Testing /api/maulana-voice endpoint...")
try:
    body = {
        "rule": "Qalqalah",
        "word": "بِسْمِ",
        "guidance": "Please bounce the letter Qaaf.",
        "language": "english",
        "madhab": "shafi",
        "ayah_id": "1:1"
    }
    res = requests.post(f"{AI_BRIDGE_URL}/api/maulana-voice", json=body, timeout=60)
    print("Status:", res.status_code)
    try:
        # Check if it's text fallback or audio response headers
        if "application/json" in res.headers.get("Content-Type", ""):
            print("Response (JSON):", json.dumps(res.json(), indent=2))
        else:
            print("Response Headers:", dict(res.headers))
            print("Audio length (bytes):", len(res.content))
    except Exception as parse_err:
        print("Response parsing failed:", parse_err)
        print("Response (Raw):", res.text[:500])
except Exception as e:
    print("Failed to reach Maulana voice endpoint:", e)
