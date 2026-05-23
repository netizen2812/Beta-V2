import os
import torch
import scipy.io.wavfile as wavfile
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts
from pathlib import Path

def generate_manual_verify_samples():
    print("--- GENERATING MANUAL VERIFICATION SAMPLES ---")

    # 1. Setup Paths
    MODEL_DIR  = "models/base_xtts"
    CONFIG_PATH = os.path.join(MODEL_DIR, "config.json")
    OUTPUT_DIR  = "data/verification_samples"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Canonical speaker references — must match CANONICAL_REFS in local_tts.py
    # and ANCHORS in tritower_tts.py.  Single source of truth for all conditioning.
    CANONICAL_REFS = {
        "en": "data/tts_dataset/en/wavs/en_0012.wav",
        "hi": "data/tts_dataset/ur/wavs/ur_0001.wav",   # XTTS routes Urdu through 'hi'
        "ar": "data/tts_dataset/ar/wavs/ar_0007.wav",
    }

    # Per-language inference params aligned with ANCHORS in tritower_tts.py
    PARAMS = {
        "en": {"temperature": 0.65, "repetition_penalty": 10.0, "top_p": 0.80},
        "hi": {"temperature": 0.55, "repetition_penalty": 10.0, "top_p": 0.80},
        "ar": {"temperature": 0.70, "repetition_penalty": 5.0,  "top_p": 0.80},
        # Arabic: rep_penalty 5.0 (not 10.0) — high penalty causes trembling artifact
    }

    # 2. Load Model
    config = XttsConfig()
    config.load_json(CONFIG_PATH)
    model = Xtts.init_from_config(config)
    print(f" > Loading Base Engine...")
    model.load_checkpoint(config, checkpoint_dir=MODEL_DIR, use_deepspeed=False)
    model.cuda()

    # 3. Generate Final Verification Set
    samples = [
        {"lang": "en", "text": "Assalamu Alaikum. This is the Maulana voice, speaking with a fluid and continuous scholarly tone, without any pauses."},
        {"lang": "hi", "text": "اسلام علیکم۔ مولانا کی آواز اب اردو میں بھی بالکل تیار ہے اور ہدایت کی راہ دکھا رہی ہے۔"},
        {"lang": "ar", "text": "السلام عليكم. صوت مولانا الآن جاهز باللغة العربية لنشر العلم والهدى."}
    ]

    for s in samples:
        lang     = s["lang"]
        text     = s["text"]
        ref_wav  = CANONICAL_REFS[lang]
        params   = PARAMS[lang]
        out_file = os.path.join(OUTPUT_DIR, f"maulana_verify_{lang}.wav")

        if not os.path.exists(ref_wav):
            print(f" ! Speaker ref not found: {ref_wav} — skipping {lang.upper()}")
            continue

        # Extract per-language conditioning latents from the correct native speaker
        print(f" > Extracting [{lang.upper()}] latents from: {ref_wav}")
        gpt_cond_latent, speaker_embedding = model.get_conditioning_latents(
            audio_path=[ref_wav]
        )

        print(f" > Synthesizing {lang.upper()}...")
        out = model.inference(
            text,
            lang,
            gpt_cond_latent,
            speaker_embedding,
            temperature=params["temperature"],
            length_penalty=1.0,
            repetition_penalty=params["repetition_penalty"],
            top_k=50,
            top_p=params["top_p"],
        )

        wav_data = out["wav"]
        if hasattr(wav_data, "cpu"):
            wav_data = wav_data.cpu().numpy()

        wavfile.write(out_file, 24000, wav_data)
        print(f"   -> READY: {out_file}")

    print("\n--- SAMPLES READY FOR MANUAL VERIFICATION ---")


if __name__ == "__main__":
    try:
        generate_manual_verify_samples()
    except Exception as e:
        print(f"ERROR: {e}")
