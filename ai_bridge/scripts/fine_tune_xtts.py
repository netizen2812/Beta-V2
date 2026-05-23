import os
from trainer import Trainer, TrainerArgs
from TTS.config.shared_configs import BaseDatasetConfig
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.datasets import load_tts_samples
from TTS.tts.models.xtts import Xtts
from TTS.utils.downloaders import download_xtts

# Paths
DATASET_PATH = "ai_bridge/data/tts_dataset"
OUTPUT_PATH = "ai_bridge/models/maulana_finetune"
CHECKPOINTS_OUT_PATH = os.path.join(OUTPUT_PATH, "checkpoints")

def fine_tune(language="en"):
    print(f"--- Starting Fine-tuning for Maulana [{language.upper()}] ---")
    
    # 1. Download base model if not exists
    model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
    release_path = download_xtts(model_name)
    
    config_path = os.path.join(release_path, "config.json")
    checkpoint_dir = release_path
    
    # 2. Setup Dataset Config
    dataset_config = BaseDatasetConfig(
        formatter="ljspeech",
        dataset_name="maulana_dataset",
        path=DATASET_PATH,
        meta_file_train=f"metadata_{language}.csv",
        wav_dir=f"wavs_{language}"
    )
    
    # 3. Load Config
    config = XttsConfig()
    config.load_json(config_path)
    
    # 4. Update Config for Fine-tuning
    config.epochs = 10
    config.batch_size = 2
    config.lr = 5e-6
    config.save_step = 1000
    config.output_path = OUTPUT_PATH
    config.datasets = [dataset_config]
    
    # 5. Initialize Model
    model = Xtts.init_from_config(config)
    model.load_checkpoint(config, checkpoint_dir=checkpoint_dir, eval=False)
    model.cuda()
    
    # 6. Load Samples
    train_samples, eval_samples = load_tts_samples(
        dataset_config,
        eval_split=True,
        eval_split_max_size=32,
        eval_split_size=0.1
    )
    
    # 7. Initialize Trainer
    trainer = Trainer(
        TrainerArgs(
            output_path=OUTPUT_PATH,
            checkpoint_path=CHECKPOINTS_OUT_PATH,
            device="cuda"
        ),
        config,
        OUTPUT_PATH,
        model=model,
        train_samples=train_samples,
        eval_samples=eval_samples
    )
    
    # 8. Start Training
    trainer.fit()

if __name__ == "__main__":
    # Ensure directories exist
    os.makedirs(OUTPUT_PATH, exist_ok=True)
    
    # Fine-tune English Maulana
    fine_tune(language="en")
    
    # To fine-tune Urdu, run:
    # fine_tune(language="ur")
