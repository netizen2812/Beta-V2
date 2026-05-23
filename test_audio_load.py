import librosa
from pathlib import Path

path = Path("testing dataset/WhatsApp Audio 2026-05-12 at 12.49.45 AM (1).mp3")
try:
    y, sr = librosa.load(str(path), sr=None)
    print(f"Success! Len: {len(y)}, SR: {sr}")
except Exception as e:
    print(f"Failed: {e}")
