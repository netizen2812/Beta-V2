from google.cloud import texttospeech

def list_voices():
    client = texttospeech.TextToSpeechClient()
    voices = client.list_voices()
    
    print(f"{'Name':<40} {'Language Codes':<20} {'SSML Gender':<15}")
    for voice in voices.voices:
        if any(lang in voice.language_codes for lang in ['ar-XA', 'ur-PK']):
            print(f"{voice.name:<40} {', '.join(voice.language_codes):<20} {texttospeech.SsmlVoiceGender(voice.ssml_gender).name:<15}")

if __name__ == "__main__":
    list_voices()
