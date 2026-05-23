"""
Wav2Vec2 Phonetic Engine — Quranic phonetic transcription.

Uses TBOGamer22/wav2vec2-quran-phonetics, a fine-tuned wav2vec2 model
that outputs phonetic (romanized) representations of Quranic recitation.

Output: Phonetic string (e.g., "bismillāhirraḥmānirraḥīm")
"""

import io
import torch
import librosa
import numpy as np
import soundfile as sf
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC


MODEL_ID = "TBOGamer22/wav2vec2-quran-phonetics"


class PhoneticEngine:
    def __init__(self):
        self.processor = None
        self.model = None
        self.device = None
        self.is_loaded = False

    def load(self):
        """Load the Wav2Vec2 phonetic model and processor."""
        self.device = torch.device("cpu")

        self.processor = Wav2Vec2Processor.from_pretrained(MODEL_ID)
        
        self.model = Wav2Vec2ForCTC.from_pretrained(MODEL_ID).to(self.device)
        self.model.eval()

        self.is_loaded = True

    def transcribe_phonetics(self, audio_bytes: bytes) -> dict:
        """
        Transcribe audio bytes to a phonetic string.
        """
        logits, _ = self.get_ctc_logits(audio_bytes)
        return self.decode_logits(logits)

    def decode_logits(self, logits: torch.Tensor) -> dict:
        """Decode raw logits with frame-level timestamps and duration info."""
        import torch.nn.functional as F
        
        probs = F.softmax(logits, dim=-1)
        max_probs, predicted_ids = torch.max(probs, dim=-1)
        
        # 1. Phonetic Decoding
        phonetics = self.processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
        
        # 2. Confidence Calculation
        blank_id = self.processor.tokenizer.pad_token_id
        non_blank_mask = (predicted_ids != blank_id)
        mean_conf = max_probs[non_blank_mask].mean().item() if non_blank_mask.any() else 0.0

        # 3. Temporal Analysis (CTC Frame Counting)
        # We group identical consecutive IDs to find phoneme durations
        # Each frame is approx 20ms (for 16kHz and typical Wav2Vec2 stride)
        durations = []
        current_id = -1
        current_count = 0
        for pid in predicted_ids[0].tolist():
            if pid == current_id:
                current_count += 1
            else:
                if current_id != -1 and current_id != blank_id:
                    char = self.processor.decode([current_id])
                    durations.append({"char": char, "frames": current_count})
                current_id = pid
                current_count = 1
        
        import re
        words = [w.strip() for w in re.split(r'[| ]', phonetics) if w.strip()]

        return {
            "phonetics": phonetics.replace("|", " ").strip(),
            "words": words,
            "confidence": mean_conf,
            "char_durations": durations
        }

    def get_ctc_logits(self, audio_bytes: bytes) -> tuple:
        """
        Get raw CTC logits for forced alignment.

        Returns:
            (logits_tensor, audio_length_in_seconds)
        """
        if not self.is_loaded:
            raise RuntimeError("Phonetic model not loaded. Call load() first.")

        audio_array = self._bytes_to_array(audio_bytes)
        audio_length = len(audio_array) / 16000.0

        inputs = self.processor(
            audio_array,
            sampling_rate=16000,
            return_tensors="pt",
            padding=True,
        )

        input_values = inputs.input_values.to(self.device)

        with torch.inference_mode():
            logits = self.model(input_values).logits

        return logits, audio_length

    def _bytes_to_array(self, audio_bytes: bytes) -> np.ndarray:
        """Convert raw audio bytes to 16kHz mono float32 using the VoiceProcessor pipeline."""
        from ai_bridge.services.voice_processor import VoiceProcessor
        return VoiceProcessor.process_audio(audio_bytes, sample_rate=16000)
