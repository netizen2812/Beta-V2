import io
import numpy as np
import librosa
import soundfile as sf
import noisereduce as nr
import pyloudnorm as pyln
from scipy.signal import butter, lfilter

class VoiceProcessor:
    @staticmethod
    def process_audio(audio_bytes: bytes, sample_rate=16000) -> np.ndarray:
        """
        Full 'Maulana' Audio Intelligence Pipeline:
        1. Load & Resample
        2. Stationary Denoising (noisereduce)
        3. LUFS Normalization (Consistency)
        4. High-Frequency Articulation Boost (Makharij focus)
        """
        # 1. Load & Resample
        try:
            audio, sr = sf.read(io.BytesIO(audio_bytes))
            if len(audio.shape) > 1:
                audio = np.mean(audio, axis=1)
            if sr != sample_rate:
                audio = librosa.resample(audio, orig_sr=sr, target_sr=sample_rate)
        except Exception:
            # Fallback to ffmpeg / librosa.load for other formats
            import tempfile
            import os
            import subprocess
            
            with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as in_tmp:
                in_tmp.write(audio_bytes)
                in_path = in_tmp.name
                
            out_path = in_path + ".wav"
            
            try:
                subprocess.run([
                    "ffmpeg", "-y", "-i", in_path, 
                    "-ar", str(sample_rate), "-ac", "1", 
                    out_path
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                audio, sr = sf.read(out_path)
            except Exception:
                # Fallback to librosa.load if ffmpeg fails
                audio, sr = librosa.load(in_path, sr=sample_rate, mono=True)
            finally:
                for p in [in_path, out_path]:
                    if os.path.exists(p):
                        try:
                            os.remove(p)
                        except Exception:
                            pass
        
        # 2. Stationary Noise Reduction (Bypassed to save 20+ seconds of CPU time and preserve high-frequency Makharij features)
        audio_denoised = audio
        
        # 3. LUFS Normalization (-16 LUFS is standard for voice)
        # pyloudnorm returns -inf loudness (not an exception) for near-silent audio,
        # which causes normalize.loudness() to return an array full of Inf/NaN values.
        # Those propagate through the shelf filter and cause librosa to raise:
        #   ParameterError: Audio buffer is not finite everywhere
        try:
            meter = pyln.Meter(sr)
            loudness = meter.integrated_loudness(audio_denoised)
            audio_normalized = pyln.normalize.loudness(audio_denoised, loudness, -16.0)
            # pyloudnorm silently produces Inf/NaN for silent audio — catch it here
            if not np.all(np.isfinite(audio_normalized)):
                raise ValueError("Non-finite values after LUFS normalization (silent/near-silent audio)")
        except Exception:
            # Fallback to RMS normalization if LUFS fails (short clips, silent audio)
            peak = np.max(np.abs(audio_denoised))
            audio_normalized = audio_denoised / (peak + 1e-6) if peak > 1e-6 else audio_denoised

        # 4. Articulation Enhancement (High-shelf filter > 3kHz)
        # Most Tajweed 'identity letters' (Qaf, Sad, etc.) differ in the 3-8kHz range
        audio_enhanced = VoiceProcessor._high_shelf_filter(audio_normalized, sr, cutoff=3000, gain=6)

        # Final guard: clip to [-1, 1] and ensure all values are finite before
        # handing off to Whisper/Wav2Vec2. Prevents librosa ParameterError downstream.
        audio_enhanced = np.clip(audio_enhanced, -1.0, 1.0)
        if not np.all(np.isfinite(audio_enhanced)):
            audio_enhanced = np.nan_to_num(audio_enhanced, nan=0.0, posinf=1.0, neginf=-1.0)

        return audio_enhanced.astype(np.float32)

    @staticmethod
    def _high_shelf_filter(data, sr, cutoff, gain):
        """Boosts high frequencies to make articulation sharper."""
        nyquist = 0.5 * sr
        norm_cutoff = cutoff / nyquist
        # Simple butterworth high-pass filter as a proxy for shelf
        b, a = butter(1, norm_cutoff, btype='high')
        # Mix original with filtered to simulate shelf gain
        filtered = lfilter(b, a, data)
        return data + (filtered * (gain / 10.0))

    @staticmethod
    def to_bytes(audio_array: np.ndarray, sr=16000) -> bytes:
        """Convert numpy array back to WAV bytes."""
        buf = io.BytesIO()
        sf.write(buf, audio_array, sr, format='WAV')
        return buf.getvalue()
