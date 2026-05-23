"""
Tri-Tower Maulana TTS Engine
- Three dedicated language engines, each anchored to a native reference speaker
- Smart router: detects Arabic script in EN/UR text and fetches from AR engine
"""

import os
import re
import sys
import torch
import scipy.io.wavfile as wavfile
import numpy as np
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts
from transformers import VitsModel, VitsTokenizer

# Fix Windows console encoding for Urdu/Arabic script
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SAMPLE_RATE = 24000
MMS_SAMPLE_RATE = 16000
MODEL_DIR = "models/base_xtts"
MMS_URDU_DIR = "C:/Maulana_Training_Forge/mms_urdu_stable"
CONFIG_PATH = os.path.join(MODEL_DIR, "config.json")

# ── CANONICAL SPEAKER REFERENCES (must match local_tts.py CANONICAL_REFS) ────
# Aligned to the actual dataset structure built by extract_training_dataset.py
ANCHORS = {
    "en": {
        "ref": "data/tts_dataset/en/wavs/en_0012.wav",   # same as CANONICAL_REFS["en"]
        "lang": "en",
        "temp": 0.65,
        "rep_penalty": 10.0,
    },
    "ur": {
        "ref": "data/tts_dataset/ur/wavs/ur_0001.wav",   # same as CANONICAL_REFS["ur"]
        "lang": "hi",  # XTTS uses 'hi' pathway for Urdu
        "temp": 0.55,
        "rep_penalty": 10.0,
    },
    "ar": {
        "ref": "data/tts_dataset/ar/wavs/ar_0007.wav",   # same as CANONICAL_REFS["ar"]
        "lang": "ar",
        "temp": 0.70,
        "rep_penalty": 5.0,
    },
}


def is_arabic_text(text: str) -> bool:
    """Detect if a string contains Arabic/Quranic script."""
    arabic_pattern = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+')
    return bool(arabic_pattern.search(text))


def split_by_arabic(text: str):
    """
    Split text into segments: ('native', text) or ('arabic', text)
    Preserves order for later stitching.
    """
    arabic_pattern = re.compile(r'([\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF][^a-zA-Z\n]*)+')
    segments = []
    last_end = 0
    for match in arabic_pattern.finditer(text):
        start, end = match.span()
        if start > last_end:
            native = text[last_end:start].strip()
            if native:
                segments.append(("native", native))
        segments.append(("arabic", match.group().strip()))
        last_end = end
    if last_end < len(text):
        remainder = text[last_end:].strip()
        if remainder:
            segments.append(("native", remainder))
    return segments if segments else [("native", text)]


class TriTowerEngine:
    def __init__(self):
        print(" > Loading TriTower [XTTS Engines]...")
        config = XttsConfig()
        config.load_json(CONFIG_PATH)
        self.model = Xtts.init_from_config(config)
        self.model.load_checkpoint(config, checkpoint_dir=MODEL_DIR, use_deepspeed=False)
        self.model.cuda()

        print(" > Loading TriTower [Native Urdu MMS Engine]...")
        self.ur_tokenizer = VitsTokenizer.from_pretrained(MMS_URDU_DIR)
        self.ur_model = VitsModel.from_pretrained(MMS_URDU_DIR)
        self.ur_model.cuda()

        # Pre-compute XTTS latents
        self.latents = {}
        for lang_key, anchor in ANCHORS.items():
            print(f" > Extracting [{lang_key.upper()}] anchor: {anchor['ref']}")
            gpt_cond, speaker_emb = self.model.get_conditioning_latents(
                audio_path=[anchor["ref"]]
            )
            self.latents[lang_key] = (gpt_cond, speaker_emb)
        print(" > TriTower Engine is READY.")

    def _synthesize_urdu(self, text: str) -> np.ndarray:
        """Native MMS-Urdu Synthesis."""
        inputs = self.ur_tokenizer(text=text, return_tensors="pt").to("cuda")
        with torch.no_grad():
            output = self.ur_model(**inputs).waveform
        wav = output[0].cpu().numpy()
        # Resample from 16k to 24k to match XTTS if needed, 
        # but for verification we'll keep it native or simple resample
        import scipy.signal as signal
        secs = len(wav) / MMS_SAMPLE_RATE
        samps = int(secs * SAMPLE_RATE)
        return signal.resample(wav, samps)

    def _synthesize_xtts_segment(self, text: str, lang_key: str) -> np.ndarray:
        anchor = ANCHORS[lang_key]
        gpt_cond, speaker_emb = self.latents[lang_key]
        out = self.model.inference(
            text,
            anchor["lang"],
            gpt_cond,
            speaker_emb,
            temperature=anchor["temp"],
            length_penalty=1.0,
            repetition_penalty=anchor["rep_penalty"],
            top_k=50,
            top_p=0.8,
        )
        wav = out["wav"]
        if hasattr(wav, "cpu"):
            wav = wav.cpu().numpy()
        return wav

    def _normalize_audio(self, wav: np.ndarray) -> np.ndarray:
        """Ensure consistent loudness across all engines."""
        peak = np.abs(wav).max()
        if peak > 0:
            return wav / peak * 0.9  # Target -1dB peak
        return wav

    def synthesize(self, text: str, base_lang: str) -> np.ndarray:
        if base_lang == "ar":
            return self._normalize_audio(self._synthesize_xtts_segment(text, "ar"))
        
        if base_lang == "ur" and not is_arabic_text(text):
            return self._normalize_audio(self._synthesize_urdu(text))

        segments = split_by_arabic(text)

        if len(segments) == 1 and segments[0][0] == "native":
            return self._normalize_audio(self._synthesize_xtts_segment(text, base_lang))

        # Mixed: stitch native + arabic segments with Cross-Fading
        audio_parts = []
        fade_len = int(SAMPLE_RATE * 0.05) # 50ms cross-fade
        pause_len = int(SAMPLE_RATE * 0.15) # 150ms natural scholarly pause
        
        for i, (seg_type, seg_text) in enumerate(segments):
            if not seg_text:
                continue
            
            engine_key = "ar" if seg_type == "arabic" else base_lang
            print(f"   [{engine_key.upper()} engine] -> {seg_text[:30]}...")
            
            if engine_key == "ur":
                wav = self._synthesize_urdu(seg_text)
            else:
                wav = self._synthesize_xtts_segment(seg_text, engine_key)
            
            wav = self._normalize_audio(wav)
            
            # Apply 150ms natural pause between languages
            if i > 0:
                audio_parts.append(np.zeros(pause_len, dtype=np.float32))
            
            audio_parts.append(wav)

        return np.concatenate(audio_parts)


def run_verification():
    output_dir = "data/verification_tritower"
    os.makedirs(output_dir, exist_ok=True)

    engine = TriTowerEngine()

    test_cases = [
        {
            "id": "en_pure",
            "lang": "en",
            "text": "Assalamu Alaikum. This is the Maulana English voice. Seek knowledge, for it is a light that guides the believer.",
        },
        {
            "id": "ur_pure",
            "lang": "ur",
            "text": "اسلام علیکم۔ یہ مولانا کی اردو آواز ہے۔ علم حاصل کرنا ہر مسلمان پر فرض ہے۔",
        },
        {
            "id": "ar_pure",
            "lang": "ar",
            "text": "السلام عليكم. صوت مولانا العربي الآن جاهز. اقرأ باسم ربك الذي خلق.",
        },
        {
            "id": "en_with_arabic_citation",
            "lang": "en",
            "text": "The Prophet, peace be upon him, said: طَلَبُ الْعِلْمِ فَرِيضَةٌ عَلَى كُلِّ مُسْلِمٍ which means seeking knowledge is obligatory upon every Muslim.",
        },
    ]

    for case in test_cases:
        out_file = os.path.join(output_dir, f"maulana_{case['id']}.wav")
        print(f"\n > Generating [{case['id'].upper()}]...")
        wav = engine.synthesize(case["text"], case["lang"])
        wavfile.write(out_file, SAMPLE_RATE, wav)
        print(f"   -> READY: {out_file}")

    print("\n--- TRI-TOWER VERIFICATION COMPLETE ---")
    print(f" > Files saved to: {output_dir}")


if __name__ == "__main__":
    try:
        run_verification()
    except Exception as e:
        import traceback
        print(f"ERROR: {e}")
        traceback.print_exc()
