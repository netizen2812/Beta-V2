import urllib.request
import json
import logging
from typing import List, Dict, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("AudioOrchestrator")

# Edition Identifiers based on user preference
EDITIONS = {
    "ar": "ar.alafasy",  # Mishary Alafasy
    "en": "en.walk",     # Ibrahim Walk
    "ur": "ur.khan"      # Shamshad Ali Khan
}

def get_alquran_audio_url(surah: int, verse: int, language: str) -> Optional[str]:
    """
    Fetches the pre-recorded audio URL from Al Quran Cloud for a specific Ayah.
    """
    edition = EDITIONS.get(language)
    if not edition:
        log.error(f"Unsupported language requested: {language}")
        return None

    url = f"http://api.alquran.cloud/v1/ayah/{surah}:{verse}/{edition}"
    
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read())
            if data['code'] == 200:
                audio_url = data['data']['audio']
                return audio_url
            else:
                log.error(f"API Error: {data.get('status')}")
                return None
    except Exception as e:
        log.error(f"Failed to fetch {url}: {e}")
        return None

def build_playlist(surah: int, verse: int, target_language: str, live_insight_url: Optional[str] = None) -> List[Dict[str, str]]:
    """
    Constructs an audio playlist (array of URLs) for the frontend to play sequentially.
    Order:
      1. Arabic Recitation (Static CDN)
      2. Translation (Static CDN)
      3. Live AI Insight (Live TTS URL) -> Optional
    """
    playlist = []
    
    # 1. Arabic
    ar_url = get_alquran_audio_url(surah, verse, "ar")
    if ar_url:
        playlist.append({"type": "arabic", "url": ar_url})
        
    # 2. Translation
    if target_language in ["en", "ur"]:
        trans_url = get_alquran_audio_url(surah, verse, target_language)
        if trans_url:
            playlist.append({"type": "translation", "url": trans_url})
            
    # 3. Live AI Insight / Mortar
    if live_insight_url:
        playlist.append({"type": "insight", "url": live_insight_url})
        
    return playlist

if __name__ == "__main__":
    # Test script
    log.info("Testing Orchestrator with Surah 112, Verse 1, English Target, with mock insight.")
    test_playlist = build_playlist(
        surah=112, 
        verse=1, 
        target_language="en", 
        live_insight_url="https://our-api.com/static/temp_insight_123.mp3"
    )
    
    for item in test_playlist:
        log.info(f"[{item['type'].upper()}] -> {item['url']}")
