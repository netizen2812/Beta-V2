import json
import os
from pathlib import Path

OUT_FILE = Path("ai_bridge/data/wisdom_templates.json")

BOOTSTRAP_DATA = {
    "en.reception.greetings.time_based.morning": [
        "Assalamu Alaikum. May your morning be filled with the light of the Quran.",
        "A blessed morning to you. Let us start our day with a heart full of reflection.",
        "Good morning. I hope you find peace in today's session.",
        "Assalamu Alaikum. May the barakah of this morning stay with you throughout the day.",
        "Welcome to your morning session. May Allah open your mind to His wisdom."
    ],
    "en.reception.greetings.time_based.evening": [
        "Assalamu Alaikum. Let us end this day in reflection and peace.",
        "Good evening. It is time to quiet the soul and listen to the words of Allah.",
        "Assalamu Alaikum. May your night be as peaceful as the verses we read today.",
        "Welcome back this evening. Let the Quran be your rest after a long day.",
        "Evening is a time for deep thought. Let us dive into the wisdom together."
    ],
    "en.pedagogy.correction.makharij.tongue_lisani.qaf_error": [
        "One moment, please. Listen closely. The 'Qaf' should resonate from the deep back of the throat.",
        "Gently now. Focus on the 'Qaf'. It needs more depth, like a heavy echo.",
        "Wait, let us try that again. Feel the vibration at the very root of your tongue for the 'Qaf'.",
        "Observe carefully. The 'Qaf' is a heavy letter. Do not let it sound like a 'Kaf'.",
        "Mashallah, good effort. But let's refine that 'Qaf'. It needs to be deeper and firmer."
    ],
    "en.pedagogy.praise.standard.mashallah": [
        "Mashallah! Your recitation has a beautiful sincerity to it.",
        "Mashallah. I can hear the focus in your voice today. Very well done.",
        "Mashallah! May Allah continue to guide your tongue to such clarity.",
        "Beautifully read. Mashallah. You are making great progress.",
        "Mashallah. That was a very heart-centered recitation."
    ],
    "en.bridge.emotional.stress.anxiety": [
        "I sense a heaviness in your heart today. Let these verses be a healing for you.",
        "My dear student, if you are feeling anxious, know that Allah is the turner of hearts. Listen to this.",
        "Do not let the worries of the world distract you. Focus on the rhythm of the Ayah.",
        "Breathe deeply. Allah mentions peace for a reason. Let us reflect on that now.",
        "I hear the stress in your tone. Remember, with hardship comes ease. Let's find that ease together."
    ],
    "en.tarbiyah.milestones.streaks.7_day_consistency": [
        "Mashallah! You have been consistent for seven days. Your heart is finding its rhythm.",
        "Seven days of devotion. I am very proud of your progress. Stay firm on this path.",
        "One full week! Your commitment to the Quran is truly inspiring. Keep going.",
        "Seven days. This is how a habit of the heart is built. May Allah reward you.",
        "Mashallah, a seven-day streak. You are becoming a true student of the Book."
    ]
}

def bootstrap():
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing or start new
    if OUT_FILE.exists():
        with open(OUT_FILE, "r", encoding="utf-8") as f:
            library = json.load(f)
    else:
        library = {}

    # Update with bootstrap data
    library.update(BOOTSTRAP_DATA)

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(library, f, indent=2)
    
    print(f"DONE: Bootstrap complete. {len(BOOTSTRAP_DATA)} core nodes pre-populated in {OUT_FILE}")

if __name__ == "__main__":
    bootstrap()
