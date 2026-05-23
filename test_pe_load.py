import sys
import os
sys.path.append(os.getcwd())
from ai_bridge.models.phonetic_engine import PhoneticEngine

try:
    print("Loading Phonetic Engine...")
    pe = PhoneticEngine()
    pe.load()
    print("Success!")
except Exception as e:
    import traceback
    traceback.print_exc()
