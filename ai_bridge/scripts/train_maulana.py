import os
from pathlib import Path
from trainer import Trainer, TrainerArgs
from TTS.config.shared_configs import BaseDatasetConfig
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.datasets import load_tts_samples
from TTS.tts.models.xtts import Xtts

# Path Configuration
import time, random
DATASET_PATH = "data/tts_dataset"
OUTPUT_PATH = "C:/Maulana_Training_Forge"
os.makedirs(OUTPUT_PATH, exist_ok=True)

# NUCLEAR MONKEY-PATCH: Fix for 'LanguageManager' object has no attribute 'save_ids_to_file'
from TTS.tts.utils.languages import LanguageManager
def patch_save_ids_to_file(self, output_path):
    import json
    import os
    os.makedirs(output_path, exist_ok=True)
    with open(os.path.join(output_path, "language_ids.json"), "w") as f:
        json.dump(self.lang_to_id, f)
LanguageManager.save_ids_to_file = patch_save_ids_to_file

class MaulanaTrainer(Trainer):
    def get_criterion(self, model):
        return None

    def train_step(self, batch, *args, **kwargs):
        try:
            return self.model.train_step(batch, self.criterion)
        except TypeError:
            return self.model.train_step(batch)

    def eval_step(self, batch, *args, **kwargs):
        try:
            return self.model.eval_step(batch, self.criterion)
        except TypeError:
            return self.model.eval_step(batch)

def train_maulana():
    print("--- Starting TRILINGUAL Fine-tuning for Maulana [EN + UR + AR] ---")
    
    # 1. Dataset Config (Unified Multilingual)
    dataset_config = BaseDatasetConfig(
        formatter="ljspeech",
        dataset_name="maulana_unified",
        path=str(Path(DATASET_PATH).absolute()),
        meta_file_train="metadata_unified.csv"
    )

    # 2. Model Config (LOCAL MIRROR)
    local_base = os.path.join("models", "base_xtts")
    config_path = os.path.join(local_base, "config.json")
    model_file = os.path.join(local_base, "model.pth")
    
    config = XttsConfig()
    config.load_json(config_path)
    
    config.datasets = [dataset_config]
    config.output_path = str(Path(OUTPUT_PATH).absolute())
    
    # TRILINGUAL OPTIMIZATIONS
    config.batch_size = 1
    config.eval_batch_size = 1
    config.epochs = 15
    config.lr = 1e-6
    
    # 3. Initialize Model
    from TTS.tts.models.xtts import Xtts
    model = Xtts.init_from_config(config)
    
    # 3.5 MONKEY-PATCH LANGUAGE MANAGER (Fix for save_ids_to_file error)
    if hasattr(model, "language_manager") and model.language_manager:
        if not hasattr(model.language_manager, "save_ids_to_file"):
            print(" > Patching LanguageManager.save_ids_to_file...")
            def save_ids_to_file(output_path):
                import json
                with open(os.path.join(output_path, "language_ids.json"), "w") as f:
                    json.dump(model.language_manager.lang_to_id, f)
            model.language_manager.save_ids_to_file = save_ids_to_file
    
    # 4. LINK VOCAB AND SPEAKERS (LOCAL)
    config.model_dir = local_base
    config.model_args.vocab_file = os.path.join(local_base, "vocab.json")
    config.model_args.speaker_file = os.path.join(local_base, "speakers_xtts.pth")
    
    print(f" > Loading base weights from: {model_file}")
    model.load_checkpoint(config, checkpoint_path=model_file, eval=False)
    
    # 5. Load training samples
    train_samples, eval_samples = load_tts_samples(dataset_config, eval_split=True)

    # 6. Initialize CUSTOM Trainer
    # NUCLEAR MOCK: Bypass read-only LanguageManager properties
    class MockLanguageManager:
        def __init__(self):
            self.name_to_id = {"en": 0, "ur": 1, "ar": 2, "": 0}
            self.lang_to_id = self.name_to_id
        def save_ids_to_file(self, x):
            print(" > Skipping LanguageManager.save_ids_to_file")
    
    model.language_manager = MockLanguageManager()

    # FIX for AttributeError: 'XttsArgs' object has no attribute 'use_language_embedding'
    if not hasattr(model.args, "use_language_embedding"):
        model.args.use_language_embedding = True
        
    # FIX for AttributeError: 'XttsConfig' object has no attribute 'use_d_vector_file'
    if not hasattr(config, "use_d_vector_file"):
        config.use_d_vector_file = False
    
    # FIX for AttributeError: 'XttsConfig' object has no attribute 'r'
    if not hasattr(config, "r"):
        config.r = 1
        
    # FIX for AttributeError: 'VoiceBpeTokenizer' object has no attribute 'use_phonemes'
    if hasattr(model, "tokenizer") and model.tokenizer is not None:
        if not hasattr(model.tokenizer, "use_phonemes"):
            model.tokenizer.use_phonemes = False
        if not hasattr(model.tokenizer, "print_logs"):
            model.tokenizer.print_logs = lambda level: print(" > Tokenizer logs skipped.")
        if not hasattr(model.tokenizer, "text_to_ids"):
            # XTTS tokenizer uses 'encode' instead of 'text_to_ids'
            # We provide a default 'en' but it will process the trilingual text vectors
            model.tokenizer.text_to_ids = lambda text: model.tokenizer.encode(text, lang="en")
            
    # FIX for AttributeError: 'NoneType' object has no attribute 'load_wav'
    from TTS.utils.audio import AudioProcessor
    # Use standard XTTS audio defaults to avoid NoneType errors
    audio_config = {
        "sample_rate": 22050,
        "resample": False,
        "do_trim_silence": False,
        "frame_length_ms": 60,
        "frame_shift_ms": 20,
        "fft_size": 2048,
        "num_mels": 80,
        "mel_fmin": 0,
        "mel_fmax": None
    }
    model.ap = AudioProcessor(verbose=False, **audio_config)

    trainer = MaulanaTrainer(
        TrainerArgs(
            restore_path=None, 
            skip_train_epoch=False,
            start_with_eval=False,
            grad_accum_steps=8
        ),
        config,
        str(Path(OUTPUT_PATH).absolute()),
        model=model,
        train_samples=train_samples,
        eval_samples=eval_samples
    )

    # RE-IGNITE
    trainer.fit()

if __name__ == "__main__":
    train_maulana()
