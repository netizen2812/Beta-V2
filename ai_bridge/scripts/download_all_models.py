import os
import shutil
import subprocess

def run_cmd(cmd):
    print(f"Running command: {cmd}")
    ret = os.system(cmd)
    if ret != 0:
        print(f"Warning: command returned exit code {ret}")
    return ret

def download_all_models():
    print("=== STARTING FULL MODEL DOWNLOAD PROCESS ===")
    
    # 1. Setup local directories
    models_dir = os.path.join("ai_bridge", "models")
    base_dir = os.path.join(models_dir, "base_xtts")
    en_dir = os.path.join(models_dir, "en_xtts_v74")
    ur_dir = os.path.join(models_dir, "ur_mms_v32_final", "ur_mms_v32")
    
    os.makedirs(base_dir, exist_ok=True)
    os.makedirs(en_dir, exist_ok=True)
    os.makedirs(ur_dir, exist_ok=True)
    
    # 2. Download Base XTTS v2 model via huggingface_hub
    print("\n[Base XTTS v2 Model]")
    vocab_dest = os.path.join(base_dir, "vocab.json")
    if not os.path.exists(vocab_dest):
        print(" > Downloading base XTTS model from HuggingFace Hub...")
        try:
            from huggingface_hub import snapshot_download
            snapshot_download(
                repo_id="coqui/XTTS-v2",
                local_dir=base_dir,
                local_dir_use_symlinks=False,
                allow_patterns=["model.pth", "config.json", "vocab.json", "speakers_xtts.pth"]
            )
            print(" > Base XTTS downloaded successfully.")
        except Exception as e:
            print(f" > [ERROR] Failed to download base model: {e}")

    else:
        print(" > Base XTTS v2 model already exists.")
        
    # 3. Download English Fine-Tuned Model v74
    print("\n[English Model v74]")
    en_model = os.path.join(en_dir, "model.pth")
    if not os.path.exists(en_model):
        print(" > Downloading English model.pth from GCS...")
        run_cmd(f"gcloud storage cp gs://maulana-urdu-forge-project-ffb3710a/en_xtts_v74/best_model.pth {en_model}")
        run_cmd(f"gcloud storage cp gs://maulana-urdu-forge-project-ffb3710a/en_xtts_v74/config.json {os.path.join(en_dir, 'config.json')}")
        # Copy vocab and speakers from base
        for f in ["vocab.json", "speakers_xtts.pth"]:
            src = os.path.join(base_dir, f)
            dest = os.path.join(en_dir, f)
            if os.path.exists(src) and not os.path.exists(dest):
                shutil.copy(src, dest)
                print(f"   - Copied {f} from base")
    else:
        print(" > English model v74 already exists.")
        
    # 4. Download Urdu Fine-Tuned MMS Model v32
    print("\n[Urdu Model v32]")
    ur_model_config = os.path.join(ur_dir, "config.json")
    if not os.path.exists(ur_model_config):
        print(" > Downloading Urdu model files from GCS...")
        run_cmd(f"gcloud storage cp -r gs://maulana-urdu-forge-project-ffb3710a/ur_mms_v32/final/* {ur_dir}/")
    else:
        print(" > Urdu model v32 already exists.")
        
    print("\n=== VERIFICATION ===")
    all_ok = True
    for path, name, files in [
        (base_dir, "Base XTTS v2", ["model.pth", "config.json", "vocab.json", "speakers_xtts.pth"]),
        (en_dir, "English v74", ["model.pth", "config.json", "vocab.json", "speakers_xtts.pth"]),
        (ur_dir, "Urdu MMS v32", ["config.json", "model.safetensors"])
    ]:
        print(f"\nChecking {name}:")
        for f in files:
            p = os.path.join(path, f)
            if os.path.exists(p):
                print(f"  [OK] {f} exists ({os.path.getsize(p)/(1024*1024):.2f} MB)")
            else:
                print(f"  [MISSING] {f} does not exist!")
                all_ok = False
                
    if all_ok:
        print("\n🎉 ALL MODEL WEIGHTS SUCCESSFULLY DOWNLOADED AND VERIFIED!")
    else:
        print("\n⚠️ SOME MODEL WEIGHTS ARE MISSING. PLEASE CHECK ERRORS ABOVE.")

if __name__ == "__main__":
    download_all_models()
