"""
FastAPI Inference Routes — API endpoints for the AI Bridge.

Endpoints:
  POST /api/transcribe              — Whisper ASR (audio → Arabic text)
  POST /api/phonetics               — Wav2Vec2 (audio → phonetic string)
  POST /api/tajweed-check           — Full pipeline (audio + ayah_id → Tajweed Report)
  GET  /api/phonetic-ref/{id}       — Reference phonetics for an ayah
  POST /api/tafsir-query            — Semantic search over tafsir
  POST /api/maulana-voice           — Gemini advice + ElevenLabs voice stream
"""

import time
import logging
import os
import tempfile
from fastapi import APIRouter, UploadFile, File, Form, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

from services.tajweed_scorer import TajweedScorer
from services.alignment import AlignmentEngine
from services.maulana_voice import get_maulana_advice
from services.spectral_analyzer import QALQALAH_LETTERS_TR, QALQALAH_LETTERS_AR

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_AUDIO_BYTES = 10 * 1024 * 1024  # 10 MB limit


# ─── Request / Response Models ────────────────────────────────────────────────

class TafsirQueryRequest(BaseModel):
    query: str
    ayah_id: str | None = None
    n_results: int = 5


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/transcribe")
async def transcribe(request: Request, audio_file: UploadFile = File(...)):
    """
    Whisper-only transcription: audio → Arabic Quranic text.
    """
    whisper = request.app.state.whisper
    if not whisper or not whisper.is_loaded:
        raise HTTPException(503, "Whisper model not loaded")

    audio_bytes = await audio_file.read(MAX_AUDIO_BYTES + 1)
    if len(audio_bytes) > MAX_AUDIO_BYTES:
        raise HTTPException(413, "Audio file exceeds 10 MB limit")

    start = time.time()
    result = whisper.transcribe(audio_bytes, mime_type=audio_file.content_type or "audio/webm")
    elapsed = time.time() - start

    return {
        "status": "success",
        "data": {
            "text": result["text"],
            "chunks": result.get("chunks", []),
            "inference_time_ms": round(elapsed * 1000, 1),
        },
    }


@router.post("/phonetics")
async def phonetics(request: Request, audio_file: UploadFile = File(...)):
    """
    Wav2Vec2-only phonetic transcription: audio → phonetic string.
    """
    phonetic_engine = request.app.state.phonetic
    if not phonetic_engine or not phonetic_engine.is_loaded:
        raise HTTPException(503, "Phonetic model not loaded")

    audio_bytes = await audio_file.read(MAX_AUDIO_BYTES + 1)
    if len(audio_bytes) > MAX_AUDIO_BYTES:
        raise HTTPException(413, "Audio file exceeds 10 MB limit")

    start = time.time()
    result = phonetic_engine.transcribe_phonetics(audio_bytes)
    elapsed = time.time() - start

    return {
        "status": "success",
        "data": {
            "phonetics": result["phonetics"],
            "words": result["words"],
            "inference_time_ms": round(elapsed * 1000, 1),
        },
    }


@router.post("/tajweed-check")
async def tajweed_check(
    request: Request,
    audio_file: UploadFile = File(...),
    ayah_id: str = Form(...),
    madhab: str = Form("shafi"),
):
    """
    Full Tajweed validation pipeline:
      1. Whisper ASR → Arabic text (ayah identification)
      2. Wav2Vec2 → Phonetic transcription
      3. Phonetic DB → Reference phonetics
      4. Levenshtein scoring → Word-level Tajweed report

    Returns a complete Tajweed Report with per-word scores.
    """
    whisper = request.app.state.whisper
    phonetic_engine = request.app.state.phonetic
    phonetic_db = request.app.state.phonetic_db

    if not whisper or not whisper.is_loaded:
        raise HTTPException(503, "Whisper model not loaded")
    if not phonetic_engine or not phonetic_engine.is_loaded:
        raise HTTPException(503, "Phonetic model not loaded")
    if not phonetic_db or not phonetic_db.is_loaded:
        raise HTTPException(503, "Phonetic reference DB not loaded")

    audio_bytes = await audio_file.read(MAX_AUDIO_BYTES + 1)
    if len(audio_bytes) > MAX_AUDIO_BYTES:
        raise HTTPException(413, "Audio file exceeds 10 MB limit")

    start = time.time()

    # Step 3: Get reference phonetics from Buraaq DB
    reference_words = phonetic_db.search_by_ayah_id(ayah_id)
    if not reference_words:
        raise HTTPException(404, f"No phonetic reference found for ayah {ayah_id}")

    # Step 1 & 2: Concurrently run Whisper ASR and Wav2Vec2 CTC logits extraction to minimize latency
    import asyncio
    
    async def run_whisper_parallel():
        return await asyncio.to_thread(
            whisper.transcribe,
            audio_bytes,
            mime_type=audio_file.content_type or "audio/webm"
        )
        
    async def run_phonetics_parallel():
        return await asyncio.to_thread(
            phonetic_engine.get_ctc_logits,
            audio_bytes
        )
        
    whisper_task = asyncio.create_task(run_whisper_parallel())
    phonetics_task = asyncio.create_task(run_phonetics_parallel())
    
    whisper_result, (logits, audio_length) = await asyncio.gather(whisper_task, phonetics_task)
    transcribed_text = whisper_result["text"]

    # Guard against completely empty/silent or untranscribable recitation (P2.12)
    if not transcribed_text:
        elapsed = time.time() - start
        return {
            "status": "success",
            "data": {
                "maulana_feedback": {
                    "status": "Correction Required (Niqis)",
                    "score": 0.0,
                    "guidance": "Silence or untranscribable audio detected. Please speak clearly near the microphone.",
                    "summary": {"correct": 0, "minor_error": 0, "major_error": len(reference_words)}
                },
                "tajweed_score": 0.0,
                "total_words": len(reference_words),
                "correct_words": 0,
                "error_summary": {"correct": 0, "minor_error": 0, "major_error": len(reference_words)},
                "ayah_id": ayah_id,
                "madhab": madhab,
                "transcribed_text": "",
                "phonetic_transcript": "",
                "word_results": [
                    {
                        "word_index": ref["word_index"],
                        "word_ar": ref["word_ar"],
                        "expected_phonetic": ref["word_tr"],
                        "actual_phonetic": "",
                        "similarity": 0.0,
                        "status": "major_error",
                        "rule": "Missing Word",
                        "guidance": "No recitation detected for this word.",
                        "error_details": {
                            "error_type": "tongue_lisani",
                            "pedagogical_key": "pedagogy.correction.makharij.tongue_lisani",
                            "description": "No audio signal detected"
                        }
                    }
                    for ref in reference_words
                ],
                "inference_time_ms": round(elapsed * 1000, 1),
            },
        }

    # Step 4: Decode Wav2Vec2 phonetics
    phonetic_result = phonetic_engine.decode_logits(logits)
    actual_phonetics = phonetic_result["words"]

    # Step 4: Forced alignment
    aligned_words = AlignmentEngine.align_words(
        logits, audio_length, phonetic_engine.processor
    )

    # Step 5: Tajweed scoring with Maulana Grade Logic
    # We now integrate temporal and spectral feedback
    merged_feedback = {}
    
    # 5a. Temporal Feedback (Madd/Ghunnah)
    if request.app.state.temporal_engine:
        user_word_timings = [
            {"word_index": i, "duration": w["end_time"] - w["start_time"]} 
            for i, w in enumerate(aligned_words)
        ]
        temp_feedback = request.app.state.temporal_engine.validate_durations(ayah_id, user_word_timings)
        for tf in temp_feedback:
            if tf.get("error"):
                w_idx = tf["word_index"]
                merged_feedback[w_idx] = tf

    # 5b. Spectral Feedback (Qalqalah)
    if request.app.state.spectral_analyzer:
        # Save temp audio for analysis using thread-safe NamedTemporaryFile (P0.2)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            temp_audio_path = tmp.name
            
        # Identify words that SHOULD have Qalqalah (P1.6)
        segment_times = []
        for i, word in enumerate(reference_words):
            if i >= len(aligned_words): continue
            
            is_qal = any(l in word["word_tr"].lower() for l in QALQALAH_LETTERS_TR) or \
                     any(l in word["word_ar"] for l in QALQALAH_LETTERS_AR)
            
            segment_times.append({
                "word_index": i,
                "start": aligned_words[i]["start_time"],
                "end": aligned_words[i]["end_time"],
                "is_qalqalah": is_qal
            })
            
        spectral_feedback = request.app.state.spectral_analyzer.detect_qalqalah(temp_audio_path, segment_times)
        for sf in spectral_feedback:
            if sf.get("error"):
                w_idx = sf["word_index"]
                if w_idx in merged_feedback:
                    # Combine errors if a word has both timing and spectral errors
                    existing = merged_feedback[w_idx]
                    existing["rule"] = f"{existing['rule']} & {sf['rule']}"
                    existing["guidance"] = f"{existing['guidance']} Also, {sf['guidance'].lower()}"
                else:
                    merged_feedback[w_idx] = sf
        
        # Cleanup
        try: os.remove(temp_audio_path)
        except: pass

    # Step 6: Generate Final Maulana Feedback
    report = TajweedScorer.score_recitation(
        actual_phonetics=actual_phonetics, 
        reference_words=reference_words,
        temporal_feedback=merged_feedback # Merged feedback dict
    )

    elapsed = time.time() - start

    return {
        "status": "success",
        "data": {
            "maulana_feedback": report["maulana_feedback"],
            "tajweed_score": report["tajweed_score"],
            "total_words": len(reference_words),
            "correct_words": report["maulana_feedback"]["summary"].get("correct", 0),
            "error_summary": report["maulana_feedback"]["summary"],
            "ayah_id": ayah_id,
            "madhab": madhab,
            "transcribed_text": transcribed_text,
            "phonetic_transcript": phonetic_result["phonetics"],
            "word_results": report["word_results"],
            "inference_time_ms": round(elapsed * 1000, 1),
        },
    }


@router.get("/phonetic-ref/{ayah_id}")
async def get_phonetic_ref(request: Request, ayah_id: str):
    """
    Get reference phonetics for a specific ayah.
    ayah_id format: "surah:ayah" (e.g., "1:1")
    """
    phonetic_db = request.app.state.phonetic_db
    if not phonetic_db or not phonetic_db.is_loaded:
        raise HTTPException(503, "Phonetic DB not loaded")

    words = phonetic_db.search_by_ayah_id(ayah_id)
    if not words:
        raise HTTPException(404, f"No phonetic data for ayah {ayah_id}")

    phonetic_string = " ".join(w["word_tr"] for w in words)

    return {
        "status": "success",
        "data": {
            "ayah_id": ayah_id,
            "phonetic_string": phonetic_string,
            "words": words,
            "word_count": len(words),
        },
    }


@router.post("/tafsir-query")
async def tafsir_query(request: Request, body: TafsirQueryRequest):
    """
    Semantic search over the indexed tafsir collection.
    Retrieves the most relevant scholarly interpretations.
    """
    tafsir_rag = request.app.state.tafsir_rag
    if not tafsir_rag or not tafsir_rag.is_loaded:
        raise HTTPException(503, "Tafsir RAG not initialized")

    results = tafsir_rag.query(
        text=body.query,
        ayah_id=body.ayah_id,
        n_results=body.n_results,
    )

    return {
        "status": "success",
        "data": {
            "query": body.query,
            "results": results,
            "count": len(results),
        },
    }


@router.get("/tafsir/context")
async def get_tafsir_context(request: Request, ayah_id: str):
    """
    Get consolidated scholarly context for a specific ayah.
    Used by the Node.js backend to ground AI explanations.
    """
    tafsir_rag = request.app.state.tafsir_rag
    if not tafsir_rag or not tafsir_rag.is_loaded:
        raise HTTPException(503, "Tafsir RAG not initialized")

    context = tafsir_rag.get_ayah_context(ayah_id)
    
    return {
        "status": "success",
        "ayah_id": ayah_id,
        "context": context
    }


# ─── Direct TTS Endpoint (for RAG answer voiceover) ───────────────────────────

class TTSRequest(BaseModel):
    text: str
    language: str = "en"   # 'en' | 'ar' | 'ur'

@router.post("/tts")
async def direct_tts(req: TTSRequest):
    """
    POST /api/tts

    Synthesizes raw text directly to audio — no templates, no caching.
    Used for voicing RAG/chat answers verbatim so every unique response
    has unique audio (fixes the "same audio repeating" bug).

    Body:
        text     (str): The text to synthesize
        language (str): 'en' | 'ar' | 'ur'

    Returns:
        audio/wav stream
    """
    import io
    from services.local_tts import tts_engine

    text = req.text.strip()
    if not text:
        raise HTTPException(400, "text is required")

    # Clamp to a reasonable length for voice response (~300 words max)
    words = text.split()
    if len(words) > 300:
        text = " ".join(words[:300])
        if not text.endswith((".", "!", "?")):
            text += "."

    lang = req.language.lower().strip()
    if lang not in ("en", "ar", "ur"):
        lang = "en"

    if not tts_engine.is_loaded:
        tts_engine.load_models(lang)

    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            out_path = tmp.name

        success = tts_engine.synthesize(text, lang, out_path)
        if not success:
            raise RuntimeError("TTS synthesis failed")

        # Stream back the WAV file then delete
        async def wav_stream():
            try:
                with open(out_path, "rb") as f:
                    while True:
                        chunk = f.read(4096)
                        if not chunk:
                            break
                        yield chunk
            finally:
                try:
                    os.remove(out_path)
                except Exception:
                    pass

        return StreamingResponse(
            wav_stream(),
            media_type="audio/wav",
            headers={"X-TTS-Language": lang},
        )

    except Exception as e:
        logger.error(f"[/api/tts] Direct TTS failed: {e}")
        try:
            os.remove(out_path)
        except Exception:
            pass
        raise HTTPException(500, f"TTS synthesis failed: {str(e)}")


# ─── Maulana Voice Endpoint ────────────────────────────────────────────────────

class MaulanaVoiceRequest(BaseModel):
    rule: str
    word: str
    guidance: str
    language: str = "english"   # 'urdu' | 'arabic' | 'english'
    madhab: str = "shafi"
    ayah_id: str | None = None

from fastapi import Query

@router.get("/maulana-voice")
@router.post("/maulana-voice")
async def maulana_voice(
    req: MaulanaVoiceRequest | None = None,
    rule: str = Query(None),
    word: str = Query(None),
    guidance: str = Query(None),
    language: str = Query("english"),
    madhab: str = Query("shafi"),
    ayah_id: str = Query(None)
):
    """
    POST /api/maulana-voice

    Generates a ≤15-word Maulana-grade Tajweed advisory via Gemini 1.5 Flash,
    then synthesizes it into a streaming audio response using ElevenLabs
    Multilingual v3. Audio begins playing on the frontend before the full
    file is ready (optimized streaming buffer).

    On ElevenLabs quota exhaustion, falls back to JSON text response.

    Body:
        rule     (str): Violated Tajweed rule (e.g., 'Qalqalah')
        word     (str): Arabic word where error occurred
        guidance (str): Existing TajweedScorer guidance text
        language (str): 'urdu' | 'arabic' | 'english'

    Returns:
        audio/mpeg stream  — if ElevenLabs is available
        JSON text fallback — if quota is exhausted or ElevenLabs errors
    """
    # Fallback to GET parameters if POST body is not provided
    req_rule = req.rule if req else rule
    req_word = req.word if req else word
    req_guidance = req.guidance if req else guidance
    req_language = req.language if req else language
    req_madhab = req.madhab if req else madhab
    req_ayah_id = req.ayah_id if req else ayah_id

    error_details = {
        "rule":     req_rule,
        "word":     req_word,
        "guidance": req_guidance,
    }

    result = await get_maulana_advice(
        error_details=error_details,
        language=req_language,
        madhab=req_madhab,
        ayah_id=req_ayah_id,
    )

    # --- Streaming Response: Audio begins before full file is ready ---
    if result["audio_stream"] is not None:
        async def audio_generator():
            async for chunk in result["audio_stream"]:
                yield chunk

        return StreamingResponse(
            audio_generator(),
            media_type="audio/mpeg",
            headers={
                "X-Maulana-Text":     result["text"],
                "X-Maulana-Language": req_language,
                "X-Maulana-Madhab":   req_madhab,
                "X-Fallback":         "false",
            },
        )

    # --- Text Fallback: Local TTS unavailable ---
    logger.warning(
        f"[/api/maulana-voice] Falling back to text. Reason: {result.get('fallback_reason')}"
    )
    return JSONResponse(
        status_code=200,
        content={
            "status":          "fallback_text",
            "text":            result["text"],
            "language":        req_language,
            "madhab":          req_madhab,
            "fallback":        True,
            "fallback_reason": result.get("fallback_reason"),
        },
    )


# ─── Audio Orchestrator Endpoint ───────────────────────────────────────────────

class PlaylistRequest(BaseModel):
    surah: int
    verse: int
    language: str = "en"
    include_insight: bool = False
    rule: str = ""
    word: str = ""
    guidance: str = ""

@router.post("/audio-playlist")
async def get_audio_playlist(req: PlaylistRequest):
    """
    Returns an orchestrated playlist combining static CDN audio with dynamic TTS.
    """
    from services.audio_orchestrator import build_playlist
    
    insight_url = None
    if req.include_insight:
        import urllib.parse
        # Construct the URL to hit our own maulana-voice endpoint
        params = urllib.parse.urlencode({
            "rule": req.rule,
            "word": req.word,
            "guidance": req.guidance,
            "language": req.language
        })
        # The frontend will hit this URL to stream the local TTS audio
        insight_url = f"/api/maulana-voice?{params}"

    # Map language 'english'/'urdu' to code 'en'/'ur' expected by orchestrator
    lang_code = "ur" if "urdu" in req.language.lower() else "ar" if "arabic" in req.language.lower() else "en"
        
    playlist = build_playlist(
        surah=req.surah,
        verse=req.verse,
        target_language=lang_code,
        live_insight_url=insight_url
    )
    
    return {
        "status": "success",
        "playlist": playlist
    }


class SmartQueryRequest(BaseModel):
    madhab: str
    query: str
    n_results: int = 3

@router.post("/smart-query")
async def smart_query(body: SmartQueryRequest):
    """
    Directly query the Madhab vector database (ChromaDB) to test RAG retrieval.
    """
    from services.smart_rag import smart_rag
    if not smart_rag.is_loaded:
        raise HTTPException(503, "SmartRAG service not initialized")
        
    results = smart_rag.query_madhab(
        madhab=body.madhab,
        query_text=body.query,
        n_results=body.n_results
    )
    
    return {
        "status": "success",
        "data": {
            "madhab": body.madhab,
            "query": body.query,
            "results": results
        }
    }
