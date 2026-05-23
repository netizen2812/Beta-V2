import os
import httpx
from dotenv import load_dotenv

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

print(f"Key: {OPENROUTER_API_KEY[:10]}...")

url = "https://openrouter.ai/api/v1/models"
headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
}

try:
    with httpx.Client() as client:
        resp = client.get(url, headers=headers)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            models = resp.json().get('data', [])
            print(f"Found {len(models)} models.")
            for m in models[:5]:
                print(f" - {m['id']}")
        else:
            print(f"Resp: {resp.text}")
except Exception as e:
    print(f"Error: {e}")
