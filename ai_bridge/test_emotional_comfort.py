import os
import sys
import asyncio

# Ensure root ai_bridge directory is in path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from services.smart_rag import smart_rag
from services.maulana_voice import get_maulana_advice

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

async def main():
    print("Loading smart_rag...")
    try:
        smart_rag.load()
        print(f"smart_rag loaded. is_loaded={smart_rag.is_loaded}")
        if not smart_rag.is_loaded:
            print("Warning: smart_rag loaded but is_loaded is False!")
    except Exception as e:
        print(f"Error loading smart_rag: {e}")
        import traceback
        traceback.print_exc()
        return


    scenarios = [
        {
            "name": "Scenario 1: English Exam Stress (Shafi)",
            "error_details": {
                "rule": "Academic Exam Stress",
                "word": "Exams",
                "guidance": "I am feeling so stressed about my exams tomorrow, I cannot study."
            },
            "language": "english",
            "madhab": "shafi"
        },
        {
            "name": "Scenario 2: Urdu Exam Stress (Hanafi)",
            "error_details": {
                "rule": "Urdu Exam Stress",
                "word": "Exams",
                "guidance": "کل میرے امتحانات ہیں اور مجھے بہت گھبراہٹ ہو رہی ہے۔ پڑھا نہیں جا رہا۔"
            },
            "language": "urdu",
            "madhab": "hanafi"
        }
    ]

    for sc in scenarios:
        print(f"\n=== Running {sc['name']} ===")
        res = await get_maulana_advice(
            error_details=sc["error_details"],
            language=sc["language"],
            madhab=sc["madhab"]
        )
        print("Blended Advice Text:")
        print(res["text"])
        print("-" * 60)

if __name__ == "__main__":
    asyncio.run(main())
