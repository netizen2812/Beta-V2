import librosa
import numpy as np
import logging

logger = logging.getLogger(__name__)

# Qalqalah Letters: ق , ط , ب , ج , د
QALQALAH_LETTERS_TR = {'q', 'ṭ', 'b', 'j', 'd'}  # Transliteration (with dot for Taa)
QALQALAH_LETTERS_AR = {'ق', 'ط', 'ب', 'ج', 'د'}  # Arabic

class SpectralAnalyzer:
    @staticmethod
    def detect_qalqalah(audio_path, segment_times):
        """
        Detect Qalqalah energy spikes using STFT.
        
        Args:
            audio_path: Path to the audio file
            segment_times: list of {"word_index": i, "start": float, "end": float, "is_qalqalah": bool}
        """
        try:
            y, sr = librosa.load(audio_path, sr=16000)
        except Exception as e:
            logger.error(f"Failed to load audio for spectral analysis: {e}")
            return []

        feedback = []
        for segment in segment_times:
            if not segment.get("is_qalqalah"):
                continue

            start_idx = int(segment["start"] * sr)
            end_idx = int(segment["end"] * sr)
            
            # Focus on the end of the segment where the bounce happens
            tail_start = max(start_idx, end_idx - int(0.1 * sr))
            y_tail = y[tail_start:end_idx]
            
            if len(y_tail) == 0: continue

            # Compute STFT
            # Use smaller n_fft for short segments (100ms = 1600 samples)
            stft = np.abs(librosa.stft(y_tail, n_fft=512, hop_length=128))
            freqs = librosa.fft_frequencies(sr=sr, n_fft=512)
            
            # Find indices for 4k-8k Hz band
            band_mask = (freqs >= 4000) & (freqs <= 8000)
            if not np.any(band_mask):
                feedback.append({"word_index": segment["word_index"], "error": False})
                continue
                
            band_energy = np.mean(stft[band_mask, :])
            mean_energy = np.mean(stft)
            logger.debug(f"DEBUG QAL: band={band_energy:.4f} mean={mean_energy:.4f} ratio={band_energy/mean_energy if mean_energy > 0 else 0:.2f}")
            
            # Success if band energy > 2x mean energy
            if band_energy < (2 * mean_energy):
                feedback.append({
                    "word_index": segment["word_index"],
                    "error": True,
                    "rule": "Qalqalah",
                    "guidance": "Missing bouncing sound (Qalqalah). Ensure a sharp release on the Sakin letter."
                })
            else:
                feedback.append({"word_index": segment["word_index"], "error": False})

        return feedback
