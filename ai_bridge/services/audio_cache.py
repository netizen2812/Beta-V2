import sqlite3
import hashlib
import logging
from pathlib import Path

logger = logging.getLogger("AudioCache")

CACHE_DB_PATH = Path("ai_bridge/data/audio_cache.db")
CACHE_AUDIO_DIR = Path("ai_bridge/data/cache_wavs")

class AudioCache:
    def __init__(self):
        CACHE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        CACHE_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(CACHE_DB_PATH, check_same_thread=False)

        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS audio_cache (
                hash_key TEXT PRIMARY KEY,
                rule TEXT,
                word TEXT,
                language TEXT,
                audio_path TEXT,
                text_content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()
        self.evict_old_cache()
        
    def evict_old_cache(self, limit: int = 1000):
        """Keep only the most recent `limit` items."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT hash_key, audio_path FROM audio_cache 
                ORDER BY created_at DESC LIMIT -1 OFFSET ?
            ''', (limit,))
            rows = cursor.fetchall()
            for row in rows:
                hash_key, audio_path = row
                try:
                    Path(audio_path).unlink(missing_ok=True)
                except:
                    pass
                self.conn.execute('DELETE FROM audio_cache WHERE hash_key = ?', (hash_key,))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Eviction error: {e}")
            
    def _generate_hash(self, rule: str, word: str, language: str, madhab: str = "shafi", guidance: str = "") -> str:
        key_str = f"{rule.lower()}_{word.lower()}_{language.lower()}_{madhab.lower()}"
        if guidance:
            key_str += f"_{guidance.strip().lower()}"
        return hashlib.md5(key_str.encode('utf-8')).hexdigest()

    def get_cached_insight(self, rule: str, word: str, language: str, madhab: str = "shafi", guidance: str = ""):
        """Returns (audio_path, text_content) if exists, else None."""
        hash_key = self._generate_hash(rule, word, language, madhab, guidance)
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT audio_path, text_content FROM audio_cache WHERE hash_key = ?', (hash_key,))
            row = cursor.fetchone()
            if row and Path(row[0]).exists():
                return {"audio_path": row[0], "text": row[1]}
        except Exception as e:
            logger.error(f"Cache read error: {e}")
        return None

    def get_cached_by_text(self, text_content: str, language: str, madhab: str = "shafi"):
        """Returns cache entry if text_content matches, else None."""
        try:
            norm_text = text_content.strip().lower()
            cursor = self.conn.cursor()
            # Select by exact normalized text match
            cursor.execute('SELECT audio_path, text_content FROM audio_cache WHERE LOWER(TRIM(text_content)) = ? AND language = ?', (norm_text, language.lower()))
            row = cursor.fetchone()
            if row and Path(row[0]).exists():
                return {"audio_path": row[0], "text": row[1]}
        except Exception as e:
            logger.error(f"Cache read by text error: {e}")
        return None

    def save_to_cache(self, rule: str, word: str, language: str, text_content: str, source_audio_path: Path, madhab: str = "shafi", guidance: str = "") -> Path:
        """Saves generated audio to cache and returns the new permanent path."""
        hash_key = self._generate_hash(rule, word, language, madhab, guidance)
        new_audio_path = CACHE_AUDIO_DIR / f"{hash_key}.mp3"
        
        try:
            # Move/Copy the temp audio to the permanent cache dir
            new_audio_path.write_bytes(source_audio_path.read_bytes())
            
            self.conn.execute(
                'INSERT OR REPLACE INTO audio_cache (hash_key, rule, word, language, audio_path, text_content) VALUES (?, ?, ?, ?, ?, ?)',
                (hash_key, rule, word, language, str(new_audio_path), text_content)
            )
            self.conn.commit()
            logger.info(f"Insight cached successfully: {hash_key}")
            return new_audio_path
        except Exception as e:
            logger.error(f"Cache write error: {e}")
            return source_audio_path

audio_cache_manager = AudioCache()
