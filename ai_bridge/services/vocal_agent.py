"""
services/vocal_agent.py
Multi-Vocal Agent — orchestrates ElevenLabs vs GCP Studio switching.

Logic:
  • Literal Tarjumah (pre-recorded)  → GCP Chirp3/Studio (high-quality, low latency)
  • Contextual Live RAG chat          → ElevenLabs (streaming, expressive Maulana voice)
  • Locale routing:
      EN / UR / BN  → ElevenLabs Multilingual v3
      AR                  → GCP Studio ar-XA voice (native Arabic prosody)
      ML                  → GCP Studio ml-IN (Malayalam)
"""
import os
import logging
import httpx
from typing import AsyncIterator

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────
ELEVENLABS_API_KEY  = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "")
ELEVENLABS_TTS_URL  = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}/stream"

GCP_TTS_URL = "https://texttospeech.googleapis.com/v1/text:synthesize"
GCP_API_KEY = os.getenv("GCP_API_KEY", "")

# Locale → GCP voice name mapping (Chirp3 / Studio)
GCP_VOICE_MAP = {
    "ar": {"languageCode": "ar-XA", "name": "ar-XA-Studio-B",  "ssmlGender": "MALE"},
    "ml": {"languageCode": "ml-IN", "name": "ml-IN-Chirp3-HD-Achernar", "ssmlGender": "MALE"},
}

# Locales handled by ElevenLabs Multilingual v3
ELEVENLABS_LOCALES = {"en", "ur", "bn"}


# ── Static Assets ──────────────────────────────────────────────────────────────
import json
from pathlib import Path
import random

MANIFEST_PATH = Path("ai_bridge/data/asset_manifest.json")
ASSET_ROOT    = Path("ai_bridge/data/assets")
_asset_cache  = None

def _load_asset_manifest():
    global _asset_cache
    if _asset_cache is not None:
        return _asset_cache
    if MANIFEST_PATH.exists():
        try:
            with open(MANIFEST_PATH, "r") as f:
                _asset_cache = json.load(f)
                return _asset_cache
        except Exception as e:
            logger.error(f"Failed to load asset manifest: {e}")
    return {}

async def get_scholarly_feedback(key: str) -> bytes:
    """
    Retrieves a pre-recorded scholarly feedback audio (Zero-OPEX).
    Key format: 'en.reception.greetings.morning'
    """
    manifest = _load_asset_manifest()
    variants = manifest.get(key)
    if variants:
        # Pick a random variation to ensure variety
        variant_path = random.choice(variants)
        full_path = ASSET_ROOT / variant_path
        if full_path.exists():
            logger.info(f"Using static asset: {key} ({variant_path})")
            with open(full_path, "rb") as f:
                return f.read()
    
    logger.warning(f"Static asset not found for key: {key}")
    return b""


# ── Public interface ───────────────────────────────────────────────────────────
async def synthesize_tarjumah(text: str, locale: str) -> bytes:
    """
    Pre-recorded literal Tarjumah.
    Always uses GCP Studio for maximum audio fidelity.
    Falls back to ElevenLabs if GCP key is missing.
    """
    if locale in GCP_VOICE_MAP and GCP_API_KEY:
        return await _gcp_synthesize(text, locale)
    return await _elevenlabs_synthesize_bytes(text, locale)


async def stream_rag_response(text: str, locale: str) -> AsyncIterator[bytes]:
    """
    Streaming voice output for live RAG / Maulana chat responses.
    Uses the Zero-OPEX Local TTS Engine (fine-tuned XTTSv2).
    """
    from .local_tts import tts_engine
    import tempfile
    import asyncio
    from pathlib import Path
    
    # Ensure models are loaded
    if not tts_engine.is_loaded:
        tts_engine.load_models()
        
    try:
        lang = "en" if locale in ["en", "en-US", "en-GB"] else "ur" if locale in ["ur", "ur-PK", "ur-IN"] else "ar"
        
        MASTER_REFS = {
            "en": Path("ai_bridge/data/tts_dataset/wavs_en/en_0012.wav"),
            "ur": Path("ai_bridge/data/tts_dataset/wavs_ur/ur_0001.wav"),
            "ar": Path("ai_bridge/data/tts_dataset/wavs_ar/ar_0001.wav")
        }
        ref_path = MASTER_REFS.get(lang, MASTER_REFS["en"])
        speaker_wav = str(ref_path.absolute()) if ref_path.exists() else None
        
        if speaker_wav and getattr(tts_engine, "tts", None) and hasattr(tts_engine.tts, "tts_stream"):
            chunks = tts_engine.tts.tts_stream(text=text, speaker_wav=speaker_wav, language=lang)
            for chunk in chunks:
                if isinstance(chunk, torch.Tensor):
                    yield chunk.cpu().numpy().tobytes()
                else:
                    yield chunk
        else:
            # Fallback if tts_stream is not available
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                temp_path = Path(tmp.name)
            try:
                success = await asyncio.to_thread(tts_engine.synthesize, text, lang, temp_path)
                if success and temp_path.exists():
                    with open(temp_path, "rb") as f:
                        chunk = f.read(4096)
                        while chunk:
                            yield chunk
                            chunk = f.read(4096)
                else:
                    yield b""
            finally:
                if temp_path.exists():
                    try:
                        os.remove(temp_path)
                    except:
                        pass

    except Exception as e:
        logger.error(f"Local TTS streaming failed: {e}")
        yield b""



# ── ElevenLabs ─────────────────────────────────────────────────────────────────
async def _elevenlabs_stream(text: str) -> AsyncIterator[bytes]:
    headers = {
        "xi-api-key":   ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
        "Accept":       "audio/mpeg",
    }
    payload = {
        "text":       text,
        "model_id":   "eleven_turbo_v2_5",
        "voice_settings": {"stability": 0.55, "similarity_boost": 0.8, "style": 0.25},
    }
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            async with client.stream("POST", ELEVENLABS_TTS_URL, headers=headers, json=payload) as resp:
                if resp.status_code == 429:
                    logger.warning("ElevenLabs quota hit — falling back to text notification")
                    return
                resp.raise_for_status()
                async for chunk in resp.aiter_bytes(chunk_size=4096):
                    yield chunk
    except Exception as e:
        logger.error(f"ElevenLabs stream error: {e}")


async def _elevenlabs_synthesize_bytes(text: str, locale: str) -> bytes:
    chunks = []
    async for chunk in _elevenlabs_stream(text):
        chunks.append(chunk)
    return b"".join(chunks)


# ── GCP Studio / Chirp3 ────────────────────────────────────────────────────────
async def _gcp_synthesize(text: str, locale: str) -> bytes:
    voice = GCP_VOICE_MAP.get(locale, {"languageCode": "en-US", "name": "en-US-Studio-O", "ssmlGender": "MALE"})
    payload = {
        "input":       {"ssml": f'<speak><prosody rate="slow">{text}</prosody></speak>'},
        "voice":       voice,
        "audioConfig": {"audioEncoding": "MP3", "speakingRate": 0.9},
    }
    headers = {"X-Goog-Api-Key": GCP_API_KEY}
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(GCP_TTS_URL, headers=headers, json=payload)
            resp.raise_for_status()
            import base64
            return base64.b64decode(resp.json()["audioContent"])
    except Exception as e:
        logger.error(f"GCP TTS error: {e}")
        return b""


# ── Convenience ────────────────────────────────────────────────────────────────
def get_provider_for_locale(locale: str, mode: str = "rag") -> str:
    """Returns 'elevenlabs' or 'gcp' for logging and routing decisions."""
    if mode == "tarjumah" and locale in GCP_VOICE_MAP and GCP_API_KEY:
        return "gcp"
    if locale in ELEVENLABS_LOCALES and ELEVENLABS_API_KEY:
        return "elevenlabs"
    return "gcp"
