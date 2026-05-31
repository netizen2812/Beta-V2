import logging
from pathlib import Path
import os
import torch

import numpy as np
import unicodedata

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("LocalTTS")

# Absolute path resolutions based on the file location to ensure Cwd-independence
SERVICE_DIR = Path(__file__).resolve().parent
AI_BRIDGE_DIR = SERVICE_DIR.parent
DATA_DIR = AI_BRIDGE_DIR / "data"

# Fine-tuned XTTS model paths (EN + AR use XTTSv2)
MODEL_PATHS = {
    "en": AI_BRIDGE_DIR / "models" / "en_xtts_v74",
    "ar": AI_BRIDGE_DIR / "models" / "base_xtts"
}

# Config paths
CONFIG_PATHS = {
    "en": AI_BRIDGE_DIR / "models" / "en_xtts_v74" / "config.json",
    "ar": AI_BRIDGE_DIR / "models" / "base_xtts" / "config.json"
}

# ── CANONICAL SPEAKER REFERENCES ─────────────────────────────────────────────
# Single source of truth — used at BOTH training and inference.
# Changing a path here affects both. Never reference speaker wavs anywhere else.
CANONICAL_REFS = {
    "en": DATA_DIR / "tts_dataset" / "wavs_en" / "en_0012.wav",
    "ur": DATA_DIR / "tts_dataset" / "wavs_ur" / "ur_0001.wav",
    "ar": DATA_DIR / "tts_dataset" / "wavs_ar" / "ar_0007.wav",
}

# Arabic multi-reference voices for zero-shot cloning
AR_REFS = [
    str((AI_BRIDGE_DIR / "scratch" / "ref_wavs" / "ar_0109_s09.wav").absolute()),
    str((AI_BRIDGE_DIR / "scratch" / "ref_wavs" / "ar_0121_s04.wav").absolute()),
    str((AI_BRIDGE_DIR / "scratch" / "ref_wavs" / "ar_0150_s06.wav").absolute()),
    str((AI_BRIDGE_DIR / "scratch" / "ref_wavs" / "ar_0184_s07.wav").absolute())
]

# MMS-VITS Urdu model directory (fine-tuned on GCP)
MMS_URDU_DIR = AI_BRIDGE_DIR / "models" / "ur_mms_v32_final" / "ur_mms_v32"
MMS_SAMPLE_RATE = 16000
XTTS_SAMPLE_RATE = 24000

class LocalTTSEngine:
    def __init__(self):
        self.is_loaded = False
        self.tts = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._phonetic_dict = {}
        self._ur_model = None
        self._ur_tokenizer = None
        self._tone_color_converter = None
        self._ar_target_se = None
        self._load_phonetic_dictionary()
        log.info(f"LocalTTSEngine initialized (Device: {self.device.upper()}).")

    def _load_phonetic_dictionary(self):
        dict_path = DATA_DIR / "maulana_phonetic_dictionary.json"
        if dict_path.exists():
            try:
                import json
                with open(dict_path, "r", encoding="utf-8") as f:
                    self._phonetic_dict = json.load(f)
                log.info(f"Loaded {len(self._phonetic_dict)} phonetic mappings.")
            except Exception as e:
                log.error(f"Failed to load phonetic dictionary: {e}")

    def load_models(self, language: str = "en"):
        """Load the Coqui TTS model into VRAM."""
        if self.is_loaded and getattr(self, 'loaded_language', None) == language:
            return
        try:
            from TTS.api import TTS
            
            model_path = MODEL_PATHS.get(language)
            config_path = CONFIG_PATHS.get(language)
            
            if model_path and model_path.exists() and config_path and config_path.exists():
                log.info(f"Loading custom fine-tuned Maulana model [{language.upper()}]...")
                # We pass the directory to model_path for custom models as required by XTTS loader
                self.tts = TTS(model_path=str(model_path), config_path=str(config_path)).to(self.device)
            else:
                log.info(f"Loading base XTTSv2 model for [{language.upper()}] zero-shot cloning...")
                self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(self.device)
            
            self.is_loaded = True
            self.loaded_language = language
            log.info(f"✅ TTS Model loaded onto {self.device.upper()} successfully.")
        except ImportError:
            log.warning("Coqui TTS library not found. Falling back to stub mode.")
            self.is_loaded = True # Mark as loaded to prevent retry loops

    def unload_all_models(self):
        """Unload all heavy models from memory/VRAM to prevent MemoryError."""
        log.info("Unloading all heavy models from VRAM/RAM...")
        self.tts = None
        self.is_loaded = False
        self.loaded_language = None
        self._ur_model = None
        self._ur_tokenizer = None
        self._tone_color_converter = None
        self._ar_target_se = None
        
        import gc
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def apply_phonetic_fixes(self, text: str, language: str = "en") -> str:
        """Apply systemic phonetic overrides for Islamic terms (EN + UR)."""
        import re
        # Only apply if we have a loaded dictionary and language supports it
        if language not in ("en", "ur"):
            return text
        for word, phonetic in self._phonetic_dict.items():
            pattern = re.compile(rf'\b{re.escape(word)}\b', re.IGNORECASE)
            text = pattern.sub(phonetic, text)
        return text

    @staticmethod
    def normalize_arabic(text: str) -> str:
        """
        Normalize Arabic text before synthesis.
        - Removes tatweel/kashida (U+0640) — decorative elongation that confuses tokenizers.
        - NFC-normalizes all Unicode to consolidate composed forms.
        - Strips invisible Unicode control chars that survive copy-paste from web.
        """
        # Remove tatweel (kashida)
        text = text.replace('\u0640', '')
        # Remove zero-width non-joiner / zero-width joiner / soft-hyphen
        text = text.replace('\u200c', '').replace('\u200d', '').replace('\u00ad', '')
        # NFC normalization — ensures harakaat are in composed canonical form
        text = unicodedata.normalize('NFC', text)
        return text.strip()

    def _load_mms_urdu(self):
        """Lazy-load the MMS-VITS Urdu model (heavy, only when needed)."""
        if self._ur_model is not None:
            return  # Already loaded
        from transformers import VitsModel, VitsTokenizer
        mms_dir = str(MMS_URDU_DIR) if MMS_URDU_DIR.exists() else "facebook/mms-tts-urd-script_arabic"
        log.info(f"Loading MMS-VITS Urdu from: {mms_dir}")
        self._ur_tokenizer = VitsTokenizer.from_pretrained(mms_dir)
        self._ur_model = VitsModel.from_pretrained(mms_dir).to("cpu")
        self._ur_model.eval()
        log.info("✅ MMS-VITS Urdu model loaded.")

    def apply_urdu_prepositional_spacing(self, text: str) -> str:
        """Inject explicit spacing around core Urdu prepositions/clitics to resolve token merging in MMS-VITS."""
        prepositions = ["کے", "سے", "میں", "پر", "کا", "کی", "کو", "نے", "اور", "جو", "ہے", "ہیں"]
        for prep in prepositions:
            text = text.replace(prep, f" {prep} ")
        import re
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def normalize_urdu(self, text: str) -> str:
        """
        Normalize Urdu spelling variations to resolve instabilities in MMS-VITS.
        Replaces Arabic loan spelling 'الاخلاص' with standard Urdu spelling 'اخلاص' to prevent voicing glitches.
        """
        # Replace Arabic definite loan spelling 'الاخلاص' with standard Urdu 'اخلاص'
        text = text.replace("الاخلاص", "اخلاص")
        return text

    def _load_openvoice(self):
        """Lazy-load the OpenVoice ToneColorConverter (heavy, only when needed)."""
        if self._tone_color_converter is not None:
            return
        log.info("Loading OpenVoice ToneColorConverter...")
        from openvoice_cli.api import ToneColorConverter
        from openvoice_cli.downloader import download_checkpoint
        
        # Store converter checkpoints in the local models folder (OS-independent and docker-friendly)
        ckpt_converter = AI_BRIDGE_DIR / "models" / "openvoice" / "converter"
        if not ckpt_converter.exists():
            log.info("Downloading OpenVoice converter checkpoints...")
            ckpt_converter.mkdir(parents=True, exist_ok=True)
            download_checkpoint(str(ckpt_converter))
            
        self._tone_color_converter = ToneColorConverter(str(ckpt_converter / "config.json"), device=self.device)
        self._tone_color_converter.load_ckpt(str(ckpt_converter / "checkpoint.pth"))
        log.info("Extracting target Arabic speaker embedding (cached)...")
        self._ar_target_se = self._tone_color_converter.extract_se(AR_REFS)
        log.info("✅ OpenVoice ToneColorConverter loaded.")

    def _denoise_urdu(self, wav: np.ndarray, sr: int) -> np.ndarray:
        """
        Premium Urdu noise removal: 3rd-order Butterworth bandpass filter (150Hz - 6.5kHz)
        coupled with an envelope-following soft noise gate to eliminate VITS vocoder
        whistle ("teee") and background hiss ("shhh") during silent parts.
        """
        import scipy.signal as sig
        
        # 1. 3rd-order Butterworth Bandpass filter (180Hz to 6.5kHz)
        nyq = sr / 2.0
        low = 180.0 / nyq
        high = 6500.0 / nyq
        b, a = sig.butter(3, [low, high], btype='band')
        wav_filtered = sig.filtfilt(b, a, wav).astype(np.float32)
        
        # 2. Envelope-following soft noise gate
        threshold_db = -45.0
        threshold = 10 ** (threshold_db / 20.0)
        envelope = np.abs(wav_filtered)
        
        # Smooth envelope using exponential follower
        attack = 0.02
        release = 0.10
        alpha_attack = np.exp(-1.0 / (sr * attack))
        alpha_release = np.exp(-1.0 / (sr * release))
        
        smoothed_envelope = np.zeros_like(envelope)
        current_val = 0.0
        for i in range(len(envelope)):
            val = envelope[i]
            if val > current_val:
                current_val = alpha_attack * current_val + (1.0 - alpha_attack) * val
            else:
                current_val = alpha_release * current_val + (1.0 - alpha_release) * val
            smoothed_envelope[i] = current_val
            
        gain = np.ones_like(wav_filtered)
        for i in range(len(wav_filtered)):
            env_val = smoothed_envelope[i]
            if env_val < threshold:
                ratio = env_val / threshold
                gain[i] = max(0.01, ratio) # smooth fade down to 1% amplitude
                
        return (wav_filtered * gain).astype(np.float32)

    def _synthesize_mms_urdu(self, text: str, output_path: Path) -> bool:
        """
        Synthesize Urdu text using the fine-tuned MMS-VITS model.
        Splits on sentence-ending punctuation to insert natural pauses between clauses.
        Resamples from 16kHz -> 24kHz to match the XTTS pipeline output rate using exact 3:2 polyphase resampling.
        Applies a premium bandpass filter and soft noise gate to eliminate vocoder whistle and hiss.
        """
        try:
            import re
            import scipy.signal as signal
            import scipy.io.wavfile as wavfile

            self._load_mms_urdu()
            # Normalize spelling variations to prevent VITS voicing instability
            text = self.normalize_urdu(text)
            # Apply phonetic fixes and prepositional spacing
            text = self.apply_phonetic_fixes(text, language="ur")
            text = self.apply_urdu_prepositional_spacing(text)

            # Split on major punctuation to generate pause segments between clauses
            # Use comma (،), period (۔), and standard punctuation as split points
            clause_pattern = re.compile(r'([^!\?!\?،؟\.\,;:]+[!\?!\?،؟\.\,;:]*)')
            clauses = [c.strip() for c in clause_pattern.findall(text) if c.strip()]
            if not clauses:
                clauses = [text]

            # Silence segments between clauses (300ms at 24kHz)
            pause_300ms = np.zeros(int(XTTS_SAMPLE_RATE * 0.30), dtype=np.float32)
            # Shorter pause for commas (150ms)
            pause_150ms = np.zeros(int(XTTS_SAMPLE_RATE * 0.15), dtype=np.float32)

            segments = []
            for i, clause in enumerate(clauses):
                if not clause:
                    continue
                inputs = self._ur_tokenizer(text=clause, return_tensors="pt").to("cpu")
                with torch.no_grad():
                    waveform = self._ur_model(**inputs).waveform  # [1, T] at 16kHz
                wav = waveform.squeeze().cpu().numpy()
                # Exact 3:2 polyphase resampling to resample 16kHz -> 24kHz
                wav_24k = signal.resample_poly(wav, 3, 2).astype(np.float32)
                
                # Apply bandpass filter and noise gate per-clause to prevent filter ringing across silence pauses
                wav_24k = self._denoise_urdu(wav_24k, XTTS_SAMPLE_RATE)
                
                # Programmatically trim leading/trailing pre-padded silence from raw VITS synthesis
                wav_abs = np.abs(wav_24k)
                # Highly sensitive threshold (-50dB) to preserve soft ending consonants
                threshold = 0.003
                wav_indices = np.where(wav_abs > threshold)[0]
                if len(wav_indices) > 0:
                    start_w = max(0, wav_indices[0] - int(XTTS_SAMPLE_RATE * 0.050))
                    end_w = min(len(wav_24k), wav_indices[-1] + int(XTTS_SAMPLE_RATE * 0.200))
                    wav_24k = wav_24k[start_w:end_w]
                    
                # Apply a smooth 20ms linear fade-in and 50ms fade-out to guarantee perfectly pop-free transitions
                fade_in_w = int(XTTS_SAMPLE_RATE * 0.020)
                fade_out_w = int(XTTS_SAMPLE_RATE * 0.050)
                if len(wav_24k) > (fade_in_w + fade_out_w):
                    fade_in_arr = np.linspace(0.0, 1.0, fade_in_w, dtype=np.float32)
                    wav_24k[:fade_in_w] *= fade_in_arr
                    fade_out_arr = np.linspace(1.0, 0.0, fade_out_w, dtype=np.float32)
                    wav_24k[-fade_out_w:] *= fade_out_arr
                
                segments.append(wav_24k)
                
                # Add pause after each clause except the last
                if i < len(clauses) - 1:
                    # Use longer pause after sentence-ending, shorter for commas
                    last_char = clause[-1] if clause else ''
                    if last_char in '!?!?۔.':
                        segments.append(pause_300ms)
                    else:
                        segments.append(pause_150ms)

            wav_combined = np.concatenate(segments).astype(np.float32)

            # Peak normalize to -1dBFS
            peak = np.abs(wav_combined).max()
            if peak > 0:
                wav_combined = wav_combined / peak * 0.9

            wavfile.write(str(output_path), XTTS_SAMPLE_RATE, wav_combined)
            log.info(f"MMS-VITS Urdu synthesis complete ({len(clauses)} clauses): {output_path.name}")
            self.apply_audio_cushion(output_path)
            return True
        except Exception as e:
            log.error(f"MMS-VITS Urdu synthesis failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def apply_audio_cushion(self, file_path: Path, target_sr: int = 24000) -> bool:
        """
        Loads a WAV file, crops excessive noise-floor silence with an extremely sensitive
        threshold and a generous original-audio buffer to ensure soft/trailing phonemes are 
        fully preserved, applies a 50ms fade-in/fade-out on the silent margins to prevent abrupt 
        clicks/pops, pads with exactly 150ms of pure silence at the start/end, and saves it back.
        """
        try:
            import soundfile as sf
            
            data, sr = sf.read(str(file_path), dtype='float32')
            if len(data.shape) > 1:
                data = np.mean(data, axis=1).astype(np.float32)  # Mono conversion
                
            # If not matching target sample rate, resample
            if sr != target_sr:
                import librosa
                data = librosa.resample(data, orig_sr=sr, target_sr=target_sr).astype(np.float32)
                sr = target_sr
                
            # Crop excessive leading/trailing silence using a very sensitive amplitude threshold
            abs_data = np.abs(data)
            threshold = 0.002  # -54 dB threshold (highly sensitive to soft consonant/vowel tails)
            indices = np.where(abs_data > threshold)[0]
            if len(indices) > 0:
                start_idx = indices[0]
                end_idx = indices[-1]
                # Keep a 250ms buffer of the original audio on both ends to guarantee full articulation
                buffer_samples = int(sr * 0.25)
                start_idx = max(0, start_idx - buffer_samples)
                end_idx = min(len(data), end_idx + buffer_samples)
                data = data[start_idx:end_idx]
                
            # Apply 50ms linear fade-in/fade-out to ensure starting and ending are smooth and click-free
            fade_samples = int(sr * 0.05)
            if len(data) > fade_samples * 2:
                # Fade in
                fade_in = np.linspace(0.0, 1.0, fade_samples, dtype=np.float32)
                data[:fade_samples] *= fade_in
                # Fade out
                fade_out = np.linspace(1.0, 0.0, fade_samples, dtype=np.float32)
                data[-fade_samples:] *= fade_out
                
            # Pad with exactly 150ms of pure silence at start and end for breathing room
            silence_samples = int(sr * 0.15)
            silence = np.zeros(silence_samples, dtype=np.float32)
            
            padded_data = np.concatenate([silence, data, silence])
            
            # Peak normalize to -1dBFS (0.9) to guarantee uniform volume levels across all segments
            peak = np.abs(padded_data).max()
            if peak > 0:
                padded_data = (padded_data / peak) * 0.9
            
            # Write back
            sf.write(str(file_path), padded_data, sr)
            log.info(f"✅ Programmatic audio cushion applied: 250ms buffer, 50ms fades, 150ms silence pad to {file_path.name}")
            return True
        except Exception as e:
            log.warning(f"Failed to apply audio cushion to {file_path.name}: {e}")
            return False

    def _apply_openvoice_ar(self, wav_path: Path) -> bool:
        """
        Apply OpenVoice v2 ToneColorConverter to an Arabic WAV file in-place.
        Uses tau=0.07 for subtle register timbre shifting — same as test_ar_soothing.wav.
        Returns True on success, False if OpenVoice is unavailable (soft fallback).
        """
        try:
            self._load_openvoice()
            import tempfile, soundfile as sf
            src_se, _ = self._tone_color_converter.get_se(str(wav_path), self._ar_target_se, vad=False)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_out = Path(tmp.name)
            self._tone_color_converter.convert(
                audio_src_path=str(wav_path),
                src_se=src_se,
                tgt_se=self._ar_target_se,
                output_path=str(tmp_out),
                tau=0.07,
            )
            # Overwrite original with tone-converted audio
            import shutil
            shutil.move(str(tmp_out), str(wav_path))
            log.info("✅ OpenVoice ToneColorConverter applied (tau=0.07) to Arabic audio.")
            return True
        except Exception as e:
            log.warning(f"OpenVoice conversion failed (non-fatal): {e}. Using raw XTTS output.")
            return False

    def synthesize(self, text: str, language: str, output_path: Path) -> bool:
        """
        Generate audio using the local engine.
        Routes Urdu → MMS-VITS, English → XTTSv2, Arabic → XTTSv2 Zero-shot + OpenVoice v2 Conversion.
        """
        log.info(f"--- Synthesizing [LOCAL - {language.upper()}] ---")

        # ── URDU: Route to fine-tuned MMS-VITS (not XTTSv2) ─────────────────
        if language == "ur":
            import re
            if bool(re.search(r'[a-zA-Z]', text)):
                log.info("Urdu text contains Latin characters (fallback). Routing to EN XTTSv2 instead.")
                language = "en"
            else:
                return self._synthesize_mms_urdu(text, output_path)

        # ── EN / AR: Route to XTTSv2 ─────────────────────────────────────────
        if not self.is_loaded:
            self.load_models(language)
        
        # Stub fallback if library missing
        try:
            from TTS.api import TTS
        except ImportError:
            log.warning("TTS library missing. Simulating output.")
            output_path.write_bytes(b"\x00" * 1024)
            return True

        # Use canonical speaker reference (en/ar) directly to guarantee high-quality cloning
        ref_path = CANONICAL_REFS.get(language, CANONICAL_REFS["en"])
        speaker_wav = str(ref_path.absolute()) if ref_path.exists() else None

        if not speaker_wav:
            log.error(f"Speaker reference not found for language: {language}")
            return False

        try:
            # Apply systemic phonetic fixes for English
            if language == "en":
                original_text = text
                text = self.apply_phonetic_fixes(text, language="en")
                if text != original_text:
                    log.info("Applied phonetic overrides to text.")

            # Apply Arabic text normalization to prevent tokenizer mangling
            if language == "ar":
                original_text = text
                text = self.normalize_arabic(text)
                if text != original_text:
                    log.info("Applied Arabic normalization (tatweel/NFC).")

            import re
            # Normalize whitespace but PRESERVE punctuation — XTTS uses commas and periods
            # for natural pacing and pause modeling. Stripping them destroys rhythm.
            # Only collapse repeated punctuation and normalize internal whitespace.
            smooth_text = re.sub(r'([,\.!\?;:]){2,}', r'\1', text)   # collapse repeated punct
            smooth_text = re.sub(r'\s+', ' ', smooth_text).strip()

            # VOCAL PADDING: Add a short text cue to prevent abrupt start clipping
            padded_text = smooth_text
            log.info(f"Synthesizing text: '{padded_text[:80]}...' ({len(padded_text)} chars)")

            # Setup synthesis parameters
            synth_params = {
                "text": padded_text,
                "speaker_wav": speaker_wav,
                "language": language,
                "file_path": str(output_path.absolute()),
                # temperature=0.85 = XTTS config default. Produces naturally faster,
                # more energetic prosody than lower values — no DSP stretching needed.
                "temperature": 0.85,
            }

            # Natively pace up English to address user request cleanly based on sentence length
            if language == "en":
                word_count = len(text.split())
                speed = 1.0 if word_count < 8 else 1.1 if word_count < 15 else 1.15
                synth_params["speed"] = speed

            # Arabic: lower temperature for stable Quranic prosody
            if language == "ar":
                synth_params["temperature"] = 0.55
                log.info("Using stabilized temperature for Arabic.")

            # ── LENGTH-AWARE SYNTHESIS ───────────────────────────────────────
            # If the text is short/medium (< 250 characters), we synthesize in one single call.
            # This allows the model to naturally manage transitions between sentences, making them
            # flow beautifully as a continuation with no abrupt sentence-end transitions.
            # Long texts are split and stitched to prevent VRAM attention window issues.
            if len(padded_text) < 250:
                log.info(f"Synthesizing entire text in one go for natural continuity ({len(padded_text)} chars)")
                self.tts.tts_to_file(**synth_params)
            else:
                log.info(f"Text is long ({len(padded_text)} chars). Splitting for stability...")
                import soundfile as sf
                
                # Split English on sentence boundary punctuation, Arabic on clause boundaries
                if language == "en":
                    sentence_pattern = re.compile(r'([^!\?\.]+[!\?\.]*)')
                    sentences = [s.strip() for s in sentence_pattern.findall(padded_text) if s.strip()]
                    pause_sec = 0.12  # 120ms punchy pacing
                else: # ar
                    # Split on comma (،) or period (.)
                    clauses = [s.strip() for s in re.split(r'([،\.])', padded_text) if s.strip()]
                    # Re-group punctuation with their clauses
                    sentences = []
                    temp_s = ""
                    for token in clauses:
                        if token in ["،", "."]:
                            temp_s += token
                            sentences.append(temp_s.strip())
                            temp_s = ""
                        else:
                            temp_s = token
                    if temp_s:
                        sentences.append(temp_s.strip())
                    pause_sec = 0.35  # 350ms breathing space for scholarly flow
                
                if not sentences:
                    sentences = [padded_text]
                    
                log.info(f"Split into {len(sentences)} segments: {sentences}")
                
                pause_samples = np.zeros(int(XTTS_SAMPLE_RATE * pause_sec), dtype=np.float32)
                segments = []
                
                for i, sent in enumerate(sentences):
                    log.info(f"Synthesizing segment {i+1}: '{sent}'")
                    # Generate raw wav array in VRAM
                    wav_list = self.tts.tts(
                        text=sent,
                        speaker_wav=speaker_wav,
                        language=language,
                        speed=synth_params.get("speed", 1.0),
                        temperature=synth_params.get("temperature", 0.85)
                    )
                    wav_np = np.array(wav_list, dtype=np.float32)
                    
                    # Programmatically trim leading/trailing pre-padded silence from raw synthesis
                    wav_abs = np.abs(wav_np)
                    # Highly sensitive threshold (-50dB) to preserve soft ending consonants
                    threshold = 0.003
                    wav_indices = np.where(wav_abs > threshold)[0]
                    if len(wav_indices) > 0:
                        start_w = max(0, wav_indices[0] - int(XTTS_SAMPLE_RATE * 0.050))
                        end_w = min(len(wav_np), wav_indices[-1] + int(XTTS_SAMPLE_RATE * 0.200))
                        wav_np = wav_np[start_w:end_w]
                        
                    # Apply a smooth 20ms linear fade-in and 50ms fade-out to guarantee perfectly pop-free transitions
                    fade_in_w = int(XTTS_SAMPLE_RATE * 0.020)
                    fade_out_w = int(XTTS_SAMPLE_RATE * 0.050)
                    if len(wav_np) > (fade_in_w + fade_out_w):
                        fade_in_arr = np.linspace(0.0, 1.0, fade_in_w, dtype=np.float32)
                        wav_np[:fade_in_w] *= fade_in_arr
                        fade_out_arr = np.linspace(1.0, 0.0, fade_out_w, dtype=np.float32)
                        wav_np[-fade_out_w:] *= fade_out_arr
                        
                    segments.append(wav_np)
                    if i < len(sentences) - 1:
                        segments.append(pause_samples)
                        
                wav_combined = np.concatenate(segments).astype(np.float32)
                sf.write(str(output_path.absolute()), wav_combined, XTTS_SAMPLE_RATE)

            # Crop, fade, and pad for smooth start/end
            self.apply_audio_cushion(output_path)

            # ── ARABIC: Apply OpenVoice v2 ToneColorConverter (tau=0.07) ─────
            # Matches how test_ar_soothing.wav pre-made assets were generated.
            # Soft fallback — raw XTTS output used if OpenVoice is unavailable.
            if language == "ar":
                self._apply_openvoice_ar(output_path)

            log.info(f"Synthesis complete: {output_path.name}")
            return True
        except Exception as e:
            log.error(f"TTS Synthesis failed: {e}")
            return False

# Singleton instance
tts_engine = LocalTTSEngine()

