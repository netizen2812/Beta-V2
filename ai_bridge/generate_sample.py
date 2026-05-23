import torch
import soundfile as sf
from transformers import VitsTokenizer, VitsModel
import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument("--model_dir", default="./ur_mms_v6_final")
parser.add_argument("--text", default="یہ ایک مثال کی آڈیو فائل ہے۔")
parser.add_argument("--output", default="sample.wav")
args = parser.parse_args()

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

print(f"Loading model from {args.model_dir} ...")
tokenizer = VitsTokenizer.from_pretrained(args.model_dir)
model = VitsModel.from_pretrained(args.model_dir)
model.eval()

print(f"Synthesizing text...")
inputs = tokenizer(text=args.text, return_tensors="pt", padding=True)
with torch.no_grad():
    out = model(**inputs)
    wav = out.waveform.squeeze().cpu().numpy()

sf.write(args.output, wav, samplerate=16000)
print(f"Saved audio to {args.output}")
