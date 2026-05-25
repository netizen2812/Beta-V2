import logging
import numpy as np
from Levenshtein import ratio as lev_ratio

logger = logging.getLogger(__name__)

# --- Precision Constants (Maulana Grade) ---
CORRECT_THRESHOLD = 0.95

# Identity Letters (Lahn Khafi prone pairs)
# Both Arabic and common Transliteration characters included
IDENTITY_PAIRS = [
    ('ص', 'س'), ('ط', 'ت'), ('ق', 'ك'),
    ('ذ', 'ز'), ('ث', 'س'), ('ح', 'ه'),
    ('ع', 'ء'), ('ض', 'د'), ('ظ', 'ز'),
    # Transliteration mappings
    ('ṣ', 's'), ('ṭ', 't'), ('q', 'k'),
    ('ḥ', 'h'), ('ʿ', 'ʾ'), ('ḍ', 'd'), ('ẓ', 'z'),
    ('dh', 'z'), ('th', 's')
]

class TajweedScorer:
    @staticmethod
    def _has_identity_swap(actual: str, expected: str) -> bool:
        """Positional check for identity letter swaps (P1.4)."""
        # Character-by-character comparison at aligned positions
        for a_char, e_char in zip(actual, expected):
            if a_char == e_char:
                continue
            for p1, p2 in IDENTITY_PAIRS:
                # Handle single-character pairs
                if len(p1) == 1 and len(p2) == 1:
                    if (e_char == p1 and a_char == p2) or (e_char == p2 and a_char == p1):
                        return True
        
        # Fallback for multi-character transliteration pairs (dh, th)
        # only if the word is highly similar otherwise
        for p1, p2 in [('dh', 'z'), ('th', 's')]:
            if (p1 in expected and p2 in actual) or (p2 in expected and p1 in actual):
                # Using a high similarity guard to ensure they are likely the same word
                if lev_ratio(actual, expected) > 0.8:
                    return True
        return False

    @staticmethod
    def score_temporal_madd(char_durations: list[dict], reference_words: list[dict]) -> list[dict]:
        """
        Calculates temporal scores for Madd (lengthening) rules.
        Returns a list of word-level temporal feedback.
        """
        temporal_feedback = []
        
        # 1. Calculate the 'Base Harakah' (Mean duration of single short vowels)
        short_vowels = [d['frames'] for d in char_durations if d['char'] in ['a', 'i', 'u'] and d['frames'] < 8]
        base_harakah = np.mean(short_vowels) if short_vowels else 5.0 # default 5 frames (~100ms)

        # 2. Map durations to reference words (Simplified alignment)
        # In a production system, we'd use Forced Alignment, here we use position
        char_ptr = 0
        for i, ref in enumerate(reference_words):
            word_tr = ref['word_tr'].lower()
            word_frames = []
            
            # Extract frames for this word's duration (approximate)
            chars_in_word = len(word_tr)
            word_chars = char_durations[char_ptr : char_ptr + chars_in_word]
            char_ptr += chars_in_word
            
            # Check for Madd in transliteration (elongated vowels)
            # e.g., 'aa', 'ii', 'uu' or scholarly markings like 'ā'
            is_madd_required = any(v in word_tr for v in ['aa', 'ii', 'uu', 'ā', 'ī', 'ū'])
            
            word_feedback = {"error": False, "rule": None, "guidance": None}
            
            if is_madd_required:
                # Find the actual duration of the longest vowel in this word
                vowels = [d['frames'] for d in word_chars if d['char'] in ['a', 'i', 'u']]
                actual_madd_frames = max(vowels) if vowels else 0
                
                # Rule: Madd should be at least 2.2x base harakah
                if actual_madd_frames < (base_harakah * 2.2):
                    print(f"      [DEBUG] Madd Short: Word='{word_tr}', Required=True, Actual={actual_madd_frames} frames, Base={base_harakah:.1f}")
                    word_feedback = {
                        "error": True,
                        "rule": "Madd Tabii (Short Lengthening)",
                        "guidance": f"The lengthening was too short ({actual_madd_frames} frames). Ensure it is at least 2 harakat."
                    }
                else:
                    print(f"      [DEBUG] Madd Pass: Word='{word_tr}', Actual={actual_madd_frames} frames")
            
            temporal_feedback.append(word_feedback)
            
        return temporal_feedback

    @staticmethod
    def score_temporal_ghunnah(char_durations: list[dict], reference_words: list[dict]) -> list[dict]:
        """
        Calculates temporal scores for Ghunnah (nasalization) rules.
        """
        temporal_feedback = []
        
        # 1. Calculate Base Harakah
        short_vowels = [d['frames'] for d in char_durations if d['char'] in ['a', 'i', 'u'] and d['frames'] < 8]
        base_harakah = np.mean(short_vowels) if short_vowels else 5.0

        char_ptr = 0
        for i, ref in enumerate(reference_words):
            word_tr = ref['word_tr'].lower()
            chars_in_word = len(word_tr)
            word_chars = char_durations[char_ptr : char_ptr + chars_in_word]
            char_ptr += chars_in_word
            
            # Identify Ghunnah requirements (Noon/Meem Mushaddad or Ikhfa)
            # In simple transliteration, this is often 'nn' or 'mm'
            is_ghunnah_required = any(g in word_tr for g in ['nn', 'mm'])
            
            word_feedback = {"error": False, "rule": None, "guidance": None}
            
            if is_ghunnah_required:
                # Find the duration of Noon or Meem in this word
                nasals = [d['frames'] for d in word_chars if d['char'] in ['n', 'm']]
                actual_ghunnah_frames = max(nasals) if nasals else 0
                
                # Rule: Ghunnah should be ~2 harakat
                if actual_ghunnah_frames < (base_harakah * 1.8):
                    word_feedback = {
                        "error": True,
                        "rule": "Ghunnah (Short Nasalization)",
                        "guidance": f"The Ghunnah was too short ({actual_ghunnah_frames} frames). Hold for 2 counts."
                    }
            
            temporal_feedback.append(word_feedback)
            
        return temporal_feedback

    @staticmethod
    def weighted_similarity(actual, expected):
        """
        Calculate similarity with heavy penalties for identity-letter swaps.
        """
        actual = actual.lower().strip()
        expected = expected.lower().strip()
        
        # Base similarity
        if actual == expected:
            return 1.0
            
        base_sim = lev_ratio(actual, expected)
        
        if TajweedScorer._has_identity_swap(actual, expected):
            # Apply 0.9 penalty (P1.4)
            base_sim *= 0.1
                
        return base_sim

    @staticmethod
    def classify_mistake(actual: str, expected: str, rule: str = None) -> dict:
        """
        Classifies a specific Tajweed mistake with high pedagogical precision.
        """
        actual = actual.lower().strip()
        expected = expected.lower().strip()

        # 1. Check if it is a timing/spectral error (passed via rule)
        if rule:
            r_lower = rule.lower()
            if "madd" in r_lower:
                return {
                    "error_type": "madd_error",
                    "pedagogical_key": "pedagogy.correction.sifaat.madd_length",
                    "description": "Madd (lengthening) duration error"
                }
            elif "ghunnah" in r_lower:
                return {
                    "error_type": "ghunnah_error",
                    "pedagogical_key": "pedagogy.correction.sifaat.ghunnah_nasality",
                    "description": "Ghunnah (nasalization) duration error"
                }
            elif "qalqalah" in r_lower:
                return {
                    "error_type": "qalqalah_error",
                    "pedagogical_key": "pedagogy.correction.sifaat.qalqalah_echo",
                    "description": "Qalqalah (echo) articulation error"
                }

        # 2. Check for vowel / Harakah swaps (e.g. an'amtu instead of an'amta)
        def strip_vowels(s):
            return "".join([c for c in s if c not in "aeiouāīū"])

        if strip_vowels(actual) == strip_vowels(expected) and actual != expected:
            return {
                "error_type": "vowel_change",
                "pedagogical_key": "pedagogy.correction.vowel.vowel_change",
                "description": f"Harakah vowel swap (pronounced '{actual}' instead of '{expected}')"
            }

        # 3. Check for Makhraj Swaps
        # Throat letters (Halqi)
        throat_chars = ['ʿ', 'ḥ', 'ʾ', 'gh', 'kh', 'ع', 'ح', 'ء', 'غ', 'خ']
        # Lip letters (Shafawi)
        lip_chars = ['b', 'm', 'w', 'f', 'ب', 'م', 'و', 'ف']
        # Teeth letters (Dars)
        teeth_chars = ['th', 'dh', 'ث', 'ذ']

        # Find the mismatching character pair
        mismatch_pair = None
        for a, e in zip(actual, expected):
            if a != e:
                mismatch_pair = (a, e)
                break

        if mismatch_pair:
            a_char, e_char = mismatch_pair
            
            # Check throat letters
            if any(c in throat_chars for c in [a_char, e_char]):
                return {
                    "error_type": "throat_halqi",
                    "pedagogical_key": "pedagogy.correction.makharij.throat_halqi",
                    "description": f"Throat Makhraj swap between '{a_char}' and '{e_char}'"
                }
            
            # Check lip letters
            if any(c in lip_chars for c in [a_char, e_char]):
                return {
                    "error_type": "lip_shafawi",
                    "pedagogical_key": "pedagogy.correction.makharij.lip_shafawi",
                    "description": f"Lip Makhraj swap between '{a_char}' and '{e_char}'"
                }

            # Check teeth letters
            if any(c in teeth_chars for c in [a_char, e_char]):
                return {
                    "error_type": "teeth_dars",
                    "pedagogical_key": "pedagogy.correction.makharij.teeth_dars",
                    "description": f"Teeth Makhraj swap between '{a_char}' and '{e_char}'"
                }

        # Default to tongue (Lisani)
        return {
            "error_type": "tongue_lisani",
            "pedagogical_key": "pedagogy.correction.makharij.tongue_lisani",
            "description": f"Tongue Makhraj swap in '{actual}'"
        }

    @staticmethod
    def score_recitation(
        actual_phonetics: list[str],
        reference_words: list[dict],
        temporal_feedback: list[dict] = None
    ) -> dict:
        word_results = []
        total_score = 0.0
        error_summary = {"correct": 0, "minor_error": 0, "major_error": 0}

        num_words = max(len(reference_words), len(actual_phonetics))

        for i in range(num_words):
            ref = reference_words[i] if i < len(reference_words) else None
            act = actual_phonetics[i] if i < len(actual_phonetics) else ""

            if ref is None:
                word_results.append({
                    "word_index": i,
                    "status": "extra_word",
                    "actual_phonetic": act
                })
                continue

            expected = ref["word_tr"]
            actual = act

            if not actual:
                similarity = 0.0
                status = "major_error"
                rule = "Missing Word"
            else:
                similarity = TajweedScorer.weighted_similarity(actual, expected)
                
                # Maulana Feedback Logic
                if similarity >= CORRECT_THRESHOLD:
                    status = "correct"
                    rule = None
                elif similarity >= 0.70:
                    status = "minor_error"
                    rule = "Lahn Khafi (Phonetic Shift)"
                else:
                    status = "major_error"
                    rule = "Lahn Jali (Major Mispronunciation)"

            # Integrate Temporal/Spectral Feedback if provided
            maulana_guidance = None
            if temporal_feedback:
                if isinstance(temporal_feedback, dict):
                    tf = temporal_feedback.get(i)
                elif isinstance(temporal_feedback, list) and i < len(temporal_feedback):
                    tf = temporal_feedback[i]
                else:
                    tf = None

                if tf and tf.get("error"):
                    status = "major_error" # Timing/Spectral errors are major
                    rule = tf["rule"]
                    maulana_guidance = tf["guidance"]
                    # Penalize similarity for precision errors
                    similarity = min(similarity, 0.65) 

            # Classify error details for pedagogy
            error_details = None
            if status != "correct":
                error_details = TajweedScorer.classify_mistake(actual, expected, rule)

            total_score += similarity
            error_summary[status] = error_summary.get(status, 0) + 1

            word_results.append({
                "word_index": ref["word_index"],
                "word_ar": ref["word_ar"],
                "expected_phonetic": expected,
                "actual_phonetic": actual,
                "similarity": round(similarity, 3),
                "status": status,
                "rule": rule,
                "guidance": maulana_guidance,
                "error_details": error_details
            })

        ref_count = len(reference_words)
        tajweed_score = round((total_score / ref_count) * 100, 1) if ref_count > 0 else 0

        # Generate Overall Maulana Feedback
        if tajweed_score >= 95:
            status_text = "Excellent (Mumtaz)"
            guidance = "Your recitation is precise and adheres to the rules of Tajweed."
        elif tajweed_score >= 85:
            status_text = "Good (Jayyid)"
            guidance = "Your recitation is clear, but some minor Lahn Khafi errors were detected. Focus on identity letter attributes."
        else:
            status_text = "Correction Required (Niqis)"
            guidance = "Several Lahn Jali or major timing errors were detected. Please review the highlighted words with a teacher."

        return {
            "maulana_feedback": {
                "status": status_text,
                "score": tajweed_score,
                "guidance": guidance,
                "summary": error_summary
            },
            "word_results": word_results,
            "tajweed_score": tajweed_score
        }
