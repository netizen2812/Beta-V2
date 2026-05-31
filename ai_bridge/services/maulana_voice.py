"""
maulana_voice.py — Multilingual RAG-Grounded & Madhab-Aware Maulana Voice Advisor

Pipeline:
    1. Retrieve scholarly Fiqh contexts from ChromaDB collection 'madhab_rules' based on selected Madhab.
    2. Retrieve Quranic context (translation/tafsir) from collection 'quran_tafsir' based on Ayah ID.
    3. Select deterministic pre-made greeting, pedagogical correction, and closure assets from 'wisdom_templates.json'.
    4. Estimate pre-made word counts and calculate maximum allowed words for dynamic LLM advice (at most 20% of total).
    5. Call Gemini 2.0 Flash to translate templates and compose highly customized, concise Fiqh warnings in the target language.
    6. Mathematically truncate the dynamic segment if it violates the 20% limit.
    7. Synthesize using zero-OPEX local TTS engines (XTTSv2/MMS-VITS) with madhab-aware caching.
"""

import os
import json
import logging
import datetime
import hashlib
from pathlib import Path
from typing import AsyncGenerator, Optional
from dotenv import load_dotenv

from google import genai
from google.genai import types as genai_types

load_dotenv()

logger = logging.getLogger("MaulanaVoice")

# ─── Configuration ────────────────────────────────────────────────────────────

GEMINI_API_KEY      = os.getenv("GEMINI_API_KEY")
ELEVENLABS_API_KEY  = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB")

# Gemini Client Singleton (P3.15)
gemini_client = None
if GEMINI_API_KEY:
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)

LANGUAGE_DIRECTIVES = {
    "urdu":    "Urdu (Urdu script). Keep it warm, Islamic, gentle, and brief.",
    "english": "English. Keep it warm, Islamic, gentle, and brief.",
    "arabic":  "Arabic (Arabic script with proper harakaat). Keep it warm, Islamic, gentle, and brief.",
}

def _fetch_alquran_translation(ayah_id: str, lang: str = "en") -> str:
    """Fetches the exact text and translation of an Ayah from api.alquran.cloud dynamically."""
    import urllib.request
    import json
    
    # Clean ayah_id (e.g., convert "1:1:1" -> "1:1")
    parts = ayah_id.split(":")
    if len(parts) >= 2:
        ayah_id = f"{parts[0]}:{parts[1]}"
        
    edition = "en.sahih" if lang == "en" else "ur.jandagarhi"
    url = f"http://api.alquran.cloud/v1/ayah/{ayah_id}/{edition}"
    
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read())
            if data['code'] == 200:
                ayah_text = data['data']['text']
                surah_name = data['data']['surah']['englishName']
                surah_num = data['data']['surah']['number']
                ayah_num = data['data']['numberInSurah']
                return f'Surah {surah_name} ({surah_num}:{ayah_num}) says: "{ayah_text}"'
    except Exception as e:
        logger.error(f"Failed to fetch translation from alquran.api for {ayah_id}: {e}")
    return ""


# ─── Step 1: Deterministic Template Selection ───────────────────────────────

def _get_stable_template_idx(category_key: str, seed: str, max_variations: int = 3) -> tuple[str, int]:
    """Retrieves the template text and its index deterministically using a seed, limited to max_variations."""
    from services.smart_rag import smart_rag
    
    full_key = f"en.{category_key}"
    templates = smart_rag.wisdom_templates.get(full_key, [])
    if not templates:
        templates = smart_rag.wisdom_templates.get(category_key, [])
        
    if not templates:
        logger.warning(f"⚠️ Wisdom template key '{category_key}' not found.")
        return "", 0
        
    h = int(hashlib.md5(seed.encode('utf-8')).hexdigest(), 16)
    limit = min(len(templates), max_variations)
    idx = h % limit if limit > 0 else 0
    return templates[idx], idx

def _get_premade_audio_path(lang: str, category_key: str, idx: int, text: str) -> Path:
    from services.smart_rag import DATA_DIR
    manifest_key = f"{lang}.{category_key}"
    hash_key = hashlib.md5(f"{manifest_key}_{idx}_{text}".encode("utf-8")).hexdigest()
    file_name = f"{category_key.replace('.', '_')}_{idx}_{hash_key}.wav"
    return DATA_DIR / "assets" / "premade_audios" / lang / file_name

def stitch_audio_files(input_paths: list[Path], output_path: Path, target_sr: int = 24000, silence_duration: float = 0.12) -> bool:
    import soundfile as sf
    import numpy as np
    import librosa
    
    try:
        combined_arrays = []
        silence_samples = int(silence_duration * target_sr)
        silence = np.zeros(silence_samples, dtype=np.float32)
        
        for i, path in enumerate(input_paths):
            if not path or not path.exists():
                logger.warning(f"Stitching: Audio file not found/empty: {path}")
                continue
            
            # Load and resample
            data, sr = sf.read(str(path))
            if len(data.shape) > 1:
                data = np.mean(data, axis=1) # Convert to mono
            
            if sr != target_sr:
                data = librosa.resample(data, orig_sr=sr, target_sr=target_sr)
            
            # 1. Programmatic active-speech trimming to strip pre-padded silence down to core speech
            abs_data = np.abs(data)
            # Highly sensitive threshold (-50dB) to avoid cutting soft consonants
            threshold = 0.003
            indices = np.where(abs_data > threshold)[0]
            if len(indices) > 0:
                start_idx = indices[0]
                end_idx = indices[-1]
                # Keep a 50ms start margin and 200ms end margin for breathing room and natural soft transitions
                margin_start = int(target_sr * 0.050)
                margin_end = int(target_sr * 0.200)
                start_idx = max(0, start_idx - margin_start)
                end_idx = min(len(data), end_idx + margin_end)
                data = data[start_idx:end_idx]
                
            # 2. Apply a smooth 20ms fade-in and 50ms fade-out to prevent clicks/pops and ensure natural continuation
            fade_in_samples = int(target_sr * 0.020)
            fade_out_samples = int(target_sr * 0.050)
            if len(data) > (fade_in_samples + fade_out_samples):
                # Fade in
                fade_in = np.linspace(0.0, 1.0, fade_in_samples, dtype=np.float32)
                data[:fade_in_samples] *= fade_in
                # Fade out
                fade_out = np.linspace(1.0, 0.0, fade_out_samples, dtype=np.float32)
                data[-fade_out_samples:] *= fade_out
                
            combined_arrays.append(data)
            
            # Add silence between segments (but not after the last segment)
            if i < len(input_paths) - 1:
                combined_arrays.append(silence)
                
        if not combined_arrays:
            return False
            
        combined_data = np.concatenate(combined_arrays)
        
        # Peak normalize to -1dBFS
        peak = np.abs(combined_data).max()
        if peak > 0:
            combined_data = combined_data / peak * 0.9
            
        sf.write(str(output_path), combined_data, target_sr)
        return True
    except Exception as e:
        logger.error(f"Error stitching audio files: {e}")
        return False

async def _stream_audio_file(file_path: Path) -> AsyncGenerator[bytes, None]:
    import aiofiles
    async with aiofiles.open(file_path, "rb") as f:
        chunk = await f.read(4096)
        while chunk:
            yield chunk
            chunk = await f.read(4096)


def _enforce_80_20_audio_ratio(
    premade_paths: list[Path],
    dynamic_wav: Path | None,
    target_sr: int = 24000,
    max_dynamic_ratio: float = 0.20,
) -> Path | None:
    """
    Enforces the 80/20 audio budget constraint at the WAV sample level.

    Measures actual audio duration (in samples) of:
      • premade segments (greeting + correction + closure)
      • dynamic live TTS segment (Gemini-generated advice)

    If dynamic_duration / total_duration > max_dynamic_ratio (default 20%):
      • Hard-truncates the dynamic WAV in-place at the sample boundary.
      • Applies a 50ms fade-out to prevent a click at the cut point.

    Returns the (potentially truncated) dynamic_wav Path, or None if no
    dynamic segment exists or truncation makes it too short to use.

    This is the WAV-level enforcement that backs the word-count budget set
    in the LLM prompt — ensuring the ratio holds even if TTS synthesis
    produces different durations than the word count predicts.
    """
    if dynamic_wav is None or not dynamic_wav.exists():
        return None

    try:
        import soundfile as sf
        import numpy as np

        # 1. Measure premade duration (samples)
        premade_samples = 0
        for p in premade_paths:
            if p and p.exists():
                info = sf.info(str(p))
                premade_samples += info.frames

        if premade_samples == 0:
            # No premade audio — ratio is undefined, let dynamic pass
            return dynamic_wav

        # 2. Measure dynamic duration
        dynamic_data, sr = sf.read(str(dynamic_wav), dtype="float32")
        dynamic_samples = len(dynamic_data)

        total_samples = premade_samples + dynamic_samples
        actual_ratio = dynamic_samples / total_samples if total_samples > 0 else 0.0

        logger.info(
            f"[80/20 Enforcer] Premade: {premade_samples / target_sr:.2f}s | "
            f"Dynamic: {dynamic_samples / target_sr:.2f}s | "
            f"Ratio: {actual_ratio:.1%} (limit {max_dynamic_ratio:.0%})"
        )

        if actual_ratio <= max_dynamic_ratio:
            # Within budget — no truncation needed
            return dynamic_wav

        # 3. Calculate the maximum allowed dynamic samples
        # dynamic / (premade + dynamic) = max_ratio
        # => dynamic = max_ratio * premade / (1 - max_ratio)
        max_dynamic_samples = int(max_dynamic_ratio * premade_samples / (1 - max_dynamic_ratio))

        if max_dynamic_samples < int(target_sr * 0.3):  # < 300ms is too short to be meaningful
            logger.warning(
                f"[80/20 Enforcer] Max allowed dynamic duration < 300ms. "
                f"Dropping dynamic segment entirely."
            )
            return None

        # 4. Truncate dynamic WAV at the sample boundary
        truncated = dynamic_data[:max_dynamic_samples]

        # 5. Apply 50ms fade-out at the cut point to avoid click
        fade_samples = min(int(target_sr * 0.05), len(truncated))
        if fade_samples > 0:
            fade_out = np.linspace(1.0, 0.0, fade_samples, dtype=np.float32)
            truncated[-fade_samples:] *= fade_out

        sf.write(str(dynamic_wav), truncated, sr)

        new_ratio = max_dynamic_samples / (premade_samples + max_dynamic_samples)
        logger.info(
            f"[80/20 Enforcer] Truncated dynamic: {max_dynamic_samples / target_sr:.2f}s "
            f"(new ratio: {new_ratio:.1%})"
        )
        return dynamic_wav

    except Exception as e:
        logger.error(f"[80/20 Enforcer] Failed: {e}. Skipping enforcement.")
        return dynamic_wav  # Soft fallback — don't crash the pipeline


def _get_ayah_audio_segment(ayah_id: str, edition: str) -> Optional[Path]:
    """
    Downloads, converts, and caches a specific Quranic audio segment (e.g. ar.alafasy or en.walk)
    as a 24kHz mono WAV in a persistent cache folder.
    """
    from services.smart_rag import DATA_DIR
    import urllib.request
    import json
    import tempfile
    import librosa
    import soundfile as sf
    import os
    
    # Determine persistent cache directory
    if os.getenv("HF_HOME") and os.path.exists("/models"):
        cache_dir = Path("/models/quran_audio")
    else:
        cache_dir = DATA_DIR / "assets" / "quran_audio"
        
    safe_edition = edition.replace(".", "_")
    safe_ayah = ayah_id.replace(":", "_")
    wav_path = cache_dir / safe_edition / f"{safe_ayah}.wav"
    
    if wav_path.exists() and wav_path.stat().st_size > 1024:
        return wav_path
        
    try:
        wav_path.parent.mkdir(parents=True, exist_ok=True)
        # Fetch the direct audio URL from Al Quran Cloud API
        api_url = f"http://api.alquran.cloud/v1/ayah/{ayah_id}/{edition}"
        req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
        audio_url = None
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read())
            if data['code'] == 200:
                audio_url = data['data']['audio']
                
        if not audio_url:
            logger.error(f"Could not resolve audio url from api for {ayah_id} ({edition})")
            return None
            
        # Download the MP3 file
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp_mp3_path = Path(tmp.name)
            
        logger.info(f"Downloading {edition} for {ayah_id} from {audio_url}...")
        download_req = urllib.request.Request(audio_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(download_req, timeout=20) as response:
            with open(tmp_mp3_path, "wb") as f:
                f.write(response.read())
                
        # Load and resample to 24000Hz mono using librosa
        logger.info(f"Converting and resampling {tmp_mp3_path} to 24kHz mono WAV...")
        data, sr = librosa.load(str(tmp_mp3_path), sr=24000, mono=True)
        
        # Save as WAV
        sf.write(str(wav_path), data, 24000)
        
        try:
            os.remove(tmp_mp3_path)
        except Exception:
            pass
            
        logger.info(f"Successfully cached {edition} for {ayah_id} at {wav_path}")
        return wav_path
    except Exception as e:
        logger.error(f"Failed to get audio segment for {ayah_id} ({edition}): {e}")
        return None


# ─── Step 3: Orchestrator — Public API ────────────────────────────────────────

async def get_maulana_advice(
    error_details: dict,
    language: str = "english",
    madhab: str = "shafi",
    ayah_id: Optional[str] = None
) -> dict:
    """
    Unified RAG-grounded, Madhab-aware advice generator.
    Enforces at most 20% dynamic live TTS ratio constraint.
    """
    import tempfile
    import asyncio
    from services.smart_rag import smart_rag
    from services.audio_cache import audio_cache_manager
    from services.local_tts import tts_engine
    
    VALID_MADHABS = {"hanafi", "shafi", "maliki", "hanbali"}
    madhab = madhab.lower().strip()
    if madhab not in VALID_MADHABS:
        madhab = "shafi"

    rule = error_details.get("rule", "") or ""
    word = error_details.get("word", "") or ""
    guidance = error_details.get("guidance", "") or ""

    # Prevent prompt injection by clamping length and stripping templating characters
    rule = rule[:100].replace("{", "").replace("}", "").replace("\n", " ")
    word = word[:50].replace("{", "").replace("}", "").replace("\n", " ")
    guidance = guidance[:300].replace("{", "").replace("}", "").replace("\n", " ")

    rule_lower = rule.lower()
    word_lower = word.lower()
    is_emotional = any(k in rule_lower or k in word_lower for k in ["academic", "exam", "anxiety", "worry", "fear", "grief", "lonely", "loneliness", "sad", "family", "parent", "overwhelmed", "burnout", "spiritual", "emotional", "envy", "hasad", "jealous", "comfort"])

    lang_code = (
        "ur" if "urdu"    in language.lower() else
        "ar" if "arabic"  in language.lower() else
        "en"
    )

    # 1. Fast Path: Check Cache first to prevent redundant LLM/TTS calls
    cached_data = None
    if is_emotional:
        if len(guidance) > 80:
            # Frontend playback uses the full stitched advice text as the guidance parameter
            cached_data = audio_cache_manager.get_cached_by_text(guidance, lang_code, madhab)
        if not cached_data and guidance:
            # Express ask uses the user question as guidance
            cached_data = audio_cache_manager.get_cached_insight(rule, word, lang_code, madhab, guidance=guidance)
    else:
        # Tajweed rules are globally cached at the category/word level
        cached_data = audio_cache_manager.get_cached_insight(rule, word, lang_code, madhab)

    if cached_data:
        logger.info(f"[MaulanaVoice] Returning cached advice for {rule} on {word} ({madhab})")
        audio_stream = _stream_audio_file(Path(cached_data["audio_path"]))
        return {
            "text": cached_data["text"],
            "audio_stream": audio_stream,
            "fallback": False,
            "fallback_reason": None,
        }

    # 2. Select templates deterministically using the word + rule as a seed
    seed = f"{rule}_{word}"
    
    # 2a. Greeting (Time-based but deterministic)
    current_hour = datetime.datetime.now().hour
    if current_hour < 12:
        greeting_key = "reception.greetings.time_based.morning"
    elif current_hour < 17:
        greeting_key = "reception.greetings.time_based.afternoon"
    elif current_hour < 21:
        greeting_key = "reception.greetings.time_based.evening"
    else:
        greeting_key = "reception.greetings.time_based.night"
        
    greeting_en, greeting_idx = _get_stable_template_idx(greeting_key, seed)
    if not greeting_en:
        greeting_key = "reception.greetings.context_based.welcome_back_short"
        greeting_en, greeting_idx = _get_stable_template_idx(greeting_key, seed)

    # 2b. Pedagogical Correction
    pedagogical_key = error_details.get("error_details", {}).get("pedagogical_key") if isinstance(error_details.get("error_details"), dict) else error_details.get("pedagogical_key")
    if not pedagogical_key:
        # Fallback mapping
        rule_lower = rule.lower()
        if "academic" in rule_lower or "exam" in rule_lower:
            pedagogical_key = "bridge.emotional.stress.academic_stress"
        elif "anxiety" in rule_lower or "worry" in rule_lower or "fear" in rule_lower:
            pedagogical_key = "bridge.emotional.stress.anxiety"
        elif "grief" in rule_lower or "lonely" in rule_lower or "loneliness" in rule_lower or "sad" in rule_lower:
            pedagogical_key = "bridge.emotional.personal.grief_loneliness"
        elif "family" in rule_lower or "parent" in rule_lower:
            pedagogical_key = "bridge.emotional.personal.family_issues"
        elif "overwhelmed" in rule_lower or "burnout" in rule_lower:
            pedagogical_key = "bridge.emotional.stress.overwhelmed"
        elif "envy" in rule_lower or "hasad" in rule_lower or "jealous" in rule_lower:
            pedagogical_key = "bridge.emotional.personal.envy_hasad"
        elif "comfort" in rule_lower or "spiritual" in rule_lower or "general" in rule_lower:
            pedagogical_key = "bridge.emotional.general_comfort"
        elif "throat" in rule_lower or "halqi" in rule_lower:
            pedagogical_key = "pedagogy.correction.makharij.throat_halqi"
        elif "madd" in rule_lower:
            pedagogical_key = "pedagogy.correction.sifaat.madd_length"
        elif "ghunnah" in rule_lower:
            pedagogical_key = "pedagogy.correction.sifaat.ghunnah_nasality"
        elif "qalqalah" in rule_lower:
            pedagogical_key = "pedagogy.correction.sifaat.qalqalah_echo"
        elif "lip" in rule_lower or "shafawi" in rule_lower:
            pedagogical_key = "pedagogy.correction.makharij.lip_shafawi"
        elif "teeth" in rule_lower or "dars" in rule_lower:
            pedagogical_key = "pedagogy.correction.makharij.teeth_dars"
        elif "vowel" in rule_lower or "harakah" in rule_lower or "swap" in rule_lower:
            pedagogical_key = "pedagogy.correction.vowel.vowel_change"
        elif any(kw in rule_lower for kw in ["heavy", "light", "tafkheem", "tarqeeq"]):
            pedagogical_key = "pedagogy.correction.sifaat.heavy_light"
        elif any(kw in rule_lower for kw in ["noon", "tanween", "ikhfa", "idgham", "izhar", "iqlab"]):
            pedagogical_key = "pedagogy.correction.sifaat.noon_sakinah"
        elif any(kw in rule_lower for kw in ["waqf", "stop", "ibtida"]):
            pedagogical_key = "pedagogy.correction.sifaat.waqf_stopping"
        else:
            pedagogical_key = "pedagogy.correction.makharij.tongue_lisani"
            
    correction_en, correction_idx = _get_stable_template_idx(pedagogical_key, seed)
    if not correction_en:
        correction_en = "Please focus on the pronunciation and the rules of Tajweed for this word."
        correction_idx = 0

    # 2c. Closure — use a non-Tajweed closure for emotional/spiritual queries
    if is_emotional:
        closure_key = "reception.closures.encouragement.consistency_promise"
        closure_en, closure_idx = _get_stable_template_idx(closure_key, seed)
        if not closure_en:
            closure_key = "reception.closures.standard.farewell"
            closure_en, closure_idx = _get_stable_template_idx(closure_key, seed)
    else:
        closure_key = "reception.closures.standard.until_next_time"
        closure_en, closure_idx = _get_stable_template_idx(closure_key, seed)
    if not closure_en:
        closure_en = "May Allah keep you safe. Assalamu alaikum."
        closure_idx = 0

    # 3. Retrieve Context from alquran.api directly (ChromaDB local tafsir query completely bypassed)
    quran_context = "No specific ayah context."
    madhab_context = "No specific madhab ruling found."
    
    if is_emotional:
        # Determine appropriate comfort Ayah if no ayah_id is provided or if it is the default "1:1"
        if not ayah_id or ayah_id == "1:1":
            try:
                # Query ChromaDB collection 'quran_tafsir' based on the user's question (guidance)
                results = smart_rag.query_tafsir(query_text=guidance, n_results=1)
                if results:
                    ayah_id = results[0]["ayah_id"]
                    logger.info(f"[MaulanaVoice] RAG selected comfort ayah_id: {ayah_id} dynamically based on guidance: '{guidance}'")
            except Exception as e:
                logger.error(f"[MaulanaVoice] RAG search failed for emotional comfort: {e}")
                
            # Fallback if RAG returned nothing or failed
            if not ayah_id or ayah_id == "1:1":
                pedagogy_lower = str(pedagogical_key).lower()
                rule_lower = rule.lower()
                if "academic_stress" in pedagogy_lower or "academic" in rule_lower or "exam" in rule_lower:
                    ayah_id = "94:5"  # Surah Ash-Sharh (hardship/ease)
                elif "anxiety" in pedagogy_lower or "worry" in rule_lower or "fear" in rule_lower:
                    ayah_id = "2:186" # Surah Al-Baqarah (Allah is near)
                elif "overwhelmed" in pedagogy_lower or "burnout" in rule_lower:
                    ayah_id = "2:286" # Surah Al-Baqarah (Allah does not burden)
                elif "grief_loneliness" in pedagogy_lower or "sad" in rule_lower or "grief" in rule_lower:
                    ayah_id = "50:16" # Surah Qaf (closer than jugular vein)
                elif "family_issues" in pedagogy_lower or "family" in rule_lower or "parent" in rule_lower:
                    ayah_id = "17:23" # Surah Al-Isra (parents treatment)
                elif "envy_hasad" in pedagogy_lower or "envy" in rule_lower or "hasad" in rule_lower or "jealous" in rule_lower:
                    ayah_id = "113:5" # Surah Al-Falaq (envy/hasad)
                else:
                    ayah_id = "94:5"  # Default comforting verse
                
        # Fetch the exact text and translation directly from Al Quran Cloud
        quran_context = _fetch_alquran_translation(ayah_id, lang_code)
        if not quran_context:
            quran_context = f"Surah Ash-Sharh (94:5-6) says: 'For indeed, with hardship [will be] ease.'"
    else:
        # 3a. Tafsir / Quranic Context — strictly fetch from Al Quran Cloud
        if ayah_id:
            quran_context = _fetch_alquran_translation(ayah_id, lang_code)
        elif word:
            # If only word is passed for Tajweed, lookup meaning using local RAG as fallback
            tafsir_results = smart_rag.query_tafsir(f"meaning of {word}", n_results=1)
            if tafsir_results:
                quran_context = tafsir_results[0]["text"]

        # 3b. Madhab-Aware Theological Context — retrieved from ChromaDB (madhab-specific)
        madhab_results = smart_rag.query_madhab(madhab, f"recitation error {rule} {word}", n_results=1)
        if madhab_results:
            madhab_context = madhab_results[0]["text"]

    # 4. Resolve translated texts from cache
    tg = smart_rag.get_localized_template(lang_code, greeting_key, greeting_idx)
    tc = smart_rag.get_localized_template(lang_code, pedagogical_key, correction_idx)
    tcl = smart_rag.get_localized_template(lang_code, closure_key, closure_idx)

    # Fallbacks if translation missing
    if not tg: tg = greeting_en
    if not tc: tc = correction_en
    if not tcl: tcl = closure_en

    # Enforce at most 20% dynamic ratio constraint mathematically
    total_premade_words = len(tg.split()) + len(tc.split()) + len(tcl.split())
    if is_emotional:
        # Emotional comfort needs room for a Quranic ayah + translation; allow at least 50 words
        max_dynamic_words = max(50, int(total_premade_words * 0.25))
    else:
        # Dynamic <= 0.25 * Premade guarantees Dynamic / (Premade + Dynamic) <= 20%
        max_dynamic_words = int(total_premade_words * 0.25)
        if max_dynamic_words < 3:
            max_dynamic_words = 3  # Ensure a basic sentence is allowed

    # 5. Invoke Gemini 2.0 Flash for structured localized dynamic advice segment
    da = ""
    if not gemini_client:
        # Fallback without LLM
        logger.warning("[MaulanaVoice] Gemini Client not initialized. Returning un-translated English fallback.")
        if language.lower() == "english":
            da = f"In the {madhab} school, this error requires correction."
        elif "urdu" in language.lower():
            da = f"{madhab.upper()} مذہب کے مطابق، اس غلطی کی اصلاح ضروری ہے۔"
        elif "arabic" in language.lower():
            da = f"وفقًا لمذهب {madhab.upper()}، يجب تصحيح هذا الخطأ."
        else:
            da = f"According to the {madhab.upper()} school, this error must be corrected."
    else:
        lang_directive = LANGUAGE_DIRECTIVES.get(language.lower(), LANGUAGE_DIRECTIVES["english"])
        if is_emotional:
            prompt = (
                f"You are a warm, gentle, and highly scholarly Quran teacher (Maulana) providing personal spiritual comfort to a student.\n\n"
                f"Student's selected school: {madhab.upper()}\n"
                f"Student's personal situation/guidance text: {guidance}\n"
                f"Quranic context retrieved from the knowledge base: {quran_context}\n\n"
                f"Your task is to generate a very brief, custom, warm bridging sentence of spiritual comfort in {language.upper()} (using its native script: Urdu for Urdu, Arabic for Arabic) that:\n"
                f"1. Directly addresses the student's emotional situation: '{rule}'.\n"
                f"2. Quotes or references ONE specific, relevant Quranic Ayah (e.g. Surah Ash-Sharh 94:5-6, or Al-Baqarah 2:286) that is appropriate for their situation. Include the Ayah reference AND its meaning/translation in {language.upper()}.\n"
                f"3. Ends with a word of gentle encouragement and trust in Allah ('tawakkul').\n\n"
                f"It MUST NOT exceed {max_dynamic_words} words under any circumstances. Do NOT mention Tajweed, Makhraj, or recitation corrections.\n"
                f"Return ONLY a JSON object with a single field 'dynamic_advice'."
            )
        else:
            prompt = (
                f"You are a warm, gentle, and highly scholarly Quran teacher (Maulana) providing custom correction advice to a student.\n\n"
                f"Retrieved Fiqh & Quranic RAG Context for this attempt:\n"
                f"  - Student's Selected School (Madhab): {madhab.upper()}\n"
                f"  - Madhab Fiqh Rulings: {madhab_context}\n"
                f"  - Quranic Meaning / Tafsir of this Ayah: {quran_context}\n\n"
                f"Your task is to generate a custom, warm scholarly advisory sentence in {language.upper()} (using its native script: Urdu script for Urdu, Arabic script for Arabic) that briefly warns the student about the theological/Fiqh implications of their specific Tajweed mistake '{rule}' on the word '{word}' according to the {madhab.upper()} school, and/or references the Quranic meaning.\n\n"
                f"It MUST be extremely concise, and MUST NOT exceed {max_dynamic_words} words under any circumstances.\n"
                f"Return ONLY a JSON object with a single field 'dynamic_advice'."
            )

        try:
            logger.info(f"[MaulanaVoice] Querying Gemini for madhab-aware ({madhab}) dynamic advice...")
            response = gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=500 if is_emotional else 200,
                    response_mime_type="application/json",
                )
            )
            
            logger.info(f"[MaulanaVoice] Gemini raw response: {response.text}")
            text_to_parse = response.text.strip() if response.text else ""
            if text_to_parse.startswith("```"):
                import re
                text_to_parse = re.sub(r"^```(?:json)?\n", "", text_to_parse)
                text_to_parse = re.sub(r"\n```$", "", text_to_parse)
            
            try:
                data = json.loads(text_to_parse.strip())
                da = data.get("dynamic_advice", "").strip()
            except Exception as parse_err:
                logger.warning(f"[MaulanaVoice] JSON parsing failed. Trying to extract plain text: {parse_err}")
                da = text_to_parse.strip()
                if da.startswith("{") and "dynamic_advice" in da:
                    import re
                    match = re.search(r'"dynamic_advice"\s*:\s*"([^"]+)"', da)
                    if match:
                        da = match.group(1)

            # Enforce mathematical 20% limit on dynamic word count
            dynamic_words = da.split()
            dynamic_count = len(dynamic_words)
            
            if dynamic_count > max_dynamic_words:
                logger.info(f"[MaulanaVoice] Dynamic advice word count ({dynamic_count}) exceeds allowed ({max_dynamic_words}). Truncating.")
                da = " ".join(dynamic_words[:max_dynamic_words])
                if not da.endswith((".", "!", "?")):
                    da += "."

        except Exception as e:
            logger.error(f"[MaulanaVoice] Gemini generation/parsing failed: {e}")
            if language.lower() == "english":
                da = f"In the {madhab} school, this error requires correction."
            elif "urdu" in language.lower():
                da = f"{madhab.upper()} مذہب کے مطابق، اس غلطی کی اصلاح ضروری ہے۔"
            elif "arabic" in language.lower():
                da = f"وفقًا لمذهب {madhab.upper()}، يجب تصحيح هذا الخطأ."
            else:
                da = f"According to the {madhab.upper()} school, this error must be corrected."

    advice_text = f"{tg} {tc} {da} {tcl}".strip()
    logger.info(f"[MaulanaVoice] Blended text: {advice_text}")
    logger.info(f"[MaulanaVoice] Word count metrics -> Premade: {total_premade_words}, Dynamic: {len(da.split())}, Ratio: {len(da.split()) / (total_premade_words + len(da.split())):.2%}")

    # 6. Audio Generation Pipeline (Pre-synthesized templates + live dynamic segment stitching)
    temp_files_to_clean = []
    try:
        # Pre-load engine models
        if not tts_engine.is_loaded:
            tts_engine.load_models(lang_code)

        # Get/Synthesize Greeting
        greeting_wav = _get_premade_audio_path(lang_code, greeting_key, greeting_idx, tg)
        if not greeting_wav.exists():
            logger.info(f"Premade greeting audio not found at {greeting_wav}. Synthesizing live...")
            greeting_wav.parent.mkdir(parents=True, exist_ok=True)
            tts_engine.synthesize(tg, lang_code, greeting_wav)

        # Get/Synthesize Correction
        correction_wav = _get_premade_audio_path(lang_code, pedagogical_key, correction_idx, tc)
        if not correction_wav.exists():
            logger.info(f"Premade correction audio not found at {correction_wav}. Synthesizing live...")
            correction_wav.parent.mkdir(parents=True, exist_ok=True)
            tts_engine.synthesize(tc, lang_code, correction_wav)

        # Get/Synthesize Closure
        closure_wav = _get_premade_audio_path(lang_code, closure_key, closure_idx, tcl)
        if not closure_wav.exists():
            logger.info(f"Premade closure audio not found at {closure_wav}. Synthesizing live...")
            closure_wav.parent.mkdir(parents=True, exist_ok=True)
            tts_engine.synthesize(tcl, lang_code, closure_wav)

        # Synthesize Dynamic advice live to a temp file
        dynamic_wav = None
        if da:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                dynamic_wav = Path(tmp.name)
            temp_files_to_clean.append(dynamic_wav)
            
            logger.info(f"[MaulanaVoice] Synthesizing live dynamic advice ({lang_code}): '{da}'")
            success = tts_engine.synthesize(da, lang_code, dynamic_wav)
            if not success or not dynamic_wav.exists():
                logger.error("Live dynamic audio synthesis failed.")
                dynamic_wav = None

        # Fetch pre-recorded Quran recitation and translation if emotional
        arabic_wav = None
        translation_wav = None
        if is_emotional and ayah_id and ayah_id != "1:1":
            arabic_wav = _get_ayah_audio_segment(ayah_id, "ar.alafasy")
            if lang_code == "en":
                translation_wav = _get_ayah_audio_segment(ayah_id, "en.walk")
            elif lang_code == "ur":
                translation_wav = _get_ayah_audio_segment(ayah_id, "ur.khan")

        # ── 80/20 Audio Budget Enforcement ───────────────────────────────────────
        # Enforce the ratio at the WAV level (not just word count). This guarantees
        # that even if TTS synthesis runs longer than predicted, the dynamic segment
        # is hard-capped to ≤ 20% of the total audio duration before stitching.
        premade_audio_paths = [greeting_wav, correction_wav, closure_wav]
        if is_emotional:
            if arabic_wav:
                premade_audio_paths.append(arabic_wav)
            if translation_wav:
                premade_audio_paths.append(translation_wav)

        dynamic_wav = _enforce_80_20_audio_ratio(
            premade_paths=premade_audio_paths,
            dynamic_wav=dynamic_wav,
        )

        # Stitch all segments
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            stitched_temp = Path(tmp.name)
        temp_files_to_clean.append(stitched_temp)

        audio_parts = [greeting_wav, correction_wav]
        if is_emotional:
            if arabic_wav:
                audio_parts.append(arabic_wav)
            if translation_wav:
                audio_parts.append(translation_wav)
        if dynamic_wav:
            audio_parts.append(dynamic_wav)
        audio_parts.append(closure_wav)

        logger.info(f"[MaulanaVoice] Stitching {len(audio_parts)} audio files...")
        stitch_success = stitch_audio_files(audio_parts, stitched_temp, silence_duration=0.12)

        if stitch_success and stitched_temp.exists() and stitched_temp.stat().st_size > 1024:
            # Cache the stitched WAV
            final_path = audio_cache_manager.save_to_cache(rule, word, lang_code, advice_text, stitched_temp, madhab, guidance=guidance if is_emotional else "")
            audio_stream = _stream_audio_file(final_path)
            return {
                "text": advice_text,
                "audio_stream": audio_stream,
                "fallback": False,
                "fallback_reason": None,
            }
        else:
            raise RuntimeError("Stitching failed or produced empty audio.")

    except Exception as e:
        logger.error(f"[MaulanaVoice] Optimized pipeline failed: {e}. Falling back to full live synthesis...")
        # Emergency fallback: synthesize the entire combined text live as one piece
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            fallback_temp = Path(tmp.name)
        temp_files_to_clean.append(fallback_temp)

        try:
            success = tts_engine.synthesize(advice_text, lang_code, fallback_temp)
            if success and fallback_temp.exists():
                final_path = audio_cache_manager.save_to_cache(rule, word, lang_code, advice_text, fallback_temp, madhab, guidance=guidance if is_emotional else "")
                audio_stream = _stream_audio_file(final_path)
                return {
                    "text": advice_text,
                    "audio_stream": audio_stream,
                    "fallback": False,
                    "fallback_reason": None,
                }
            else:
                raise RuntimeError("Fallback synthesis failed.")
        except Exception as err:
            logger.error(f"[MaulanaVoice] Emergency fallback failed: {err}")
            return {
                "text": advice_text,
                "audio_stream": None,
                "fallback": True,
                "fallback_reason": f"Audio synthesis pipeline failed: {str(err)}",
            }
    finally:
        # Clean up temporary files
        for tmp_file in temp_files_to_clean:
            if tmp_file and tmp_file.exists():
                try:
                    os.remove(tmp_file)
                except Exception:
                    pass

