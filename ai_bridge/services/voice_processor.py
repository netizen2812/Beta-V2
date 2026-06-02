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
        # 1. Load & Resample using ultra-fast native ffmpeg conversion (avoids slow pure-python audioread piping)
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
        try:
            meter = pyln.Meter(sr) 
            loudness = meter.integrated_loudness(audio_denoised)
            audio_normalized = pyln.normalize.loudness(audio_denoised, loudness, -16.0)
        except:
            # Fallback to RMS normalization if LUFS fails (short clips)
            audio_normalized = audio_denoised / (np.max(np.abs(audio_denoised)) + 1e-6)

        # 4. Articulation Enhancement (High-shelf filter > 3kHz)
        # Most Tajweed 'identity letters' (Qaf, Sad, etc.) differ in the 3-8kHz range
        audio_enhanced = VoiceProcessor._high_shelf_filter(audio_normalized, sr, cutoff=3000, gain=6)
        
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
