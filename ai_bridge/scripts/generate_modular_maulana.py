import os
import logging
from pathlib import Path
from google.cloud import texttospeech

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("ModularMaulana")

# Config
PROJECT_ID = "project-1aebaa37-477b-49e5-ae0"
OUTPUT_DIR = Path("./modular_samples")

# Modular Data Matrix
MODULAR_DATA = [
    {
        "lang": "ar",
        "voice": "ar-XA-Chirp3-HD-Achird",
        "segments": [
            {
                "name": "recitation",
                "ssml": '<speak><prosody rate="0.85"><lang xml:lang="ar-XA">قُلْ هُوَ ٱللَّهُ أَحَدٌ</lang></prosody></speak>'
            }
        ]
    },
    {
        "lang": "en",
        "voice": "en-GB-Studio-B",
        "segments": [
            {
                "name": "literal",
                "ssml": '<speak><prosody rate="0.95"><s>Say, <break time="150ms"/> He is Allah, <break time="100ms"/> the One.</s></prosody></speak>'
            },
            {
                "name": "insight",
                "ssml": '<speak><prosody rate="0.95"><s>The Qāf must emerge from the deep throat. <break time="400ms"/> It is a uvular stop, <break time="200ms"/> not a k sound.</s></prosody></speak>'
            }
        ]
    },
    {
        "lang": "ur",
        "voice": "ur-IN-Chirp3-HD-Achird",
        "segments": [
            {
                "name": "literal",
                "ssml": '<speak><prosody rate="0.90"><s>کہہ دیجئے <break time="200ms"/> کہ وہ اللہ ایک ہے۔</s></prosody></speak>'
            },
            {
                "name": "insight",
                "ssml": '<speak><prosody rate="0.90"><s>\'قل\' میں \'ق\' <break time="150ms"/> گہرے حلق سے نکالیں۔ <break time="500ms"/> \'هو\' میں \'ہ\' بھی <break time="200ms"/> واضح سانس کے ساتھ ادا کریں۔</s></prosody></speak>'
            }
        ]
    }
]

def synthesize_ssml(client, ssml, voice_name, lang_code, output_path):
    synthesis_input = texttospeech.SynthesisInput(ssml=ssml)
    voice = texttospeech.VoiceSelectionParams(
        language_code=lang_code,
        name=voice_name
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        effects_profile_id=["headphone-class-device"]
    )

    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as out:
        out.write(response.audio_content)
    log.info(f"Generated: {output_path}")

def main():
    client = texttospeech.TextToSpeechClient()
    
    log.info(f"Starting Modular Maulana synthesis for Project: {PROJECT_ID}")
    
    for item in MODULAR_DATA:
        lang = item["lang"]
        voice = item["voice"]
        lang_code = "ar-XA" if lang == "ar" else "ur-IN" if lang == "ur" else "en-GB"
        
        for seg in item["segments"]:
            file_name = f"{seg['name']}.mp3"
            output_path = OUTPUT_DIR / lang / file_name
            synthesize_ssml(client, seg["ssml"], voice, lang_code, output_path)

if __name__ == "__main__":
    main()
