"""
services/personalization.py
Redis-backed personalization engine for IMAM AI home dashboard.
Fetches session logs, Levenshtein score, and generates ranked recommendations.
"""
import json
import logging
from typing import Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# ── Redis connection (lazy singleton) ──────────────────────────────────────────
_redis_client = None

def _get_redis():
    global _redis_client
    if _redis_client is None:
        try:
            import redis
            import os
            _redis_client = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", 6379)),
                db=0,
                decode_responses=True,
            )
            _redis_client.ping()
        except Exception as e:
            logger.warning(f"Redis unavailable — personalization fallback active: {e}")
            _redis_client = None
    return _redis_client


# ── Session Log Schema ─────────────────────────────────────────────────────────
# Key:   user:session:{user_id}
# Value: JSON list of {ayah_id, score, grade, timestamp, error_types}

def fetch_user_sessions(user_id: str, limit: int = 10) -> list[dict]:
    """Pull recent session logs from Redis."""
    r = _get_redis()
    if not r:
        return _fallback_sessions()
    try:
        raw = r.lrange(f"user:session:{user_id}", 0, limit - 1)
        return [json.loads(s) for s in raw]
    except Exception as e:
        logger.error(f"Session fetch error for {user_id}: {e}")
        return _fallback_sessions()


def _fallback_sessions() -> list[dict]:
    """Hardcoded fallback when Redis is offline."""
    return [
        {"ayah_id": "112:1", "score": 94, "grade": "Mumtaz",  "timestamp": datetime.utcnow().isoformat(), "error_types": []},
        {"ayah_id": "113:1", "score": 87, "grade": "Jayyid",  "timestamp": (datetime.utcnow() - timedelta(days=1)).isoformat(), "error_types": ["timing_error_madd"]},
        {"ayah_id": "1:1",   "score": 91, "grade": "Mumtaz",  "timestamp": (datetime.utcnow() - timedelta(days=2)).isoformat(), "error_types": []},
    ]


def build_home_recommendations(user_id: str) -> dict[str, Any]:
    """
    Derive personalized home dashboard data from Redis session logs.
    Returns: {
        grade, tajweed_score, rag_clarity,
        last_surah, last_ayah,
        recommended_next, weak_areas
    }
    """
    sessions = fetch_user_sessions(user_id)

    if not sessions:
        return _default_home()

    latest    = sessions[0]
    avg_score = round(sum(s["score"] for s in sessions) / len(sessions))

    # Aggregate error types to surface weak areas
    error_counts: dict[str, int] = {}
    for s in sessions:
        for err in s.get("error_types", []):
            error_counts[err] = error_counts.get(err, 0) + 1

    weak_areas = sorted(error_counts, key=lambda k: -error_counts[k])[:3]

    # Derive RAG Clarity: sessions with grade Mumtaz / total
    mumtaz_count = sum(1 for s in sessions if s.get("grade") == "Mumtaz")
    rag_clarity  = round((mumtaz_count / len(sessions)) * 100)

    # Suggest next ayah: continue from last or promote to harder chapter
    parts       = latest["ayah_id"].split(":")
    surah_no    = int(parts[0])
    verse_no    = int(parts[1]) + 1
    recommended = f"{surah_no}:{verse_no}"

    return {
        "grade":            latest.get("grade", "Jayyid"),
        "tajweed_score":    latest.get("score", avg_score),
        "rag_clarity":      rag_clarity,
        "last_ayah":        latest["ayah_id"],
        "last_surah":       _surah_name(surah_no),
        "recommended_next": recommended,
        "weak_areas":       weak_areas,
        "avg_score":        avg_score,
    }


def push_session_log(user_id: str, ayah_id: str, score: float, grade: str, error_types: list[str]):
    """Push a completed session result into Redis."""
    r = _get_redis()
    if not r:
        logger.info(f"[FALLBACK] Session log not stored: {user_id} {ayah_id} {score}")
        return
    payload = json.dumps({
        "ayah_id":     ayah_id,
        "score":       score,
        "grade":       grade,
        "timestamp":   datetime.utcnow().isoformat(),
        "error_types": error_types,
    })
    key = f"user:session:{user_id}"
    r.lpush(key, payload)
    r.ltrim(key, 0, 99)   # Keep last 100 sessions
    r.expire(key, 60 * 60 * 24 * 90)  # 90-day TTL


def _default_home() -> dict[str, Any]:
    return {
        "grade": "—", "tajweed_score": 0, "rag_clarity": 0,
        "last_ayah": "1:1", "last_surah": "Al-Fatihah",
        "recommended_next": "1:2", "weak_areas": [], "avg_score": 0,
    }


def _surah_name(n: int) -> str:
    names = {1:"Al-Fatihah",2:"Al-Baqarah",3:"Ali Imran",112:"Al-Ikhlas",113:"Al-Falaq",114:"An-Nas"}
    return names.get(n, f"Surah {n}")
