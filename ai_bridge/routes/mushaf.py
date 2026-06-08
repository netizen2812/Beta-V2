"""
routes/mushaf.py
WebSocket endpoint for smart real-time Tajweed feedback.

Protocol:
  Client → {cmd: "start", ayah_ids: ["1:1", "1:2", ...]}  — begin session
  Client → binary audio chunk (PCM/WebM, ~500ms each)      — stream audio
  Client → {cmd: "stop"}                                    — finish

  Server → {type: "ack", msg: "..."}
  Server → {type: "word_live", ayah_id, word_index, status: "correct|error"}
           Emitted only when a REAL phonetic match is detected in the chunk.
           Nothing is sent for unmatched audio (gibberish/English/silence).
  Server → {type: "gibberish_warn"}
           Sent after 3+ consecutive chunks produce zero matches.
  Server → {type: "session_done", results: [{ayah_id, score, word_results, not_quran}]}
  Server → {type: "error", message: "..."}
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

# Serialises all Wav2Vec2 chunk-decode calls across concurrent WS sessions.
# Using a Semaphore(1) means only one chunk is decoded at a time — any session
# whose chunk arrives while the semaphore is held simply skips that chunk
# (the next chunk will pick up). This prevents CPU thrash without blocking users.
_ws_decode_sem: asyncio.Semaphore | None = None

def inject_engines(phonetic, phonetic_db, spectral):
    global _phonetic_engine, _phonetic_db, _spectral_analyzer, _ws_decode_sem
    _phonetic_engine   = phonetic
    _phonetic_db       = phonetic_db
    _spectral_analyzer = spectral
    _ws_decode_sem     = asyncio.Semaphore(1)


# ── Constants ──────────────────────────────────────────────────────────────────
CHUNK_MATCH_THRESHOLD = 0.30   # minimum similarity for a live word hit
GIBBERISH_WARN_AFTER  = 3      # consecutive empty-match chunks before warning
MIN_CHUNK_BYTES       = 8_000  # ~500ms at 128kbps — skip tiny artefacts
SILENCE_RMS_THRESHOLD = 180    # int16 RMS floor — below this is silence/noise


# ── Helper: decode a raw audio chunk to phonetic word list ────────────────────
def _decode_chunk_sync(audio_bytes: bytes) -> list[str]:
    """
    Run Wav2Vec2 phonetic decode on a single audio chunk.
    Returns list of phonetic word strings.
    Runs synchronously (called via run_in_executor).
    """
    if not _phonetic_engine or not _phonetic_engine.is_loaded:
        return []
    try:
        from services.voice_processor import VoiceProcessor
        audio_array = VoiceProcessor.process_audio(audio_bytes, 16000)
        import numpy as np
        if len(audio_array) == 0 or np.max(np.abs(audio_array)) < 1e-4:
            return []
        result = _phonetic_engine.transcribe_phonetics(audio_bytes)
        return result.get("words", [])
    except Exception as e:
        logger.debug(f"[chunk-decode] error: {e}")
        return []


def _is_silence(raw_bytes: bytes) -> bool:
    """
    Fast RMS energy check on the last 4 KB of raw bytes.
    Returns True if the chunk is below the silence threshold — avoids
    queuing a Wav2Vec2 executor job for silent gaps between words.
    """
    import numpy as np
    tail = raw_bytes[-4096:] if len(raw_bytes) > 4096 else raw_bytes
    # Treat as raw int16 PCM — good enough for a floor check
    try:
        arr = np.frombuffer(tail, dtype=np.uint8).astype(np.float32) - 128.0
        rms = float(np.sqrt(np.mean(arr ** 2)))
        return rms < SILENCE_RMS_THRESHOLD
    except Exception:
        return False


# ── Helper: try to match chunk phonetics against reference words at cursor ─────
def _match_chunk(
    chunk_words: list[str],
    ref_words: list[dict],
    cursor: int,
    window: int = 4,
) -> list[tuple[int, float]]:
    """
    Try to find matches between the chunk's decoded words and reference words
    in the window [cursor, cursor+window). Only returns matches with sim > threshold.

    Returns list of (ref_word_index, similarity) sorted by ref_word_index.
    """
    from services.tajweed_scorer import TajweedScorer
    matches = []
    for chunk_word in chunk_words:
        best_sim = 0.0
        best_idx = -1
        for ri in range(cursor, min(cursor + window, len(ref_words))):
            sim = TajweedScorer.weighted_similarity(chunk_word, ref_words[ri]["word_tr"])
            if sim > best_sim:
                best_sim = sim
                best_idx = ri
        if best_idx != -1 and best_sim >= CHUNK_MATCH_THRESHOLD:
            matches.append((best_idx, best_sim))
    # Deduplicate — keep highest similarity per ref index
    seen = {}
    for idx, sim in matches:
        if idx not in seen or sim > seen[idx]:
            seen[idx] = sim
    return sorted(seen.items())


@router.websocket("/ws/mushaf/live")
async def live_recitation_ws(websocket: WebSocket):
    await websocket.accept()
    logger.info("Mushaf live WS connected")

    # ── Session state ──
    ayah_ids: list[str] = []
    # Flat list of all reference words across ayahs, each entry has ayah_id + word data
    all_ref_words: list[dict] = []
    # Cursor: index into all_ref_words of the next EXPECTED word
    cursor: int = 0
    # Per-word status cache for final report
    word_statuses: dict[int, str] = {}   # ref_word_flat_index → "correct" | "error"
    word_sims: dict[int, float] = {}

    # Accumulate all audio for final full-pipeline pass
    full_audio: bytearray = bytearray()
    # Chunk audio for live decode
    pending_chunk: bytearray = bytearray()

    empty_streak: int = 0          # consecutive chunks with zero matches
    session_active: bool = False

    loop = asyncio.get_event_loop()

    try:
        while True:
            message = await asyncio.wait_for(websocket.receive(), timeout=90)

            # ── Binary audio chunk ──────────────────────────────────────────
            if "bytes" in message and message["bytes"]:
                chunk = message["bytes"]
                full_audio.extend(chunk)
                pending_chunk.extend(chunk)

                if not session_active or not all_ref_words:
                    continue

                # Only process chunks large enough to be meaningful
                if len(pending_chunk) < MIN_CHUNK_BYTES:
                    continue

                chunk_bytes = bytes(pending_chunk)
                pending_chunk = bytearray()

                # Fast silence gate — skip executor job entirely for silent gaps
                if _is_silence(chunk_bytes):
                    continue

                # Semaphore: skip this chunk if another is already decoding.
                # The next chunk will pick up — no blocking, no CPU thrash.
                if _ws_decode_sem and _ws_decode_sem.locked():
                    logger.debug("[ws-chunk] semaphore busy — skipping chunk")
                    continue

                # Decode in executor (non-blocking)
                if _ws_decode_sem:
                    async with _ws_decode_sem:
                        chunk_words = await loop.run_in_executor(
                            None, _decode_chunk_sync, chunk_bytes
                        )
                else:
                    chunk_words = await loop.run_in_executor(
                        None, _decode_chunk_sync, chunk_bytes
                    )

                if not chunk_words:
                    empty_streak += 1
                    if empty_streak >= GIBBERISH_WARN_AFTER:
                        await websocket.send_json({"type": "gibberish_warn"})
                        empty_streak = 0
                    continue

                # Try to match against reference window
                matches = _match_chunk(chunk_words, all_ref_words, cursor, window=5)

                if not matches:
                    empty_streak += 1
                    if empty_streak >= GIBBERISH_WARN_AFTER:
                        await websocket.send_json({"type": "gibberish_warn"})
                        empty_streak = 0
                    continue

                empty_streak = 0

                # Emit live word hits and advance cursor
                for ref_idx, sim in matches:
                    if ref_idx < cursor:
                        continue  # already past this word
                    ref = all_ref_words[ref_idx]
                    status = "correct" if sim >= 0.95 else "error"
                    word_statuses[ref_idx] = status
                    word_sims[ref_idx] = sim
                    await websocket.send_json({
                        "type": "word_live",
                        "ayah_id": ref["ayah_id"],
                        "word_index": ref["word_index"],
                        "flat_index": ref_idx,
                        "status": status,
                        "score": round(sim * 100),
                    })

                # Advance cursor to one past the highest matched index
                max_matched = max(ri for ri, _ in matches)
                cursor = max_matched + 1

            # ── Text command ────────────────────────────────────────────────
            elif "text" in message:
                data = json.loads(message["text"])
                cmd = data.get("cmd")

                if cmd == "start":
                    # Reset session
                    ayah_ids = data.get("ayah_ids", ["1:1"])
                    full_audio = bytearray()
                    pending_chunk = bytearray()
                    cursor = 0
                    word_statuses = {}
                    word_sims = {}
                    empty_streak = 0
                    session_active = True

                    # Build flat reference word list
                    all_ref_words = []
                    for aid in ayah_ids:
                        ref = _phonetic_db.search_by_ayah_id(aid) if _phonetic_db else None
                        if ref:
                            for w in ref:
                                all_ref_words.append({**w, "ayah_id": aid})

                    await websocket.send_json({
                        "type": "ack",
                        "msg": f"Session started — {len(all_ref_words)} reference words across {len(ayah_ids)} ayah(s)",
                    })

                elif cmd == "stop":
                    session_active = False
                    # Run full pipeline on accumulated audio for each ayah
                    results = await _run_full_pipeline(
                        bytes(full_audio), ayah_ids, word_statuses, word_sims, loop
                    )
                    await websocket.send_json({"type": "session_done", "results": results})
                    # Reset for potential next session
                    full_audio = bytearray()
                    cursor = 0
                    word_statuses = {}
                    word_sims = {}

                elif cmd == "ping":
                    await websocket.send_json({"type": "pong"})

    except asyncio.TimeoutError:
        logger.info("Mushaf WS timeout — closing")
        await websocket.close(code=1000)
    except WebSocketDisconnect:
        logger.info("Mushaf WS disconnected")
    except Exception as e:
        logger.error(f"Mushaf WS error: {e}", exc_info=True)
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass


# ── Full pipeline after stop ───────────────────────────────────────────────────
async def _run_full_pipeline(
    audio_bytes: bytes,
    ayah_ids: list[str],
    live_statuses: dict[int, str],
    live_sims: dict[int, float],
    loop: asyncio.AbstractEventLoop,
) -> list[dict]:
    """
    Run the complete IMAM pipeline (Wav2Vec2 + TajweedScorer) on the full
    accumulated audio, split into per-ayah segments for accurate scoring.

    Because we can't perfectly timestamp each ayah boundary from the audio,
    we run the full pipeline once (as if it were one long ayah) and then
    re-partition the results back by ayah_id using the flat reference list.
    """
    if not _phonetic_engine or not _phonetic_db:
        return [{"ayah_id": aid, "error": "Engine not initialised"} for aid in ayah_ids]

    results = []

    # Run the combined audio through the phonetic pipeline once
    def _pipeline_sync():
        from services.voice_processor import VoiceProcessor
        from services.tajweed_scorer import TajweedScorer
        import numpy as np

        try:
            audio_array = VoiceProcessor.process_audio(audio_bytes, 16000)
            if len(audio_array) == 0 or np.max(np.abs(audio_array)) < 1e-4:
                return None, None  # silent

            result = _phonetic_engine.transcribe_phonetics(audio_bytes)
            actual_phonetics = result.get("words", [])
            return actual_phonetics, audio_array
        except Exception as e:
            logger.error(f"[full-pipeline] error: {e}")
            return None, None

    actual_phonetics, _ = await loop.run_in_executor(None, _pipeline_sync)

    if actual_phonetics is None:
        return [{
            "ayah_id": aid,
            "tajweed_score": 0,
            "not_quran": True,
            "maulana_feedback": {"guidance": "Could not decode audio."},
            "word_results": [],
        } for aid in ayah_ids]

    # Score each ayah independently against its reference slice
    from services.tajweed_scorer import TajweedScorer

    # Build flat offset map
    flat_offset = 0
    for aid in ayah_ids:
        ref_words = _phonetic_db.search_by_ayah_id(aid)
        if not ref_words:
            results.append({"ayah_id": aid, "error": "No reference", "tajweed_score": 0, "word_results": []})
            flat_offset += 0
            continue

        def _score_ayah(ph=actual_phonetics, rw=ref_words):
            return TajweedScorer.score_recitation(
                actual_phonetics=ph,
                reference_words=rw,
            )

        report = await loop.run_in_executor(None, _score_ayah)

        not_quran = report.get("status") == "not_quran"
        results.append({
            "ayah_id": aid,
            "tajweed_score": report.get("tajweed_score", 0),
            "not_quran": not_quran,
            "maulana_feedback": report.get("maulana_feedback", {}),
            "word_results": report.get("word_results", []),
            "correct_words": report.get("maulana_feedback", {}).get("summary", {}).get("correct", 0),
            "total_words": len(ref_words),
        })
        flat_offset += len(ref_words)

    return results
