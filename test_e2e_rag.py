import urllib.request
import json
import sys
import time

def test():
    url = "http://localhost:5001/api/quran/ask"
    payload = {
        "user_question": "I am feeling so stressed about my exams tomorrow, I cannot study.",
        "madhab": "shafi",
        "language_code": "en",
        "ayah_id": "1:1"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print("🚀 Sending emotional RAG request to local Express backend...")
    req = urllib.request.Request(
        url, 
        data=json.dumps(payload).encode('utf-8'), 
        headers=headers,
        method="POST"
    )
    
    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            print("✅ Response status:", res_data.get("status"))
            print("🔹 Stitched 80/20 Text Answer:")
            print("-" * 60)
            print(res_data.get("data", {}).get("answer"))
            print("-" * 60)
            print(f"⏱️ Time taken: {time.time() - start:.2f} seconds")
    except Exception as e:
        print("❌ Request failed:", str(e))
        sys.exit(1)

if __name__ == "__main__":
    test()
