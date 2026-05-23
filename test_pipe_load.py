from transformers import pipeline
import torch
from pathlib import Path

MODEL_ID = "tarteel-ai/whisper-base-ar-quran"
path = "testing dataset/WhatsApp Audio 2026-05-12 at 12.49.45 AM (1).mp4"

try:
    print(f"Loading pipe for {MODEL_ID}...")
    pipe = pipeline("automatic-speech-recognition", model=MODEL_ID)
    print("Running inference on path...")
    result = pipe(path, generate_kwargs={"language": "ar", "task": "transcribe"})
    print(f"Success! Text: {result['text']}")
except Exception as e:
    print(f"Failed: {e}")
