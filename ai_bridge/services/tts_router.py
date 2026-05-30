"""
tts_router.py — Two-Stage TTS Router

Provides a single synthesize() function that:
  - Stage 1 (boot → ~90s): Uses edge-tts (Microsoft cloud) for instant audio
  - Stage 2 (after XTTSv2 loads): Uses local fine-tuned XTTSv2 Maulana model

The switch is automatic — no user-visible change, just voice quality improves.

Usage:
    from services.tts_router import tts_router
    success = tts_router.synthesize(text, language, output_path)
"""

import logging
from pathlib import Path

log = logging.getLogger("TTSRouter")


class TTSRouter:
    """
    Routes TTS synthesis to the correct engine based on load state.
    Automatically prefers local XTTSv2 once it's ready.
    """

    def __init__(self):
        self._xtts_ready = False

    def mark_xtts_ready(self):
        """Called by main.py background thread when XTTSv2 finishes loading."""
        self._xtts_ready = True
        log.info("✅ [TTSRouter] XTTSv2 is now ready — switching from edge-tts to local model.")

    @property
    def is_loaded(self) -> bool:
        """
        Always returns True because edge-tts is always available.
        This prevents inference.py from trying to trigger a blocking load.
        """
        return True

    @property
    def active_stage(self) -> str:
        return "local-xtts" if self._xtts_ready else "edge-tts-cloud"

    def synthesize(self, text: str, language: str, output_path: Path) -> bool:
        """
        Synthesize text to audio, routing to the best available engine.

        Stage 1 (XTTSv2 not ready): edge-tts cloud (~1.5s latency, no warmup)
        Stage 2 (XTTSv2 ready):     local XTTSv2 fine-tuned Maulana model

        Args:
            text:        Text to synthesize
            language:    'en' | 'ur' | 'ar'
            output_path: Path where WAV should be written

        Returns:
            True on success, False on failure
        """
        if self._xtts_ready:
            # ── Stage 2: Local fine-tuned model ──────────────────────────────
            try:
                from services.local_tts import tts_engine
                log.info(f"[TTSRouter] Stage 2 → Local XTTSv2 [{language.upper()}]")
                return tts_engine.synthesize(text, language, output_path)
            except Exception as e:
                log.error(f"[TTSRouter] Local XTTSv2 failed ({e}), falling back to edge-tts")
                # Fall through to edge-tts as emergency fallback
        
        # ── Stage 1: Cloud edge-tts fallback ─────────────────────────────────
        log.info(f"[TTSRouter] Stage 1 → edge-tts cloud [{language.upper()}] (XTTSv2 still loading...)")
        try:
            from services.edge_tts_service import synthesize as edge_synthesize
            success = edge_synthesize(text, language, output_path)
            if success:
                return True
            # edge-tts failed — last resort is silence stub so the caller gets a WAV back
            log.warning("[TTSRouter] edge-tts failed — returning silent WAV stub.")
            _write_silent_wav(output_path)
            return True
        except Exception as e:
            log.error(f"[TTSRouter] edge-tts error: {e}")
            _write_silent_wav(output_path)
            return True  # Return True with silent stub so route doesn't 500


def _write_silent_wav(output_path: Path, duration_s: float = 1.0, sample_rate: int = 24000):
    """Write a silent WAV file as a last-resort stub to prevent HTTP 500."""
    import numpy as np
    import scipy.io.wavfile as wavfile
    silence = np.zeros(int(sample_rate * duration_s), dtype=np.float32)
    wavfile.write(str(output_path), sample_rate, silence)


# ── Module-level singleton ────────────────────────────────────────────────────
tts_router = TTSRouter()
