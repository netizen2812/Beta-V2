"""
edge_tts_service.py — Microsoft edge-tts cloud fallback.

Serves audio IMMEDIATELY at boot (zero model load) while the local
XTTSv2 model loads in the background. Auto-replaced by tts_router.py
once XTTSv2 is ready.

Voice mapping (professional, natural-sounding):
  en → en-US-GuyNeural      (clear, professional male)
  ur → ur-PK-AsadNeural     (Urdu male)
  ar → ar-SA-HamedNeural    (Arabic male)
"""

import asyncio
import logging
import tempfile
from pathlib import Path

log = logging.getLogger("EdgeTTS")

# Voice mapping for each supported language
EDGE_VOICES = {
    "en": "en-US-GuyNeural",
    "ur": "ur-PK-AsadNeural",
    "ar": "ar-SA-HamedNeural",
}


def synthesize(text: str, language: str, output_path: Path) -> bool:
    """
    Synthesize text using Microsoft edge-tts cloud engine.
    Matches the same interface as LocalTTSEngine.synthesize().

    Args:
        text:        The text to synthesize
        language:    'en' | 'ur' | 'ar'
        output_path: Path object where the WAV file should be written

    Returns:
        True on success, False on failure
    """
    try:
        import edge_tts  # noqa: F401 — confirmed at import time
    except ImportError:
        log.error("edge-tts package not installed. Run: pip install edge-tts")
        return False

    voice = EDGE_VOICES.get(language, EDGE_VOICES["en"])
    log.info(f"[EdgeTTS] Synthesizing [{language.upper()}] via {voice} (~1.5s latency)...")

    try:
        # edge-tts is async — run it in a new event loop from this sync context
        async def _synthesize_async():
            import edge_tts
            communicate = edge_tts.Communicate(text, voice)
            # edge-tts saves MP3 by default — we need WAV for compatibility
            # Save to temp mp3 then convert, OR use the audio/mpeg output and
            # let the streaming route pass it through directly as audio/mpeg
            mp3_path = Path(str(output_path).replace(".wav", ".mp3"))
            await communicate.save(str(mp3_path))
            return mp3_path

        mp3_path = asyncio.run(_synthesize_async())

        # Convert MP3 → WAV using pydub (already installed via TTS deps) or scipy
        try:
            import subprocess
            # Use ffmpeg (available in the Docker image via coqui-tts)
            result = subprocess.run(
                ["ffmpeg", "-y", "-i", str(mp3_path), "-ar", "24000", "-ac", "1", str(output_path)],
                capture_output=True,
                timeout=15
            )
            mp3_path.unlink(missing_ok=True)  # Clean up MP3
            if result.returncode != 0:
                log.error(f"ffmpeg conversion failed: {result.stderr.decode()}")
                return False
        except Exception as conv_err:
            log.error(f"MP3→WAV conversion failed: {conv_err}")
            mp3_path.unlink(missing_ok=True)
            return False

        log.info(f"[EdgeTTS] ✅ Synthesis complete → {output_path.name}")
        return True

    except Exception as e:
        log.error(f"[EdgeTTS] Synthesis failed: {e}")
        return False
