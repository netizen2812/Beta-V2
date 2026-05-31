"""
Faith-Tech AI Bridge — FastAPI Application
Dual-model Quranic ASR & Tajweed validation server.

Models loaded at startup:
  - tarteel-ai/whisper-base-ar-quran  (ASR transcription)
  - TBOGamer22/wav2vec2-quran-phonetics (Phonetic analysis)

Run: uvicorn main:app --reload --port 8000
"""

import os
import time
import logging
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from dotenv import load_dotenv

# Load env variables from the root workspace folder first, then local if available
root_env = Path(__file__).resolve().parent.parent / ".env"
local_env = Path(__file__).resolve().parent / ".env"
if root_env.exists():
    load_dotenv(dotenv_path=root_env)
elif local_env.exists():
    load_dotenv(dotenv_path=local_env)
else:
    load_dotenv()

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse


from models.whisper_engine import WhisperEngine
from models.phonetic_engine import PhoneticEngine
from services.phonetic_db import PhoneticDB
from services.tafsir_rag import TafsirRAG
from services.smart_rag import smart_rag
from services.temporal_engine import TemporalEngine
from services.spectral_analyzer import SpectralAnalyzer
from routes.inference import router as inference_router
from routes.mushaf   import router as mushaf_router, inject_engines as mushaf_inject
from routes.journeys import router as journeys_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ─── Global Model Instances ───────────────────────────────────────────────────
whisper_engine: WhisperEngine | None = None
phonetic_engine: PhoneticEngine | None = None
phonetic_db: PhoneticDB | None = None
tafsir_rag: TafsirRAG | None = None
temporal_engine: TemporalEngine | None = None
spectral_analyzer: SpectralAnalyzer | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load all models and data on startup, clean up on shutdown."""
    global whisper_engine, phonetic_engine, phonetic_db, tafsir_rag, temporal_engine, spectral_analyzer

    logger.info("🚀 Faith-Tech AI Bridge starting up...")
    start = time.time()

    # 1. Load Whisper ASR
    logger.info("📥 Loading Whisper ASR model (tarteel-ai/whisper-base-ar-quran)...")
    whisper_engine = WhisperEngine()
    whisper_engine.load()
    logger.info("✅ Whisper loaded.")

    # 2. Load Wav2Vec2 Phonetic
    logger.info("📥 Loading Wav2Vec2 Phonetic model (TBOGamer22/wav2vec2-quran-phonetics)...")
    phonetic_engine = PhoneticEngine()
    phonetic_engine.load()
    logger.info("✅ Wav2Vec2 Phonetic loaded.")

    # 3. Load Phonetic Reference DB
    logger.info("📥 Loading Buraaq phonetic reference database...")
    phonetic_db = PhoneticDB()
    phonetic_db.load()
    logger.info(f"✅ Phonetic DB loaded: {phonetic_db.total_words} words across {phonetic_db.total_ayahs} ayahs.")

    # 4. Initialize Tafsir RAG and SmartRAG
    logger.info("📥 Initializing ChromaDB Tafsir vector store...")
    tafsir_rag = TafsirRAG()
    tafsir_rag.load()
    logger.info(f"✅ Tafsir RAG loaded: {tafsir_rag.collection_size} entries indexed.")

    logger.info("📥 Initializing ChromaDB SmartRAG vector store...")
    smart_rag.load()
    logger.info("✅ SmartRAG loaded.")

    # 5. Initialize Tajweed Precision Engines
    logger.info("📥 Initializing Tajweed Precision Engines...")
    temporal_engine = TemporalEngine()
    spectral_analyzer = SpectralAnalyzer()
    logger.info("✅ Precision Engines ready.")

    # 6. Two-Stage TTS: Start XTTSv2 loading in background thread.
    # edge-tts (Microsoft cloud) serves audio immediately while XTTSv2 warms up (~88s).
    # Once XTTSv2 is ready, tts_router automatically switches all future calls to local model.
    logger.info("📥 [Stage 1] edge-tts cloud TTS ready immediately (zero load time).")
    logger.info("📥 [Stage 2] Starting XTTSv2 background load (will auto-switch when ready)...")

    def _load_xtts_background():
        """Background thread: load XTTSv2 + MMS-Urdu, then flip the router to local mode."""
        try:
            from services.local_tts import tts_engine
            from services.tts_router import tts_router
            logger.info("[BG] Loading XTTSv2 English model...")
            tts_engine.load_models("en")
            logger.info("[BG] Loading MMS-VITS Urdu model...")
            tts_engine._load_mms_urdu()
            tts_router.mark_xtts_ready()  # Auto-switches all future TTS calls to local model
            logger.info("✅ [BG] XTTSv2 + MMS-Urdu fully loaded. Switched from edge-tts → local model.")
        except Exception as e:
            logger.error(f"[BG] XTTSv2 background load failed: {e}. edge-tts will continue serving.")

    bg_thread = threading.Thread(target=_load_xtts_background, daemon=True, name="xtts-loader")
    bg_thread.start()

    elapsed = time.time() - start
    logger.info(f"🚀 All systems ready in {elapsed:.1f}s")

    # Store in app state for route access
    app.state.whisper = whisper_engine
    app.state.phonetic = phonetic_engine
    app.state.phonetic_db = phonetic_db
    app.state.tafsir_rag = tafsir_rag
    app.state.temporal_engine = temporal_engine
    app.state.spectral_analyzer = spectral_analyzer

    # Inject engines into mushaf WS router
    mushaf_inject(
        phonetic  = phonetic_engine,
        phonetic_db = phonetic_db,
        spectral  = spectral_analyzer,
    )

    yield

    # Cleanup
    logger.info("🛑 Shutting down AI Bridge...")
    del whisper_engine, phonetic_engine, phonetic_db, tafsir_rag, temporal_engine, spectral_analyzer


# ─── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Faith-Tech AI Bridge",
    description="Quranic ASR & Tajweed validation using Whisper + Wav2Vec2",
    version="1.0.0",
    lifespan=lifespan,
)

@app.middleware("http")
async def verify_api_key(request: Request, call_next):
    if request.url.path.startswith("/api/") and request.url.path != "/api/health":
        internal_key = os.getenv("INTERNAL_API_KEY")
        if internal_key:
            key = request.headers.get("X-API-Key")
            if key != internal_key:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Unauthorized: Invalid or missing X-API-Key header."}
                )
    return await call_next(request)

origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
origins = [o.strip() for o in origins_str.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(inference_router, prefix="/api")
app.include_router(mushaf_router,   prefix="/api")
app.include_router(journeys_router)


@app.get("/api/health")
async def health():
    from services.tts_router import tts_router
    return {
        "status": "ok",
        "models": {
            "whisper": app.state.whisper is not None and app.state.whisper.is_loaded,
            "phonetic": app.state.phonetic is not None and app.state.phonetic.is_loaded,
        },
        "phonetic_db": app.state.phonetic_db is not None and app.state.phonetic_db.is_loaded,
        "tafsir_rag": app.state.tafsir_rag is not None and app.state.tafsir_rag.is_loaded,
        "device": str(app.state.whisper.device) if app.state.whisper else "unknown",
        "tts_stage": tts_router.active_stage,  # "edge-tts-cloud" or "local-xtts"
    }
