import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Path to Tadabur metadata (to be provided by user or downloaded)
TADABUR_PATH = Path(__file__).parent.parent / "data" / "tadabur_metadata.json"

class TemporalEngine:
    def __init__(self):
        self.metadata = {}
        self._load_metadata()

    def _load_metadata(self):
        if TADABUR_PATH.exists():
            try:
                with open(TADABUR_PATH, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
                logger.info(f"✅ Loaded Tadabur metadata for {len(self.metadata)} ayahs")
            except Exception as e:
                logger.error(f"❌ Failed to load Tadabur metadata: {e}")
        else:
            logger.warning(f"⚠️ Tadabur metadata not found at {TADABUR_PATH}. Temporal validation disabled.")

    def validate_durations(self, ayah_id, user_word_timings):
        """
        Validate word durations against Tadabur Gold Standard.
        
        Args:
            ayah_id: "surah:ayah"
            user_word_timings: list of {"word_index": i, "duration": float}
            
        Returns:
            list of {"word_index": i, "error": bool, "rule": str, "guidance": str}
        """
        gold_standard = self.metadata.get(ayah_id)
        if not gold_standard:
            return []

        feedback = []
        for i, user_timing in enumerate(user_word_timings):
            gold_word = gold_standard["words"][i] if i < len(gold_standard["words"]) else None
            if not gold_word:
                continue

            user_dur = user_timing["duration"]
            gold_dur = gold_word["duration"]
            is_madd = gold_word.get("is_madd", False)
            
            # Tajweed count (haraka) conversion (P1.5)
            HARAKA_SECONDS = 0.30  
            user_counts = round(user_dur / HARAKA_SECONDS, 1)
            gold_counts = round(gold_dur / HARAKA_SECONDS, 1)

            # Logic: Trigger error if user duration is significantly shorter than gold standard
            if is_madd and user_dur < (0.8 * gold_dur):
                feedback.append({
                    "word_index": i,
                    "error": True,
                    "rule": "Madd Tabee'i",
                    "guidance": f"Elongate for at least {gold_counts:.0f} counts; you held it for {user_counts:.1f}."
                })
            else:
                feedback.append({"word_index": i, "error": False})

        return feedback
