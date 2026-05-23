"""
generate_maulana_samples.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Mission: Generate top-3 market audio samples for the Maulana persona.
Auth:    ADC (Application Default Credentials) → falls back to REST API key.
Output:  ./golden_samples/{ayah_id}/{language}.mp3

Voice Matrix (Elite Tier 2026):
  Arabic  → ar-XA-Studio-B         (0.82x — Harakat & resonance)
  Urdu    → ur-PK-Chirp3-HD-Male  (0.88x — Scholarly Makhraj)
  English → en-GB-Neural2-B        (0.92x — British-academic mentor)
"""

import os
import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("MaulanaAudio")

# ── Output directory ───────────────────────────────────────────────────────────
OUTPUT_DIR = Path("./golden_samples")

# ── Test Data ─────────────────────────────────────────────────────────────────
AYAHS = [
    {
        "id": "1-1",
        "surah": "Al-Fatihah",
        "verse": 1,
        "focus": "Flow & Bismillah opening",
        "arabic": "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ",
        "urdu_context": "یہ آیت اللہ کے نام سے شروع کی جاتی ہے۔ 'رحمٰن' اور 'رحیم' میں 'ح' کی آواز واضح ہونی چاہیے۔",
        "english_context": "The Basmalah opens with Allah's names. The 'ḥ' in Ar-Raḥmān must be a deep pharyngeal fricative — not a simple 'h'.",
        "translations": {
            "ur": "اللہ کے نام سے جو بڑا مہربان نہایت رحم والا ہے۔",
            "en": "In the name of Allah, the Entirely Merciful, the Especially Merciful.",
        },
    },
    {
        "id": "112-1",
        "surah": "Al-Ikhlas",
        "verse": 1,
        "focus": "Qaf & Ha Makhraj precision",
        "arabic": "قُلْ هُوَ ٱللَّهُ أَحَدٌ",
        "urdu_context": "'قل' میں 'ق' گہرے حلق سے نکالیں۔ 'هو' میں 'ه' بھی واضح سانس کے ساتھ ادا کریں۔",
        "english_context": "The 'Qāf' (ق) in 'Qul' must emerge from deep in the throat — a uvular stop, not a 'k'. The 'Hā' (ه) in 'Huwa' requires a clear glottal aspiration.",
        "translations": {
            "ur": "کہہ دیجئے کہ وہ اللہ ایک ہے۔",
            "en": "Say, He is Allah, [who is] One.",
        },
    },
    {
        "id": "108-1",
        "surah": "Al-Kawthar",
        "verse": 1,
        "focus": "Madd & vowel stretching (2-6 counts)",
        "arabic": "إِنَّآ أَعْطَيْنَٰكَ ٱلْكَوْثَرَ",
        "urdu_context": "'إِنَّآ' میں مدّ لازم ہے — کم از کم چار حرکات تک آواز کھینچیں۔ 'ٱلْكَوْثَرَ' میں واؤ کو سکون دیں۔",
        "english_context": "The elongated 'aa' in 'Innaa' is Madd Lāzim — stretch it for a minimum of 4 counts (harakāt). The 'Kawthar' vowel on the 'wāw' should carry a clear rounding.",
        "translations": {
            "ur": "بے شک ہم نے آپ کو کوثر عطا کیا۔",
            "en": "Indeed, We have granted you Al-Kawthar.",
        },
    },
]

# ── Voice configs ──────────────────────────────────────────────────────────────
VOICE_CONFIGS = {
    "ar": {
        "language_code":  "ar-XA",
        "name":           "ar-XA-Wavenet-B",
        "speaking_rate":  0.82,
        "label":          "The Qari (Arabic Wavenet-B)",
    },
    "ur": {
        "language_code":  "ur-IN",
        "name":           "ur-IN-Wavenet-B",
        "speaking_rate":  0.88,
        "label":          "The Maulana (Urdu Wavenet-B)",
    },
    "en": {
        "language_code":  "en-GB",
        "name":           "en-GB-Neural2-B",
        "speaking_rate":  0.92,
        "label":          "The Mentor (English Neural2-B)",
    },
}


# ── RAG Context Tip (simulated for this prototype) ─────────────────────────────
def get_rag_context_tip(ayah: dict, lang: str) -> str:
    """
    In production: this calls the ChromaDB TafsirRAG pipeline.
    For this prototype: returns the curated scholarly tip embedded in test data.
    """
    if lang == "ur":
        return ayah["urdu_context"]
    if lang == "en":
        return ayah["english_context"]
    return ""  # Arabic: text alone carries the message


# ── Script builder ─────────────────────────────────────────────────────────────
def build_synthesis_text(ayah: dict, lang: str) -> str:
    """
    Construct the full SSML/text payload for TTS.
    Arabic: Arabic text only (native TTS handles prosody).
    Urdu / English: Translation + a scholarly Maulana context tip.
    """
    if lang == "ar":
        # Arabic — pure Quranic text with intentional silences via punctuation
        return ayah["arabic"]

    translation = ayah["translations"].get(lang, "")
    tip         = get_rag_context_tip(ayah, lang)
    surah_label = f"{ayah['surah']}, Verse {ayah['verse']}"

    if lang == "ur":
        return (
            f"{surah_label}۔\n\n"
            f"{translation}\n\n"
            f"مولانا کی نصیحت: {tip}"
        )
    else:  # en
        return (
            f"{surah_label}.\n\n"
            f"{translation}\n\n"
            f"Maulana's note: {tip}"
        )


# ── GCP TTS synthesis (ADC) ────────────────────────────────────────────────────
def synthesize_with_adc(text: str, voice_cfg: dict, output_path: Path) -> bool:
    """
    Use google-cloud-texttospeech (ADC auth).
    Returns True on success.
    """
    try:
        from google.cloud import texttospeech
        client = texttospeech.TextToSpeechClient()

        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(
            language_code=voice_cfg["language_code"],
            name=voice_cfg["name"],
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=voice_cfg["speaking_rate"],
            effects_profile_id=["headphone-class-device"],  # Studio-grade profile
        )

        log.info(f"  → GCP ADC: {voice_cfg['name']} @ {voice_cfg['speaking_rate']}x")
        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(response.audio_content)
        size_kb = len(response.audio_content) / 1024
        log.info(f"  ✅ Saved: {output_path} ({size_kb:.1f} KB)")
        return True

    except Exception as e:
        log.error(f"  ✗ ADC synthesis failed: {e}")
        return False


# ── Fallback: GCP REST API ─────────────────────────────────────────────────────
def synthesize_with_rest(text: str, voice_cfg: dict, output_path: Path, api_key: str) -> bool:
    """Fallback to GCP REST if ADC is unavailable."""
    import base64
    import urllib.request

    url     = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={api_key}"
    payload = json.dumps({
        "input":       {"text": text},
        "voice":       {"languageCode": voice_cfg["language_code"], "name": voice_cfg["name"]},
        "audioConfig": {
            "audioEncoding":      "MP3",
            "speakingRate":       voice_cfg["speaking_rate"],
            "effectsProfileId":   ["headphone-class-device"],
        },
    }).encode()

    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        log.info(f"  → REST API: {voice_cfg['name']} @ {voice_cfg['speaking_rate']}x")
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            audio = base64.b64decode(data["audioContent"])
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(audio)
            log.info(f"  ✅ Saved: {output_path} ({len(audio)/1024:.1f} KB)")
            return True
    except Exception as e:
        log.error(f"  ✗ REST synthesis failed: {e}")
        return False


# ── Main runner ────────────────────────────────────────────────────────────────
def main():
    log.info("=" * 64)
    log.info("  IMAM AI — Maulana Prototype: Top 3 Market Samples")
    log.info("=" * 64)

    gcp_api_key = os.getenv("GCP_API_KEY", "")
    results     = []

    for ayah in AYAHS:
        log.info(f"\n📖 {ayah['surah']} {ayah['verse']} (Focus: {ayah['focus']})")

        for lang, voice_cfg in VOICE_CONFIGS.items():
            out_path = OUTPUT_DIR / ayah["id"] / f"{lang}.mp3"
            text     = build_synthesis_text(ayah, lang)

            log.info(f"\n  [{lang.upper()}] {voice_cfg['label']}")
            log.info(f"  Text ({len(text)} chars): {text[:80]}…")

            # Try ADC first, then REST
            ok = synthesize_with_adc(text, voice_cfg, out_path)
            if not ok and gcp_api_key:
                ok = synthesize_with_rest(text, voice_cfg, out_path, gcp_api_key)

            results.append({
                "ayah":     f"{ayah['surah']} {ayah['verse']}",
                "lang":     lang,
                "voice":    voice_cfg["name"],
                "path":     str(out_path),
                "success":  ok,
                "focus":    ayah["focus"],
            })

    # ── Summary report ─────────────────────────────────────────────────────────
    log.info("\n" + "=" * 64)
    log.info("  GENERATION REPORT")
    log.info("=" * 64)
    success = [r for r in results if r["success"]]
    failed  = [r for r in results if not r["success"]]

    for r in results:
        status = "✅" if r["success"] else "❌"
        log.info(f"  {status} [{r['lang'].upper()}] {r['ayah']} → {r['path']}")

    log.info(f"\n  Total: {len(success)}/{len(results)} generated successfully")

    if failed:
        log.warning("\n  ⚠ Failed samples:")
        for r in failed:
            log.warning(f"    [{r['lang'].upper()}] {r['ayah']} — Check GCP credentials")
        log.warning("\n  AUTH FIX:")
        log.warning("    Option 1: gcloud auth application-default login")
        log.warning("    Option 2: Set GCP_API_KEY in .env")
        log.warning("    Option 3: Set GOOGLE_APPLICATION_CREDENTIALS to a service account JSON")

    # Save manifest
    manifest_path = OUTPUT_DIR / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps({
        "generated_at": datetime.utcnow().isoformat(),
        "samples":      results,
    }, indent=2))
    log.info(f"\n  📄 Manifest: {manifest_path}")
    log.info("=" * 64)

    return len(failed) == 0


if __name__ == "__main__":
    # Load .env
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=Path(".env"))
        log.info("Loaded .env")
    except ImportError:
        pass

    ok = main()
    exit(0 if ok else 1)
