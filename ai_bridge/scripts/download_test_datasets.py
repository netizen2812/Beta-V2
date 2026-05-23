import requests
import json
import os

# Create data/test_datasets directory
os.makedirs("ai_bridge/data/test_datasets/qdat", exist_ok=True)
os.makedirs("ai_bridge/data/test_datasets/ikhlas", exist_ok=True)

def download_file(url, path):
    if os.path.exists(path):
        return True
    try:
        r = requests.get(url, timeout=30)
        if r.status_code == 200:
            with open(path, 'wb') as f:
                f.write(r.content)
            return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
    return False

# Sample data from HF (from previous view_file results)
qdat_samples = [
    {
        "id": "95dae92b",
        "url": "https://datasets-server.huggingface.co/cached-assets/obadx/qdat/--/624d5827f9062bc0203170a00f44375b2adca1f1/--/default/train/0/audio/audio.wav?Expires=1778163619&Signature=Rfqm3nlitLgF6EZDEsoMiRFWj19x4hUf0zYlMBq-OP6RQFFPzQuaEGEx-z9uNFgFp-G5e~3w108HvLlN0yvICKbbmzYu68rJxNOlFEtSsuw2K-iEwNVD-4gIAoEqHIHmfG135liPZBtcVG3As0kPp0Ihr6f~r570BX2wV5dWt3cYC10oQUpi7AfsWodarFkuPwRfv4p99EYPTX7nFc96bJzIYzSUSre2trMtOWIPAOJBxbO3c5hX6Daqqtp-m70X5cty2WaPFj9mwOybDCUIBg9R-Dg47H47LGMz14oDMLA4S~Ok3nvhr4pmdREnyShZw6IBL6VTAFGw63kbOT-Msg__&Key-Pair-Id=K204OQ5RWQVDLD",
        "label": 0 # Correct? Need to verify target mapping
    }
]

ikhlas_samples = [
    {
        "id": "ikhlas_v1_err1",
        "verse": 1,
        "url": "https://datasets-server.huggingface.co/cached-assets/MuazAhmad7/Surah_Ikhlas-Labeled_Dataset/--/973b5ef1d1532bcbe7e9a5a5b0dce125cc4d0dac/--/default/train/0/audio/audio.wav?Expires=1778163633&Signature=I58zp9iaaToTxsSmn9yslX7zr30eSP8p5hq3BZrRnMHtkhsECz21PJEuPUcTQ6iL9mZECmcOeX8-~ETfsuYVQwv8yiArRMOGfq-8MsM6sEZOhLj64YI7ql9fX-RYTum-unWR4reDz2vfgtaiITVCV8Cv3Pj0rR0MNMMUw9O6VRxYEVIjcaJPtzeyEQF6bVy80jaMxnqP-XGZFbk~0tXrZcOmbhXr6VXXM0wQ-r0x-XJRTq24qPxjrNXYJuDbfTxCQx1xDC-lIwRg~a8v5tzuTLuSryReIjGLi-ocv27w8mK19TIWW~GXj05RC3Oq~rB-FApOuREi86XTxFImI12c7Q__&Key-Pair-Id=K204OQ5RWQVDLD",
        "label": "error",
        "explanation": "Qalqalah error on Dal"
    }
]

def main():
    print("Downloading QDAT samples...")
    for s in qdat_samples:
        path = f"ai_bridge/data/test_datasets/qdat/{s['id']}.wav"
        if download_file(s['url'], path):
            print(f"Downloaded {s['id']}")
            
    print("Downloading Ikhlas samples...")
    for s in ikhlas_samples:
        path = f"ai_bridge/data/test_datasets/ikhlas/{s['id']}.wav"
        if download_file(s['url'], path):
            print(f"Downloaded {s['id']}")

if __name__ == "__main__":
    main()
