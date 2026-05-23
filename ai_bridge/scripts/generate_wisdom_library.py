import os
import json
import time
import httpx
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Config
SCRIPT_DIR = Path(__file__).parent.absolute()
OUT_FILE = SCRIPT_DIR.parent / "data" / "wisdom_templates.json"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY or "your_key" in OPENROUTER_API_KEY:
    print("🛑 ERROR: OPENROUTER_API_KEY not found in .env.")

# The Maulana Wisdom Tree
HIERARCHY = {
    "reception": {
        "greetings": {
            "time_based": ["morning", "afternoon", "evening", "night"],
            "context_based": ["first_visit", "welcome_back_short", "welcome_back_long", "post_hardship"]
        },
        "closures": {
            "standard": ["farewell", "salams", "until_next_time"],
            "encouragement": ["reflection_nudge", "consistency_promise"]
        }
    },
    "pedagogy": {
        "correction": {
            "makharij": ["throat_halqi", "tongue_lisani", "lip_shafawi", "teeth_dars"],
            "sifaat": ["qalqalah_echo", "madd_length", "ghunnah_nasality"]
        },
        "praise": {
            "standard": ["mashallah", "mumtaz", "barakallah"],
            "growth": ["much_improved", "makhraj_mastery", "effort_rewarded"]
        }
    },
    "bridge": {
        "emotional": {
            "stress": ["anxiety", "overwhelmed", "academic_stress"],
            "personal": ["family_issues", "grief_loneliness", "financial_worry"],
            "daily": ["fatigue", "distraction", "morning_determination"]
        },
        "scholarly": {
            "transition": ["fiqh_hook", "seerah_connection", "historical_context"],
            "connection": ["memory_link", "past_session_reference"]
        }
    },
    "tarbiyah": {
        "milestones": {
            "streaks": ["3_day_momentum", "7_day_consistency", "30_day_devotion"],
            "mastery": ["surah_complete", "juz_complete", "first_correct_reading"]
        }
    }
}

LANGUAGES = ["en", "ur", "ar"]

def get_leaf_nodes(d, path=""):
    nodes = []
    for k, v in d.items():
        new_path = f"{path}.{k}" if path else k
        if isinstance(v, dict):
            nodes.extend(get_leaf_nodes(v, new_path))
        elif isinstance(v, list):
            for item in v:
                nodes.append(f"{new_path}.{item}")
    return nodes

def call_openrouter(prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "google/gemini-2.0-flash-001",
        "messages": [{"role": "user", "content": prompt}]
    }
    with httpx.Client(timeout=30) as client:
        resp = client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        return resp.json()['choices'][0]['message']['content']

def generate_templates():
    base_nodes = get_leaf_nodes(HIERARCHY)
    all_nodes = []
    for lang in LANGUAGES:
        for node in base_nodes:
            all_nodes.append(f"{lang}.{node}")
            
    print(f"Found {len(base_nodes)} base nodes across {len(LANGUAGES)} languages.")
    print(f"Total target: {len(all_nodes)} nodes.")
    
    if os.path.exists(OUT_FILE):
        with open(OUT_FILE, "r", encoding="utf-8") as f:
            library = json.load(f)
    else:
        library = {}

    for node_path in all_nodes:
        if node_path in library and len(library[node_path]) >= 10:
            print(f"Skipping {node_path}")
            continue
            
        lang = node_path.split('.')[0]
        node_id = ".".join(node_path.split('.')[1:])
        lang_name = "English" if lang == "en" else "Urdu" if lang == "ur" else "Arabic"
        
        print(f"Generating [{lang_name}] for: {node_id}...")
        
        prompt = f"""
        Act as a wise, scholarly, and warm Quran teacher (Maulana). 
        Generate 10 unique variations of spoken feedback for the category: {node_id}.
        
        LANGUAGE: {lang_name}
        
        CONTEXT: 
        - Market: UK/North India/Gulf.
        - Tone: Spiritually uplifting, empathetic, authoritative yet kind.
        - CRITICAL RULE: For English (en) and Urdu (ur) templates, use ONLY the Latin alphabet (A-Z).
        - TAJWEED INTEGRITY: For Arabic terms inside English/Urdu sentences, use 'Phonetic Spelling' to guide the pronunciation (e.g., write 'Makh-raaj' for depth, 'Qaaff' for resonance, 'Ya bu-nay-ya' for rhythm).
        - For Arabic (ar): Use ONLY Modern Standard Arabic (Fusha) script with full tashkeel (vowels) if possible for maximum clarity.
        - Variations: 3s to 10s.
        - Format: JSON list of 10 strings.
        
        FORMAT: Return ONLY a JSON list of strings.
        """
        
        try:
            text = call_openrouter(prompt)
            # JSON cleanup
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
                
            variations = json.loads(text)
            
            # Sanitize English variations to prevent TTS pauses
            if lang == "en":
                import re
                clean_variations = []
                for v in variations:
                    # Expand Abbreviations for smooth reading
                    v = v.replace("(SWT)", "Subhanahu Wa Ta'ala")
                    v = v.replace("(AS)", "Alayhis Salam")
                    v = v.replace("(RA)", "Radiyallahu Anhu")
                    
                    # Keep only ASCII 32-126
                    clean_v = "".join([c for c in v if 32 <= ord(c) <= 126])
                    
                    # Remove special characters that cause pauses
                    clean_v = re.sub(r'[\*\(\)\[\]]', '', clean_v)
                    clean_v = clean_v.replace("  ", " ").strip()
                    clean_variations.append(clean_v)
                variations = clean_variations
                print(f"VERIFIED CLEAN [EN]: {variations[0][:50]}...")

            library[node_path] = variations
            
            with open(OUT_FILE, "w", encoding="utf-8") as f:
                json.dump(library, f, indent=2)
            
            time.sleep(1) 
        except Exception as e:
            print(f"Error for {node_path}: {e}")

    print(f"DONE: Library complete! Saved to {OUT_FILE}")

if __name__ == "__main__":
    generate_templates()
