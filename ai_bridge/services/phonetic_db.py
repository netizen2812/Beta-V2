"""
Phonetic Reference Database — Buraaq/quran-md-words.

Manages 77,429 word-level phonetic entries from the Buraaq dataset.
Loads from a pre-built JSON cache file. If cache doesn't exist,
run: python scripts/build_phonetic_cache.py

Lookup key: (surah_id, ayah_id) → list of word entries
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).parent.parent / "data"
CACHE_FILE = CACHE_DIR / "phonetic_cache.json"


class PhoneticDB:
    def __init__(self):
        self._data: dict[str, list[dict]] = {}  # "surah:ayah" → [words]
        self.is_loaded = False
        self.total_words = 0
        self.total_ayahs = 0

    def load(self):
        """Load phonetic data from pre-built cache."""
        if CACHE_FILE.exists():
            logger.info(f"📂 Loading phonetic cache from {CACHE_FILE}")
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
                self.total_ayahs = len(self._data)
                self.total_words = sum(len(words) for words in self._data.values())
                self.is_loaded = True
            except json.JSONDecodeError as e:
                logger.error(f"❌ Failed to parse phonetic cache {CACHE_FILE}: {e}")
                self.is_loaded = False
            except Exception as e:
                logger.error(f"❌ Unexpected error loading phonetic cache: {e}")
                self.is_loaded = False
        else:
            logger.warning(
                f"⚠️  Phonetic cache not found at {CACHE_FILE}. "
                f"Run: python scripts/build_phonetic_cache.py"
            )
            self.is_loaded = False

    def get_ayah_phonetics(self, surah_id: int, ayah_id: int) -> list[dict] | None:
        """Get word-level phonetic reference for a specific ayah."""
        return self._data.get(f"{surah_id}:{ayah_id}")

    def get_ayah_phonetic_string(self, surah_id: int, ayah_id: int) -> str | None:
        """Get the full phonetic string for an ayah (words joined by space)."""
        words = self.get_ayah_phonetics(surah_id, ayah_id)
        if words is None:
            return None
        return " ".join(w["word_tr"] for w in words)

    def search_by_ayah_id(self, ayah_id_str: str) -> list[dict] | None:
        """Lookup using string format "surah:ayah" (e.g., "1:1")."""
        return self._data.get(ayah_id_str)
