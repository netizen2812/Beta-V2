import os
import sys
import json
import time
import re
from pathlib import Path
from dotenv import load_dotenv

# Setup paths
SCRIPT_DIR = Path(__file__).resolve().parent
AI_BRIDGE_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(AI_BRIDGE_DIR))

load_dotenv(dotenv_path=AI_BRIDGE_DIR / ".env")
load_dotenv(dotenv_path=AI_BRIDGE_DIR.parent / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def get_gemini_client():
    if not GEMINI_API_KEY:
        print("[ERROR] GEMINI_API_KEY not found in environment.")
        return None
    try:
        from google import genai
        return genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"⚠️ Failed to init Gemini client: {e}")
        return None

def has_arabic_urdu_char(text):
    return bool(re.search(r'[\u0600-\u06FF]', text))

def translate_category(client, category_key: str, templates: list, target_lang: str) -> list:
    lang_names = {
        "ar": "Arabic (Arabic script with proper harakaat)",
        "ur": "Urdu (Urdu script)"
    }
    target_lang_name = lang_names.get(target_lang, target_lang)
    
    prompt = (
        f"You are a warm, gentle, and highly scholarly Quran teacher (Maulana) and a professional translator.\n"
        f"Translate the following list of Quranic recitation feedback/reflection templates into {target_lang_name}.\n"
        f"Keep the translations warm, encouraging, Islamic, and faithful to the original English meaning.\n"
        f"Return ONLY a valid JSON array of strings in the same order as the input. No markdown wrappers or additional text, just the raw JSON list of strings.\n\n"
        f"Templates:\n{json.dumps(templates, indent=2)}"
    )

    max_retries = 5
    backoff = 6.0
    
    for attempt in range(max_retries):
        try:
            from google.genai import types as genai_types
            response = client.models.generate_content(
                model="gemini-2.0-flash", # Use gemini-2.0-flash as it is fast and reliable
                contents=prompt,
                config=genai_types.GenerateContentConfig(
                    temperature=0.3,
                    response_mime_type="application/json",
                )
            )
            
            text = response.text.strip()
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
                raise ValueError("Invalid format returned")
                
        except Exception as e:
            print(f"[WARNING] Attempt {attempt+1} failed for {category_key} to {target_lang}: {e}")
            if attempt < max_retries - 1:
                time.sleep(backoff)
                backoff *= 1.5
            else:
                print(f"[ERROR] Failed to translate {category_key} to {target_lang} after all attempts.")
                return None

def main():
    client = get_gemini_client()
    if not client:
        print("[ERROR] Cannot proceed: client init failed.")
        sys.exit(1)

    templates_file = AI_BRIDGE_DIR / "data" / "wisdom_templates.json"
    localized_file = AI_BRIDGE_DIR / "data" / "wisdom_templates_localized.json"

    with open(templates_file, "r", encoding="utf-8") as f:
        english_templates = json.load(f)

    if localized_file.exists():
        with open(localized_file, "r", encoding="utf-8") as f:
            localized_data = json.load(f)
    else:
        localized_data = {"en": {}, "ar": {}, "ur": {}}

    # Fill English copy-paste
    for key, val in english_templates.items():
        clean_key = key.replace("en.", "")
        localized_data["en"][clean_key] = val

    modified = False

    for lang in ["ar", "ur"]:
        if lang not in localized_data:
            localized_data[lang] = {}
            
        print(f"\nProcessing language: {lang.upper()}")
        for key, val in english_templates.items():
            clean_key = key.replace("en.", "")
            
            # Check if translation exists and is valid (contains Arabic/Urdu script)
            existing = localized_data[lang].get(clean_key)
            is_valid = existing and len(existing) == len(val) and all(has_arabic_urdu_char(t) for t in existing)
            
            if is_valid:
                print(f"  - Key {clean_key} already fully translated. Skipping.")
                continue
            
            print(f"  + Translating key {clean_key}...")
            translated_list = translate_category(client, clean_key, val, lang)
            if translated_list:
                localized_data[lang][clean_key] = translated_list
                modified = True
                # Write after every successful key to save progress
                with open(localized_file, "w", encoding="utf-8") as f:
                    json.dump(localized_data, f, ensure_ascii=False, indent=2)
                print(f"    Saved translation for {clean_key}.")
                # Delay to prevent rate limit
                time.sleep(4.0)
            else:
                print(f"    Skipping {clean_key} due to error.")
                time.sleep(2.0)

    print("\nTranslation script completed.")

if __name__ == "__main__":
    main()
