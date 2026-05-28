import os
import modal

# ── Modal App Definition ──────────────────────────────────────────────────────
app = modal.App("imam-ai-bridge")

# ── Persistent Volume for Model Weights ───────────────────────────────────────
# Models are large (~3GB). We store them in a Modal Volume so they are downloaded
# only ONCE and reused across all container instances — no repeated downloads.
model_volume = modal.Volume.from_name("imam-ai-models", create_if_missing=True)
MODEL_VOLUME_PATH = "/models"

# ── Specialized GPU Image Builder ──────────────────────────────────────────────
def ignore_unnecessary(p) -> bool:
    ignore_names = {
        "venv", ".git", "node_modules", "__pycache__", 
        "temp_checkpoint_v29", "temp_checkpoint", "temp_checkpoint_v2",
        "ur_mms_v32_final", "en_xtts_v74", "base_xtts", "training_output"
    }
    parts = p.parts
    if any(part in ignore_names for part in parts):
        return True
    
    ext = p.suffix.lower()
    if ext in {".log", ".txt", ".wav", ".mp3", ".zip"}:
        if p.name.lower() == "requirements.txt":
            return False
        return True
    return False

image = (
    modal.Image.from_registry("pytorch/pytorch:2.6.0-cuda12.4-cudnn9-runtime")
    .env({"DEBIAN_FRONTEND": "noninteractive", "HF_HOME": f"{MODEL_VOLUME_PATH}/hf_cache", "COQUI_TOS_AGREED": "1"})
    .apt_install(
        "build-essential",
        "ffmpeg",
        "libsndfile1",
        "espeak-ng",
        "git",
    )
    .pip_install(
        "fastapi>=0.115.0",
        "uvicorn[standard]>=0.30.0",
        "python-multipart>=0.0.9",
        "transformers>=4.40.0,<5.0.0",
        "librosa>=0.11.0",
        "soundfile>=0.12.0",
        "numpy>=1.22.0,<2.0.0",
        "pandas>=1.5.0,<2.0.0",
        "datasets>=2.19.0",
        "python-Levenshtein>=0.20.0",
        "chromadb>=0.5.0",
        "sentence-transformers>=2.2.0",
        "coqui-tts>=0.24.0",
        "pydantic>=2.0.0",
        "aiofiles>=23.0.0",
        "httpx>=0.27.0",
        "google-genai>=1.0.0",
        "scipy>=1.9.0",
        "pypdf",
    )
    .pip_install(
        "openvoice-cli==0.0.5",
        extra_options="--no-deps"
    )
    # Copy source code into the container image, filtering out heavy folders/files
    .add_local_dir(".", "/usr/src/app", ignore=ignore_unnecessary)
)


# ── One-Time Model Download Function ─────────────────────────────────────────
# Run this ONCE after first deploy to download models into the persistent volume:
#   modal run ai_bridge/modal_app.py::download_models
@app.function(
    image=image,
    gpu="t4",
    volumes={MODEL_VOLUME_PATH: model_volume},
    timeout=3600,
    secrets=[
        modal.Secret.from_dict({
            "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY", ""),
            "OPENROUTER_API_KEY": os.getenv("OPENROUTER_API_KEY", ""),
            "INTERNAL_API_KEY": os.getenv("INTERNAL_API_KEY", "faith_tech_secret_key_2026"),
        })
    ]
)
def download_models():
    """Download all AI models into the persistent Modal Volume."""
    import subprocess, sys
    print("Downloading models into persistent volume...")
    result = subprocess.run(
        [sys.executable, "ai_bridge/scripts/download_models.py"],
        cwd="/usr/src/app",
        capture_output=False,
    )
    model_volume.commit()
    print("Indexing four-madhabs rules book...")
    result_index = subprocess.run(
        [sys.executable, "ai_bridge/scripts/index_madhab_book.py"],
        cwd="/usr/src/app",
        capture_output=False,
    )
    model_volume.commit()
    print(f"Model download complete (exit code: {result.returncode}) and indexing complete (exit code: {result_index.returncode})")


# ── ASGI Server Function ───────────────────────────────────────────────────────
# Exposes our FastAPI application over a secure public HTTPS URL.
# min_containers=1 keeps one warm T4 GPU container alive 24/7 — zero cold starts.
@app.function(
    image=image,
    gpu="t4",
    min_containers=1,
    timeout=600,
    volumes={MODEL_VOLUME_PATH: model_volume},
    secrets=[
        modal.Secret.from_dict({
            "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY", ""),
            "OPENROUTER_API_KEY": os.getenv("OPENROUTER_API_KEY", ""),
            "INTERNAL_API_KEY": os.getenv("INTERNAL_API_KEY", "faith_tech_secret_key_2026"),
            "TAFSIR_FAST_START": "0",
            "HF_HOME": f"{MODEL_VOLUME_PATH}/hf_cache",
            "COQUI_TOS_AGREED": "1",
        })
    ]
)
@modal.asgi_app()
def fastapi_app():
    import sys
    sys.path.append("/usr/src/app/ai_bridge")
    from main import app as web_app
    return web_app
