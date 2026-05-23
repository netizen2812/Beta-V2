import os
import shutil

def download_weights():
    print("=== STARTING WEIGHTS DOWNLOAD FOR FINE-TUNED XTTS MODELS ===")
    
    # 1. Setup paths
    en_dir = "ai_bridge/models/en_xtts_v74"
    ar_dir = "ai_bridge/models/ar_xtts_v75"
    base_dir = "ai_bridge/models/base_xtts"
    
    os.makedirs(en_dir, exist_ok=True)
    os.makedirs(ar_dir, exist_ok=True)
    
    # 2. English v74 download
    print("\n[English Model v74]")
    en_model_dest = os.path.join(en_dir, "model.pth")
    en_config_dest = os.path.join(en_dir, "config.json")
    
    print(" > Downloading English model.pth (best_model.pth)...")
    os.system(f"gcloud storage cp gs://maulana-urdu-forge-project-ffb3710a/en_xtts_v74/best_model.pth {en_model_dest}")
    print(" > Downloading English config.json...")
    os.system(f"gcloud storage cp gs://maulana-urdu-forge-project-ffb3710a/en_xtts_v74/config.json {en_config_dest}")
    
    # Copy vocab.json and speakers_xtts.pth if missing
    for f in ["vocab.json", "speakers_xtts.pth"]:
        dest = os.path.join(en_dir, f)
        if not os.path.exists(dest):
            src = os.path.join(base_dir, f)
            if os.path.exists(src):
                print(f" > Copying {f} from base model to {en_dir}...")
                shutil.copy(src, dest)
            else:
                print(f" > WARNING: Base {f} not found at {src}!")

    # 3. Arabic v75 download
    print("\n[Arabic Model v75]")
    ar_model_dest = os.path.join(ar_dir, "model.pth")
    ar_config_dest = os.path.join(ar_dir, "config.json")
    
    print(" > Downloading Arabic model.pth (best_model.pth)...")
    os.system(f"gcloud storage cp gs://maulana-urdu-forge-project-ffb3710a/ar_xtts_v75/best_model.pth {ar_model_dest}")
    print(" > Downloading Arabic config.json...")
    os.system(f"gcloud storage cp gs://maulana-urdu-forge-project-ffb3710a/ar_xtts_v75/config.json {ar_config_dest}")
    
    # Copy vocab.json and speakers_xtts.pth if missing
    for f in ["vocab.json", "speakers_xtts.pth"]:
        dest = os.path.join(ar_dir, f)
        if not os.path.exists(dest):
            src = os.path.join(base_dir, f)
            if os.path.exists(src):
                print(f" > Copying {f} from base model to {ar_dir}...")
                shutil.copy(src, dest)
            else:
                print(f" > WARNING: Base {f} not found at {src}!")

    # 4. Verify downloads
    print("\n=== VERIFICATION ===")
    for path, name in [(en_dir, "English v74"), (ar_dir, "Arabic v75")]:
        print(f"\nChecking {name} files in {path}:")
        for f in ["model.pth", "config.json", "vocab.json", "speakers_xtts.pth"]:
            full_path = os.path.join(path, f)
            if os.path.exists(full_path):
                size_mb = os.path.getsize(full_path) / (1024 * 1024)
                print(f"  [OK] {f} exists ({size_mb:.2f} MB)")
            else:
                print(f"  [ERROR] {f} is MISSING!")

if __name__ == "__main__":
    download_weights()
