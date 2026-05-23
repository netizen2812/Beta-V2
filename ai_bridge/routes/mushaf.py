"""
routes/mushaf.py
WebSocket endpoint for real-time word-by-word Tajweed feedback.
Each audio chunk is processed through the spectral + phonetic engine
and the word results are pushed back to the client as JSON events.
"""
import asyncio
import json
import logging
import tempfile
import uuid
import os
from pathlib import Path
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)
router = APIRouter()

# Injected at startup via dependency (avoids circular import)
_phonetic_engine   = None
_phonetic_db       = None
_spectral_analyzer = None

def inject_engines(phonetic, phonetic_db, spectral):
    global _phonetic_engine, _phonetic_db, _spectral_analyzer
    _phonetic_engine   = phonetic
    _phonetic_db       = phonetic_db
    _spectral_analyzer = spectral


@router.websocket("/ws/mushaf/live")
async def live_recitation_ws(websocket: WebSocket):
    """
    WebSocket protocol:
      Client → sends binary audio chunks (PCM/WebM)
      Server ← sends JSON events:
        {"type": "word_result", "word_ar": "…", "status": "correct|error|pending", "score": 0.97}
        {"type": "session_done", "summary": {…}}
        {"type": "error", "message": "…"}
    """
    await websocket.accept()
    logger.info("Mushaf live WS connected")
    audio_buffer = bytearray()

    try:
        while True:
            message = await asyncio.wait_for(websocket.receive(), timeout=60)

            if "bytes" in message and message["bytes"]:
                # Accumulate audio data
                audio_buffer.extend(message["bytes"])

            elif "text" in message:
                data = json.loads(message["text"])
                cmd  = data.get("cmd")

                if cmd == "start":
                    audio_buffer = bytearray()
                    await websocket.send_json({"type": "ack", "msg": "Recording started"})

                elif cmd == "stop":
                    ayah_id  = data.get("ayah_id", "1:1")
                    lang     = data.get("language_code", "en")
                    results  = await _process_audio_buffer(bytes(audio_buffer), ayah_id, lang)
                    await websocket.send_json({"type": "session_done", "summary": results})
                    audio_buffer = bytearray()

                elif cmd == "ping":
                    await websocket.send_json({"type": "pong"})

    except asyncio.TimeoutError:
        logger.info("Mushaf WS timeout — closing")
        await websocket.close(code=1000)
    except WebSocketDisconnect:
        logger.info("Mushaf WS disconnected")
    except Exception as e:
        logger.error(f"Mushaf WS error: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass


async def _process_audio_buffer(audio_bytes: bytes, ayah_id: str, lang: str) -> dict:
    """Run the full IMAM engine pipeline on the buffered audio."""
    if not _phonetic_engine or not _phonetic_db:
        return {"error": "Engine not initialised"}

    # Write to temp file
    suffix = ".webm"
    tmp_path = Path(tempfile.gettempdir()) / f"ws_{uuid.uuid4().hex}{suffix}"
    try:
        tmp_path.write_bytes(audio_bytes)

        # Run phonetic transcription (single-pass)
        result = _phonetic_engine.transcribe_phonetics(tmp_path.read_bytes())
        actual_phonetics = result.get("words", [])

        # Fetch reference and score
        reference_words = _phonetic_db.search_by_ayah_id(ayah_id)
        if not reference_words:
            return {"error": f"No reference phonetics for ayah {ayah_id}"}
            
        from services.tajweed_scorer import TajweedScorer
        score_data = TajweedScorer.score_recitation(
            actual_phonetics=actual_phonetics,
            reference_words=reference_words,
        )
        
        # Inject Audio Playlist
        try:
            from services.audio_orchestrator import build_playlist
            import urllib.parse
            surah, verse = map(int, ayah_id.split(':'))
            lang_code = "ur" if "urdu" in lang.lower() else "ar" if "arabic" in lang.lower() else "en"
            
            insight_url = None
            if "word_results" in score_data:
                # Find first error to generate insight
                for w in score_data["word_results"]:
                    if w.get("status") == "error":
                        params = urllib.parse.urlencode({
                            "rule": w.get("rule", "Tajweed Error"),
                            "word": w.get("word_ar", ""),
                            "guidance": score_data.get("maulana_feedback", ""),
                            "language": lang
                        })
                        insight_url = f"/api/maulana-voice?{params}"
                        break
                        
            score_data["playlist"] = build_playlist(surah, verse, lang_code, insight_url)
        except Exception as e:
            logger.error(f"Playlist generation failed: {e}")
            score_data["playlist"] = []
            
        return score_data

    except Exception as e:
        logger.error(f"Audio processing error: {e}")
        return {"error": str(e)}
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass
