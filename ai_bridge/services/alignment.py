"""
Forced Alignment Engine — CTC-based word boundary detection.

Uses the Wav2Vec2 CTC logits to align user audio frames to
reference phonetic words. This enables us to know exactly
*when* in the audio each word was spoken, enabling precise
word-level feedback.
"""

import torch
import numpy as np
import logging

logger = logging.getLogger(__name__)


class AlignmentEngine:
    @staticmethod
    def align_words(
        logits: torch.Tensor,
        audio_length_seconds: float,
        processor,
    ) -> list[dict]:
        """
        Perform forced alignment using CTC logits.

        This is a simplified alignment that uses the argmax path
        and maps predicted tokens to time boundaries, then aligns
        to reference words.

        Args:
            logits: CTC logits from Wav2Vec2 (shape: [1, T, V])
            audio_length_seconds: Duration of the audio in seconds
            reference_phonetics: List of expected phonetic words
            processor: Wav2Vec2Processor for token decoding

        Returns:
            [
                {
                    "word": "bismi",
                    "start_time": 0.0,
                    "end_time": 0.42,
                    "confidence": 0.95
                },
                ...
            ]
        """
        # Get predicted token IDs
        predicted_ids = torch.argmax(logits, dim=-1)[0]  # [T]
        num_frames = len(predicted_ids)

        if num_frames == 0:
            return []

        # Time per frame
        time_per_frame = audio_length_seconds / num_frames

        # Get log probabilities for confidence scoring
        log_probs = torch.log_softmax(logits, dim=-1)[0]  # [T, V]

        # Decode the full predicted sequence
        tokens = predicted_ids.cpu().numpy()

        # Find word boundaries using the | delimiter token and blank token
        vocab = processor.tokenizer.get_vocab()
        blank_id = processor.tokenizer.pad_token_id if processor.tokenizer.pad_token_id is not None else 0
        delimiter_id = vocab.get("|", -1)

        # Group consecutive non-blank, non-delimiter tokens into word segments
        segments = []
        current_segment = {"start": None, "end": None, "token_ids": [], "confidences": []}

        for frame_idx, token_id in enumerate(tokens):
            token_id = int(token_id)

            if token_id == blank_id:
                # Blank token — end current segment if any
                if current_segment["start"] is not None and current_segment["token_ids"]:
                    current_segment["end"] = frame_idx
                    segments.append(current_segment)
                    current_segment = {"start": None, "end": None, "token_ids": [], "confidences": []}
                continue

            if token_id == delimiter_id:
                # Word delimiter — end current segment
                if current_segment["start"] is not None and current_segment["token_ids"]:
                    current_segment["end"] = frame_idx
                    segments.append(current_segment)
                    current_segment = {"start": None, "end": None, "token_ids": [], "confidences": []}
                continue

            # Regular token
            if current_segment["start"] is None:
                current_segment["start"] = frame_idx

            current_segment["token_ids"].append(token_id)
            confidence = float(log_probs[frame_idx, token_id].exp())
            current_segment["confidences"].append(confidence)

        # Don't forget the last segment
        if current_segment["start"] is not None and current_segment["token_ids"]:
            current_segment["end"] = num_frames
            segments.append(current_segment)

        # Convert segments to timed word entries
        aligned_words = []
        for i, seg in enumerate(segments):
            # Decode the token IDs to text
            word_text = processor.tokenizer.decode(seg["token_ids"])
            avg_confidence = np.mean(seg["confidences"]) if seg["confidences"] else 0.0

            aligned_words.append({
                "word": word_text.strip(),
                "start_time": round(seg["start"] * time_per_frame, 3),
                "end_time": round(seg["end"] * time_per_frame, 3),
                "confidence": round(float(avg_confidence), 3),
            })

        return aligned_words
