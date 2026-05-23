"""
generate_premade_audios.py — Static Template Translation & Audio Pre-Synthesis Script

Steps:
  1. Load wisdom_templates.json (contains English templates).
  2. Batch-translate all English templates to Arabic (ar) and Urdu (ur)
     using Gemini 2.0 Flash, saving the results in wisdom_templates_localized.json.
  3. Pre-synthesize the first N variations of each template category into high-quality WAVs
     using XTTSv2 (for en, ar) and MMS-VITS (for ur).
  4. Write the mapping of these files to asset_manifest.json.
"""

import os
import sys
import json
import hashlib
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Setup paths
SCRIPT_DIR = Path(__file__).resolve().parent
AI_BRIDGE_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(AI_BRIDGE_DIR))

load_dotenv(dotenv_path=AI_BRIDGE_DIR / ".env")
load_dotenv(dotenv_path=AI_BRIDGE_DIR.parent / ".env")

# ─── Configuration ────────────────────────────────────────────────────────────
MAX_VARIATIONS = 10  # Synthesize all 10 templates for full production coverage
LANGUAGES = ["en", "ar", "ur"]

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ─── Translating templates using Gemini ────────────────────────────────────────

QUOTA_EXCEEDED = False

def get_gemini_client():
    if not GEMINI_API_KEY:
        print("[WARNING] GEMINI_API_KEY not found in environment. Skipping translation generation.")
        return None
    try:
        from google import genai
        return genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"⚠️ Failed to init Gemini client: {e}")
        return None

async def translate_category(client, category_key: str, templates: list, target_lang: str) -> list:
    """Translates a batch of templates using Gemini 2.0 Flash with exponential backoff retries."""
    global QUOTA_EXCEEDED
    if target_lang == "en":
        return templates

    if QUOTA_EXCEEDED:
        print(f"[WARNING] Gemini API Quota already exceeded. Instantly using English fallback for {category_key} in {target_lang}.")
        return templates

    lang_names = {
        "ar": "Arabic (Arabic script with proper harakaat)",
        "ur": "Urdu (Urdu script)"
    }
    
    target_lang_name = lang_names.get(target_lang, target_lang)
    
    prompt = (
        f"You are a warm, gentle, and highly scholarly Quran teacher (Maulana) and a professional translator.\n"
        f"Translate the following list of Quranic recitation feedback templates into {target_lang_name}.\n"
        f"Keep the translations warm, encouraging, Islamic, and faithful to the original English meaning.\n"
        f"Return ONLY a valid JSON array of strings in the same order as the input. No markdown wrappers or additional text, just the raw JSON list of strings.\n\n"
        f"Templates:\n{json.dumps(templates, indent=2)}"
    )

    max_retries = 6
    backoff = 4.0
    
    for attempt in range(max_retries):
        try:
            from google.genai import types as genai_types
            response = await asyncio.to_thread(
                client.models.generate_content,
                model="gemini-3.5-flash",
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    temperature=0.3,
                    response_mime_type="application/json",
                )
            )
            
            # Extract JSON from response
            text = response.text.strip()
            # Basic cleaning if markdown code fences exist
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            
            translated = json.loads(text)
            if isinstance(translated, list) and len(translated) == len(templates):
                return [str(t).strip() for t in translated]
            else:
                print(f"[WARNING] Invalid format returned for {category_key} in {target_lang} on attempt {attempt+1}. Content: {text[:200]}")
                raise ValueError("Invalid format returned")
                
        except Exception as e:
            err_str = str(e)
            is_quota_limit = "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str
            is_rate_limit = "429" in err_str or "Rate limit" in err_str or is_quota_limit
            
            if is_quota_limit:
                print(f"[ERROR] Gemini API Quota exceeded persistently! Fast-failing translations to save time.")
                QUOTA_EXCEEDED = True
                return templates

            if is_rate_limit and attempt < max_retries - 1:
                print(f"[INFO] Rate limit hit for {category_key} to {target_lang} (Attempt {attempt+1}/{max_retries}). Retrying in {backoff:.1f}s...")
                await asyncio.sleep(backoff)
                backoff *= 2.0  # Exponential backoff
            else:
                print(f"[ERROR] Failed to translate {category_key} to {target_lang} on attempt {attempt+1}: {e}")
                if attempt == max_retries - 1:
                    print(f"[WARNING] Reverting to English templates for {category_key} in {target_lang} as fallback.")
                    return templates
                await asyncio.sleep(2.0)  # brief pause before retry for other errors

async def build_localized_templates(client, english_templates: dict, localized_path: Path) -> dict:
    """Builds the complete localized templates dictionary and saves it."""
    if localized_path.exists():
        try:
            with open(localized_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Verify we have all languages
                if all(lang in data for lang in LANGUAGES):
                    print("[INFO] Found existing wisdom_templates_localized.json.")
                    return data
        except Exception:
            pass

    print("[INFO] Translating wisdom templates to all target languages...")
    localized = {lang: {} for lang in LANGUAGES}
    
    # English is copy-paste
    for key, val in english_templates.items():
        clean_key = key.replace("en.", "")
        localized["en"][clean_key] = val

    # Translate to other languages
    for lang in ["ar", "ur"]:
        print(f"[INFO] Translating to {lang.upper()}...")
        for key, val in english_templates.items():
            clean_key = key.replace("en.", "")
            translated_list = await translate_category(client, clean_key, val, lang)
            localized[lang][clean_key] = translated_list
            if not QUOTA_EXCEEDED:
                await asyncio.sleep(4.0) # increased delay to avoid hitting rate limits

    # Save it
    with open(localized_path, "w", encoding="utf-8") as f:
        json.dump(localized, f, ensure_ascii=False, indent=2)
    print(f"[INFO] Saved localized templates to {localized_path.name}")
    return localized

# ─── Synthesizing audio assets ────────────────────────────────────────────────

def synthesize_assets(localized_templates: dict, manifest_path: Path, output_dir: Path):
    """Iterates through localized templates and generates WAV files."""
    from services.local_tts import tts_engine
    
    print("[INFO] Starting TTS pre-synthesis of template audio assets...")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    manifest = {}
    if manifest_path.exists():
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        except Exception:
            pass

    # Ensure local tts is imported and configured
    total_files = 0
    generated_files = 0

    for lang in LANGUAGES:
        lang_dir = output_dir / lang
        lang_dir.mkdir(parents=True, exist_ok=True)
        
        # Load local models for this language
        print(f"[INFO] Loading models for language: {lang.upper()}")
        lang_code = "ur" if lang == "ur" else "ar" if lang == "ar" else "en"
        try:
            tts_engine.load_models(lang_code)
        except Exception as e:
            print(f"[WARNING] Could not load model for {lang}: {e}. Skipping audio synthesis for {lang}.")
            continue

        categories = localized_templates.get(lang, {})
        for category_key, templates in categories.items():
            manifest_key = f"{lang}.{category_key}"
            if manifest_key not in manifest:
                manifest[manifest_key] = []
            
            # Synthesize only up to MAX_VARIATIONS
            variations_to_run = templates[:MAX_VARIATIONS]
            for idx, text in enumerate(variations_to_run):
                # Unique filename hash
                hash_key = hashlib.md5(f"{manifest_key}_{idx}_{text}".encode("utf-8")).hexdigest()
                file_name = f"{category_key.replace('.', '_')}_{idx}_{hash_key}.wav"
                file_path = lang_dir / file_name
                
                total_files += 1
                
                # Check if already synthesized
                if file_path.exists() and file_path.stat().st_size > 1024:
                    # File exists and is not empty, update manifest path
                    rel_path = f"data/assets/premade_audios/{lang}/{file_name}"
                    if rel_path not in manifest[manifest_key]:
                        manifest[manifest_key].append(rel_path)
                    continue

                print(f"[INFO] Synthesizing ({lang.upper()}) {category_key} [{idx+1}/{len(variations_to_run)}]...")
                success = tts_engine.synthesize(text, lang_code, file_path)
                if success and file_path.exists():
                    rel_path = f"data/assets/premade_audios/{lang}/{file_name}"
                    if rel_path not in manifest[manifest_key]:
                        manifest[manifest_key].append(rel_path)
                    generated_files += 1
                else:
                    print(f"[ERROR] Failed to synthesize: {category_key} variation {idx}")

        # Unload models for this language to free up RAM/VRAM
        print(f"[INFO] Unloading models for language: {lang.upper()}")
        try:
            tts_engine.unload_all_models()
        except Exception as e:
            print(f"[WARNING] Failed to unload models for {lang}: {e}")

    # Write manifest back
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        
    print(f"[INFO] Audio Synthesis Stats: {generated_files} files generated, {total_files - generated_files} skipped (cached).")
    print(f"[INFO] Saved updated manifest to {manifest_path.name}")

# ─── Main Execution ───────────────────────────────────────────────────────────

async def main():
    templates_file = AI_BRIDGE_DIR / "data" / "wisdom_templates.json"
    localized_file = AI_BRIDGE_DIR / "data" / "wisdom_templates_localized.json"
    manifest_file = AI_BRIDGE_DIR / "data" / "asset_manifest.json"
    audio_output_dir = AI_BRIDGE_DIR / "data" / "assets" / "premade_audios"

    if not templates_file.exists():
        print(f"[ERROR] Error: English templates file not found at {templates_file}")
        sys.exit(1)

    with open(templates_file, "r", encoding="utf-8") as f:
        english_templates = json.load(f)

    # 1. Translation Bootstrap
    client = get_gemini_client()
    if not client and not localized_file.exists():
        print("[ERROR] Cannot proceed: localized file missing and GEMINI_API_KEY unavailable for translation.")
        sys.exit(1)
        
    localized_templates = await build_localized_templates(client, english_templates, localized_file)
    
    # 2. Synthesis
    synthesize_assets(localized_templates, manifest_file, audio_output_dir)

if __name__ == "__main__":
    asyncio.run(main())
