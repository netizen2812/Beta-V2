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

LONG_VOWELS = {'ā', 'ū', 'ī'}
HAMZAH_CHARS = {"'", 'ʾ'}
MUSHADDAD_DOUBLES = ['nn', 'mm', 'll', 'rr', 'ss', 'tt', 'dd', 'bb']
GHUNNAH_IDGHAM_LETTERS = {'y', 'w', 'n', 'm'}
IZHAAR_LETTERS = {'ʾ', 'h', 'ʿ', 'ḥ', 'gh', 'kh'}

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
    def _align_chars(actual: str, reference: str, gap_penalty: float = -1.5) -> list[int]:
        N = len(actual)
        M = len(reference)
        if N == 0 or M == 0:
            return [-1] * N

        dp = np.zeros((N + 1, M + 1))
        backtrack = np.zeros((N + 1, M + 1), dtype=int)
        
        match_score = 2
        mismatch_penalty = -1

        for i in range(1, N + 1):
            dp[i][0] = i * gap_penalty
            backtrack[i][0] = 1
        for j in range(1, M + 1):
            dp[0][j] = j * gap_penalty
            backtrack[0][j] = 2

        for i in range(1, N + 1):
            a_char = actual[i-1]
            for j in range(1, M + 1):
                r_char = reference[j-1]
                score_match = match_score if a_char == r_char else mismatch_penalty
                
                s_match = dp[i-1][j-1] + score_match
                s_ins = dp[i-1][j] + gap_penalty
                s_del = dp[i][j-1] + gap_penalty

                val = max(s_match, s_ins, s_del)
                dp[i][j] = val

                if val == s_match:
                    backtrack[i][j] = 0
                elif val == s_ins:
                    backtrack[i][j] = 1
                else:
                    backtrack[i][j] = 2

        i, j = N, M
        alignment = [-1] * N
        while i > 0 or j > 0:
            if i == 0:
                j -= 1
            elif j == 0:
                alignment[i-1] = -1
                i -= 1
            else:
                choice = backtrack[i][j]
                if choice == 0:
                    alignment[i-1] = j - 1
                    i -= 1
                    j -= 1
                elif choice == 1:
                    alignment[i-1] = -1
                    i -= 1
                else:
                    j -= 1
        return alignment

    @staticmethod
    def classify_madd_type(word_tr: str, next_word_tr: str = "") -> tuple[str, int]:
        word_tr = word_tr.lower().strip()
        next_word_tr = next_word_tr.lower().strip()
        best_type = None
        max_beats = 0
        
        for idx, char in enumerate(word_tr):
            if char in LONG_VOWELS:
                rest = word_tr[idx+1:]
                if any(d in rest for d in MUSHADDAD_DOUBLES):
                    m_type, beats = 'laazim', 6
                elif any(h in rest for h in HAMZAH_CHARS):
                    m_type, beats = 'muttasil', 4
                else:
                    clean_rest = "".join([c for c in rest if c.isalnum() or c in LONG_VOWELS])
                    if not clean_rest:
                        if next_word_tr:
                            next_clean = next_word_tr.lstrip(" -")
                            if next_clean:
                                first_char = next_clean[0]
                                if first_char in HAMZAH_CHARS or first_char in {'a', 'i', 'u', 'ā', 'ī', 'ū'}:
                                    m_type, beats = 'munfasil', 4
                                else:
                                    m_type, beats = 'tabee', 2
                            else:
                                m_type, beats = 'tabee', 2
                        else:
                            m_type, beats = 'tabee', 2
                    else:
                        if not next_word_tr and len(clean_rest) <= 2:
                            m_type, beats = 'aaridh', 4
                        else:
                            m_type, beats = 'tabee', 2
                
                if beats > max_beats:
                    max_beats = beats
                    best_type = m_type
                    
        return best_type, max_beats

    @staticmethod
    def classify_ghunnah_type(word_tr: str, next_word_tr: str = "") -> tuple[str, int]:
        word_tr = word_tr.lower().strip()
        next_word_tr = next_word_tr.lower().strip()
        if 'nn' in word_tr or 'mm' in word_tr:
            return 'mushaddad', 2
        word_clean = word_tr.rstrip(" -'")
        
        # Check for Noon Saakin in the middle of the word:
        for idx in range(len(word_clean) - 1):
            if word_clean[idx] == 'n' and word_clean[idx+1] not in {'a', 'i', 'u', 'ā', 'ī', 'ū', 'n', 'y', 'w', 'm', 'l', 'r', 'b'}:
                is_throat = False
                rest_from_n = word_clean[idx+1:]
                for h in IZHAAR_LETTERS:
                    if rest_from_n.startswith(h):
                        is_throat = True
                        break
                if not is_throat:
                    return 'ikhfaa_middle', 2
            if word_clean[idx] == 'n' and word_clean[idx+1] == 'b':
                return 'iqlaab_middle', 2
                
        ends_with_n = word_clean.endswith('n')
        ends_with_m = word_clean.endswith('m')
        if ends_with_n or ends_with_m:
            if not next_word_tr:
                return None, 0
            next_clean = next_word_tr.lstrip(" -")
            if not next_clean:
                return None, 0
            next_first = next_clean[0]
            if ends_with_n:
                if next_first == 'b':
                    return 'iqlaab', 2
                if next_first in GHUNNAH_IDGHAM_LETTERS:
                    return 'idgham_ghunnah', 2
                if next_first in {'l', 'r'}:
                    return 'idgham_no_ghunnah', 0
                is_izhaar = False
                for h in IZHAAR_LETTERS:
                    if next_clean.startswith(h):
                        is_izhaar = True
                        break
                if is_izhaar:
                    return 'izhaar', 0
                return 'ikhfaa', 2
            if ends_with_m:
                if next_first == 'b':
                    return 'ikhfaa_shafawi', 2
                if next_first == 'm':
                    return 'idgham_meem', 2
                return 'izhaar_shafawi', 0
        return None, 0

    @staticmethod
    def local_align_chars(actual: str, reference: str, match_score=2, mismatch_penalty=-1, gap_penalty=-0.5):
        N = len(actual)
        M = len(reference)
        if N == 0 or M == 0:
            return 0, 0, 0.0

        dp = np.zeros((N + 1, M + 1))
        for i in range(1, N + 1):
            a_char = actual[i-1]
            for j in range(1, M + 1):
                r_char = reference[j-1]
                score_match = match_score if a_char == r_char else mismatch_penalty
                
                s_match = dp[i-1][j-1] + score_match
                s_ins = dp[i-1][j] + gap_penalty
                s_del = dp[i][j-1] + gap_penalty

                val = max(0, s_match, s_ins, s_del)
                dp[i][j] = val

        best_val = 0
        best_cell = (0, 0)
        for i in range(1, N + 1):
            for j in range(1, M + 1):
                if dp[i][j] > best_val:
                    best_val = dp[i][j]
                    best_cell = (i, j)

        if best_val == 0:
            return 0, 0, 0.0

        i, j = best_cell
        end_act = i - 1
        
        while i > 0 and j > 0 and dp[i][j] > 0:
            a_char = actual[i-1]
            r_char = reference[j-1]
            score_match = match_score if a_char == r_char else mismatch_penalty
            
            s_match = dp[i-1][j-1] + score_match
            s_ins = dp[i-1][j] + gap_penalty
            s_del = dp[i][j-1] + gap_penalty

            max_val = max(s_match, s_ins, s_del)
            if max_val == s_match:
                i -= 1
                j -= 1
            elif max_val == s_ins:
                i -= 1
            else:
                j -= 1

        start_act = i
        normalized_score = best_val / (match_score * min(N, M))
        return start_act, end_act, normalized_score

    @staticmethod
    def score_temporal_madd(char_durations: list[dict], reference_words: list[dict]) -> list[dict]:
        """
        Calculates temporal scores for Madd (lengthening) rules.
        Returns a list of word-level temporal feedback.
        """
        temporal_feedback = []
        
        # 1. Calculate the 'Base Harakah' (Mean duration of single short vowels)
        short_vowels = [d['frames'] for d in char_durations if d['char'] in ['a', 'i', 'u'] and d['frames'] < 8]
        base_harakah = np.mean(short_vowels) if short_vowels else 5.0
        base_harakah = max(1.5, base_harakah)

        act_str = "".join([d['char'] for d in char_durations]).lower()

        # 2. Check each word for Madd using local alignment
        for i, ref in enumerate(reference_words):
            word_tr = ref['word_tr'].lower()
            next_word_tr = reference_words[i+1]['word_tr'].lower() if i+1 < len(reference_words) else ""
            
            madd_type, required_beats = TajweedScorer.classify_madd_type(word_tr, next_word_tr)
            
            word_feedback = {"error": False, "rule": None, "guidance": None}
            
            if required_beats > 0:
                # Find local alignment of the reference word against the transcribed string
                # Best parameters from grid search: gp = -0.5, score_th = 0.1, tol = 2.4, cap = 999 (uncapped)
                start_act, end_act, score = TajweedScorer.local_align_chars(act_str, word_tr, gap_penalty=-0.5)
                aligned = (score >= 0.1) and (start_act <= end_act)
                
                if aligned:
                    # Find actual maximum duration of any long vowel in the aligned region
                    aligned_vowels = [char_durations[k]["frames"] for k in range(start_act, end_act + 1) if k < len(char_durations) and char_durations[k]["char"] in LONG_VOWELS]
                    actual_frames = max(aligned_vowels) if aligned_vowels else 0
                    actual_beats = actual_frames / base_harakah
                    
                    if actual_beats < (required_beats * 2.4):
                        rule_name = {
                            'tabee': "Madd Tabii (Short Lengthening)",
                            'munfasil': "Madd Ja'ez Munfasil (Short Lengthening)",
                            'muttasil': "Madd Wajib Muttasil (Short Lengthening)",
                            'laazim': "Madd Lazim (Short Lengthening)",
                            'aaridh': "Madd Aaridh Lissukoon (Short Lengthening)"
                        }.get(madd_type, "Madd Elongation Error")
                        
                        word_feedback = {
                            "error": True,
                            "rule": rule_name,
                            "guidance": f"The lengthening was too short ({actual_frames} frames). Ensure it is at least {required_beats} beats."
                        }
                else:
                    # unaligned_is_error is True for best Madd configuration
                    rule_name = {
                        'tabee': "Madd Tabii (Short Lengthening)",
                        'munfasil': "Madd Ja'ez Munfasil (Short Lengthening)",
                        'muttasil': "Madd Wajib Muttasil (Short Lengthening)",
                        'laazim': "Madd Lazim (Short Lengthening)",
                        'aaridh': "Madd Aaridh Lissukoon (Short Lengthening)"
                    }.get(madd_type, "Madd Elongation Error")
                    
                    word_feedback = {
                        "error": True,
                        "rule": rule_name,
                        "guidance": "Madd was not detected in recitation."
                    }
            
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
        base_harakah = max(1.5, base_harakah)

        # 2. Align characters (optimized gap penalty: -1.2)
        act_str = "".join([d['char'] for d in char_durations]).lower()
        exp_str = "".join([w['word_tr'] for w in reference_words]).lower()
        alignment = TajweedScorer._align_chars(act_str, exp_str, gap_penalty=-1.2)

        # 3. Reference spans
        ref_spans = []
        curr_idx = 0
        for ref in reference_words:
            w_len = len(ref['word_tr'])
            ref_spans.append((curr_idx, curr_idx + w_len))
            curr_idx += w_len

        # 4. Check each word for Ghunnah
        for i, ref in enumerate(reference_words):
            word_tr = ref['word_tr'].lower()
            next_word_tr = reference_words[i+1]['word_tr'].lower() if i+1 < len(reference_words) else ""
            
            ghunnah_type, required_beats = TajweedScorer.classify_ghunnah_type(word_tr, next_word_tr)
            
            word_feedback = {"error": False, "rule": None, "guidance": None}
            
            if required_beats > 0:
                # Find transcribed characters aligned to this reference word
                start, end = ref_spans[i]
                aligned_chars = []
                for act_idx, ref_idx in enumerate(alignment):
                    if start <= ref_idx < end:
                        aligned_chars.append(char_durations[act_idx])
                
                # Check for alignment (unaligned_is_error = False)
                if aligned_chars:
                    # Find actual maximum duration of any character in aligned region
                    actual_frames = max(d['frames'] for d in aligned_chars)
                    actual_beats = actual_frames / base_harakah
                    
                    # Optimized tolerance for Ghunnah: 1.75
                    tol = 1.75
                    if actual_beats < (required_beats * tol):
                        rule_name = {
                            'mushaddad': "Noon/Meem Mushaddad (Ghunnah)",
                            'ikhfaa': "Ikhfaa Haqiqi (Ghunnah)",
                            'ikhfaa_middle': "Ikhfaa Haqiqi (Ghunnah)",
                            'iqlaab': "Iqlaab (Ghunnah)",
                            'iqlaab_middle': "Iqlaab (Ghunnah)",
                            'idgham_ghunnah': "Idgham with Ghunnah",
                            'ikhfaa_shafawi': "Ikhfaa Shafawi (Ghunnah)",
                            'idgham_meem': "Idgham Mutamathelayn (Ghunnah)"
                        }.get(ghunnah_type, "Ghunnah Nasality Error")
                        
                        word_feedback = {
                            "error": True,
                            "rule": rule_name,
                            "guidance": f"The Ghunnah was too short ({actual_frames} frames). Hold for {required_beats} counts."
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
    def _align_words_local(actual_words: list[str], ref_words: list[dict]) -> list[tuple[int, int]]:
        """
        Aligns actual transcribed words to reference words using semi-global DP.
        Returns a list of tuples (actual_index, reference_index).
        Unmapped actual words will map to -1.
        """
        N = len(actual_words)
        M = len(ref_words)
        if N == 0 or M == 0:
            return []

        # DP table and backtrack choices
        dp = np.zeros((N + 1, M + 1))
        # Choices: 0=Match, 1=Insert (actual extra), 2=Delete (reference skipped)
        backtrack = np.zeros((N + 1, M + 1), dtype=int)

        # Gap penalties
        gap_penalty = -0.4

        # Initialize base cases
        for i in range(1, N + 1):
            dp[i][0] = i * gap_penalty
            backtrack[i][0] = 1 # Insertion

        # Free gaps at start of reference: dp[0][j] = 0 (already 0)

        for i in range(1, N + 1):
            act_word = actual_words[i-1]
            for j in range(1, M + 1):
                ref_word = ref_words[j-1]['word_tr']
                match_val = TajweedScorer.weighted_similarity(act_word, ref_word)
                
                # We encourage matching: similarity >= 0.5 is positive, < 0.5 is negative
                score_match = match_val if match_val >= 0.5 else (match_val - 0.5)
                
                s_match = dp[i-1][j-1] + score_match
                s_ins = dp[i-1][j] + gap_penalty
                s_del = dp[i][j-1] + gap_penalty

                best = max(s_match, s_ins, s_del)
                dp[i][j] = best

                if best == s_match:
                    backtrack[i][j] = 0
                elif best == s_ins:
                    backtrack[i][j] = 1
                else:
                    backtrack[i][j] = 2

        # Find best end cell in row N (since we want to consume all actual words)
        best_j = M
        best_val = dp[N][M]
        for j in range(1, M + 1):
            if dp[N][j] > best_val:
                best_val = dp[N][j]
                best_j = j

        # Backtrack to find alignment
        i = N
        j = best_j
        alignment = []

        while i > 0 or (j > 0 and dp[i][j] != 0):
            if i == 0:
                j -= 1
            elif j == 0 or backtrack[i][j] == 1:
                alignment.append((i-1, -1))
                i -= 1
            elif backtrack[i][j] == 0:
                alignment.append((i-1, j-1))
                i -= 1
                j -= 1
            else:
                alignment.append((-1, j-1))
                j -= 1

        alignment.reverse()
        return alignment

    @staticmethod
    def score_recitation(
        actual_phonetics: list[str],
        reference_words: list[dict],
        temporal_feedback: list[dict] = None
    ) -> dict:
        word_results = []
        total_score = 0.0
        error_summary = {"correct": 0, "minor_error": 0, "major_error": 0}

        # 1. Align actual phonetics to reference words
        alignment = TajweedScorer._align_words_local(actual_phonetics, reference_words)
        
        # Define the recited span boundaries in reference words
        aligned_ref_indices = [ref_idx for _, ref_idx in alignment if ref_idx != -1]
        if aligned_ref_indices:
            ref_start = min(aligned_ref_indices)
            ref_end = max(aligned_ref_indices)
        else:
            ref_start = 999999
            ref_end = -1

        # Fallback to linear mapping if alignment is completely empty (e.g. no inputs)
        if not alignment:
            alignment = [(i, i) for i in range(max(len(actual_phonetics), len(reference_words)))]

        # Group alignment by reference word index
        ref_to_alignment = {}
        extra_words = []
        
        for act_idx, ref_idx in alignment:
            if ref_idx != -1:
                ref_to_alignment[ref_idx] = act_idx
            else:
                extra_words.append(act_idx)

        # Loop through reference words and score each
        for i, ref in enumerate(reference_words):
            expected = ref["word_tr"]
            act_idx = ref_to_alignment.get(i, -1)
            maulana_guidance = None
            
            if act_idx != -1:
                # Match / Substitution
                actual = actual_phonetics[act_idx]
                similarity = TajweedScorer.weighted_similarity(actual, expected)
                
                if similarity >= CORRECT_THRESHOLD:
                    status = "correct"
                    rule = None
                elif similarity >= 0.70:
                    status = "minor_error"
                    rule = "Lahn Khafi (Phonetic Shift)"
                else:
                    status = "major_error"
                    rule = "Lahn Jali (Major Mispronunciation)"
            else:
                # Deletion (Reference word skipped)
                actual = ""
                # Check if it is inside the recited span
                if ref_start <= i <= ref_end:
                    similarity = 0.0
                    status = "major_error"
                    rule = "Missing Word"
                    maulana_guidance = "Word was omitted from recitation."
                else:
                    # Outside the recited span (ignored)
                    similarity = 1.0
                    status = "correct"
                    rule = None
                    maulana_guidance = None

            # Integrate Temporal/Spectral Feedback if provided
            if actual and temporal_feedback:
                if isinstance(temporal_feedback, dict):
                    tf = temporal_feedback.get(i)
                elif isinstance(temporal_feedback, list) and i < len(temporal_feedback):
                    tf = temporal_feedback[i]
                else:
                    tf = None

                if tf and tf.get("error"):
                    status = "major_error"
                    rule = tf["rule"]
                    maulana_guidance = tf["guidance"]
                    similarity = min(similarity, 0.65)

            # Classify error details for pedagogy
            error_details = None
            if status != "correct":
                error_details = TajweedScorer.classify_mistake(actual, expected, rule)
                if not maulana_guidance and error_details:
                    err_type = error_details.get("error_type")
                    if err_type == "vowel_change":
                        maulana_guidance = f"Harakah vowel shift: you pronounced '{actual}' instead of '{expected}'. Ensure you pronounce the short vowels (Fathah/Dammah/Kasrah) precisely without sliding or altering the sound."
                    elif err_type == "throat_halqi":
                        maulana_guidance = f"Throat letter (Halqi) articulation error: check '{actual}' vs '{expected}'. Throat letters (Hamzah, Haa, 'Ayn, Haa, Ghayn, Khaa) must be articulated from their correct section of the throat (deep throat, middle throat, or upper throat)."
                    elif err_type == "lip_shafawi":
                        maulana_guidance = f"Lip letter (Shafawi) articulation error: check '{actual}' vs '{expected}'. Lip letters (Baa, Meem, Waaw, Faa) require full lip closure or rounding."
                    elif err_type == "teeth_dars":
                        maulana_guidance = f"Teeth/dental letter (Dars) error: check '{actual}' vs '{expected}'. The letters 'th' (ث) and 'dh' (ذ) require placing the tongue tip against the edge of the upper teeth."
                    elif err_type == "tongue_lisani":
                        maulana_guidance = f"Tongue letter (Lisani) error: check '{actual}' vs '{expected}'. Ensure your tongue tip or sides make contact with the correct areas of the palate or teeth gums."
                    else:
                        maulana_guidance = f"Pronunciation shift: pronounced '{actual}' instead of '{expected}'. Focus on the letters' articulation points (Makharij) and attributes (Sifaat)."

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

        # Append extra words (insertions) to the end of results
        for act_idx in extra_words:
            word_results.append({
                "word_index": len(reference_words),
                "status": "extra_word",
                "actual_phonetic": actual_phonetics[act_idx]
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
