import os
import json
import numpy as np
import soundfile as sf
import librosa
from pathlib import Path
from services.local_tts import tts_engine

# Config
# Config
SCRIPT_DIR = Path(__file__).parent.absolute()
DATA_DIR = SCRIPT_DIR.parent / "data"
ASSET_ROOT = DATA_DIR / "assets"
MANIFEST_PATH = DATA_DIR / "asset_manifest.json"
TEMPLATES_PATH = DATA_DIR / "wisdom_templates.json"
TARGET_LUFS = -14.0
SAMPLE_RATE = 24000  # 24kHz Mono as requested

def load_templates():
    if not TEMPLATES_PATH.exists():
        print(f"❌ Error: {TEMPLATES_PATH} not found. Run generate_wisdom_library.py first.")
        return {}
    with open(TEMPLATES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def normalize_audio(file_path: Path):
    """Normalize audio to -14.0 LUFS (approximate using RMS)."""
    try:
        data, sr = librosa.load(str(file_path), sr=SAMPLE_RATE)
        rms = np.sqrt(np.mean(data**2))
        target_rms = 10**(TARGET_LUFS / 20)
        
        if rms > 0:
            gain = target_rms / rms
            data_norm = data * gain
            data_norm = np.clip(data_norm, -1.0, 1.0)
            sf.write(str(file_path), data_norm, SAMPLE_RATE)
            return True
    except Exception as e:
        print(f"Normalization error for {file_path}: {e}")
    return False

def generate_hierarchy():
    print("Starting Mass Hierarchical Maulana Brick Synthesis...")
    templates = load_templates()
    if not templates: return

    manifest = {}

    for node_path, texts in templates.items():
        # node_path is like 'en.reception.greetings.morning'
        parts = node_path.split('.')
        lang = parts[0]
        
        # Create directory structure
        dir_path = ASSET_ROOT.joinpath(*parts[:-1])
        dir_path.mkdir(parents=True, exist_ok=True)
        
        key = parts[-1]
        variations = []
        
        for i, text in enumerate(texts, 1):
            variant_id = f"{key}_{i}"
            file_name = f"{variant_id}.wav"
            file_path = dir_path / file_name
            
            if file_path.exists() and file_path.stat().st_size > 10240:
                print(f"Skipping {file_path.name} (already exists and valid)")
                variations.append(str(file_path.relative_to(ASSET_ROOT)).replace("\\", "/"))
                continue
            
            if file_path.exists():
                print(f"Overwriting stub/corrupted file: {file_path.name}")

            print(f"Synthesizing [{node_path}] Variation {i}...")
            
            # SCHOLARLY EXPANSION: Convert abbreviations to full phonetic speech
            import re
            processed_text = text.replace("(SWT)", "Subhanahu Wa Ta'ala")
            processed_text = processed_text.replace("(AS)", "Alayhis Salam")
            processed_text = processed_text.replace("(RA)", "Radiyallahu Anhu")
            processed_text = processed_text.replace("SWT", "Subhanahu Wa Ta'ala")
            
            # REMOVE PAUSE TRIGGERS: Strip commas and brackets for 'one-breath' flow
            processed_text = re.sub(r'[\*\(\)\[\],]', '', processed_text)
            processed_text = processed_text.replace("  ", " ").strip()

            success = tts_engine.synthesize(processed_text, lang, file_path)
            
            if success:
                normalize_audio(file_path)
                variations.append(str(file_path.relative_to(ASSET_ROOT)).replace("\\", "/"))
            
        manifest[node_path] = variations

    # Save manifest
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"DONE: Mass Synthesis Complete. Manifest saved to {MANIFEST_PATH}")

if __name__ == "__main__":
    generate_hierarchy()
