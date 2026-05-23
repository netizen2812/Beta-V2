import sys
import os
sys.path.append(os.getcwd())
print("Importing Scorer...")
from ai_bridge.services.tajweed_scorer import TajweedScorer
print("Importing DB...")
from ai_bridge.services.phonetic_db import PhoneticDB
print("Importing PE...")
from ai_bridge.models.phonetic_engine import PhoneticEngine

try:
    print("Loading Phonetic Engine...")
    pe = PhoneticEngine()
    pe.load()
    print("Success!")
except Exception as e:
    import traceback
    traceback.print_exc()
