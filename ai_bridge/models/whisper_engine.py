"""
Whisper ASR Engine — Quranic Arabic transcription.

Uses tarteel-ai/whisper-base-ar-quran, a fine-tuned Whisper model
trained specifically on Quranic recitation.

Output: Arabic text transcription of recited audio.
"""

import io
import torch
import librosa
import logging
import numpy as np
import soundfile as sf
from transformers import AutoProcessor, AutoModelForSpeechSeq2Seq, pipeline

logger = logging.getLogger(__name__)


MODEL_ID = "tarteel-ai/whisper-base-ar-quran"


class WhisperEngine:
    def __init__(self):
        self.processor = None
        self.model = None
        self.pipe = None
        self.device = None
        self.is_loaded = False

    def load(self):
        """Load the Whisper model and processor."""
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        logger.info(f"Loading Whisper on device: {self.device} with dtype: {torch_dtype}")

        self.processor = AutoProcessor.from_pretrained(MODEL_ID)
        self.model = AutoModelForSpeechSeq2Seq.from_pretrained(
            MODEL_ID,
            torch_dtype=torch_dtype,
            low_cpu_mem_usage=not torch.cuda.is_available(),
        ).to(self.device)

        # Fix for generation config timestamps ValueError in transformers
        if self.model.generation_config is not None:
            try:
                no_timestamp_id = self.processor.tokenizer.convert_tokens_to_ids("<|notimestamps|>")
                if no_timestamp_id is None or (isinstance(no_timestamp_id, int) and no_timestamp_id < 0):
                    no_timestamp_id = getattr(self.model.config, "no_timestamps_token_id", None)
                if no_timestamp_id is None and hasattr(self.processor.tokenizer, "no_timestamps_token_id"):
                    no_timestamp_id = self.processor.tokenizer.no_timestamps_token_id
                
                if no_timestamp_id is not None:
                    self.model.generation_config.no_timestamps_token_id = no_timestamp_id
                    logger.info(f"✅ Configured generation_config.no_timestamps_token_id = {no_timestamp_id}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to configure no_timestamps_token_id: {e}")

        self.pipe = pipeline(
            "automatic-speech-recognition",
            model=self.model,
            tokenizer=self.processor.tokenizer,
            feature_extractor=self.processor.feature_extractor,
            torch_dtype=torch_dtype,
            device=self.device,
        )

        self.is_loaded = True

    def transcribe(self, audio_bytes: bytes, mime_type: str = "audio/webm") -> dict:
        """
        Transcribe audio bytes to Arabic Quranic text.

        Args:
            audio_bytes: Raw audio file bytes (webm, mp3, wav, etc.)
            mime_type: MIME type of the audio

        Returns:
            {
                "text": "بِسْمِ اللَّهِ الرَّحْمَنِ الرَّحِيمِ",
                "chunks": [{"text": "...", "timestamp": (start, end)}]  # if available
            }
        """
        if not self.is_loaded:
            raise RuntimeError("Whisper model not loaded. Call load() first.")

        # Convert bytes to numpy array at 16kHz mono
        audio_array = self._bytes_to_array(audio_bytes)
        
        # Guard against completely empty or trimmed silent audio (P2.12)
        if len(audio_array) == 0:
            logger.warning("Audio array is empty or silent after VAD trimming.")
            return {
                "text": "",
                "chunks": [],
            }

        if len(audio_array) / 16000 > 30:
            logger.warning("Audio >30s — Whisper will truncate. Consider chunking.")

        # Run inference with token limits to prevent infinite loop / CUDA device assert (P2.12)
        result = self.pipe(
            audio_array,
            generate_kwargs={"max_new_tokens": 128},
            return_timestamps=False,
        )

        return {
            "text": result.get("text", "").strip(),
            "chunks": result.get("chunks", []),
        }

    def _bytes_to_array(self, audio_bytes: bytes) -> np.ndarray:
        """Convert raw audio bytes to a 16kHz mono float32 numpy array."""
        try:
            # Try soundfile first (WAV, FLAC, OGG)
            audio, sr = sf.read(io.BytesIO(audio_bytes))
        except Exception:
            # Fallback to librosa (handles MP3, WebM via ffmpeg)
            audio, sr = librosa.load(io.BytesIO(audio_bytes), sr=None, mono=True)

        # Convert stereo to mono
        if audio.ndim > 1:
            audio = audio.mean(axis=1)

        # Resample to 16kHz
        if sr != 16000:
            audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)

        # VAD: Trim leading and trailing silence (top_db=30 is a good baseline)
        audio, _ = librosa.effects.trim(audio, top_db=30)

        # Check if the overall energy is near zero (silence) to prevent Whisper hallucinations
        if len(audio) == 0 or np.max(np.abs(audio)) < 1e-4:
            return np.array([], dtype=np.float32)

        return audio.astype(np.float32)
