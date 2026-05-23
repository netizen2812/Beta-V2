import os
import sys

# ── XLA / TPU KILL SWITCH ─────────────────────────────────────────────────────
# Must be set BEFORE any torch / TTS / trainer import.
# The Coqui Trainer probes torch_xla on startup; this prevents the
#   std::runtime_error: $PJRT_DEVICE is not set
# SIGSEGV crash that terminates the job at the start of trainer.fit().
os.environ["USE_XLA"]              = "0"
os.environ["PJRT_DEVICE"]         = "cpu"        # set to cpu so torch_xla doesn't abort
os.environ["XLA_USE_BF16"]        = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["ACCELERATE_USE_XLA"]  = "0"

# Monkey-patch torch_xla before it can raise at import time
try:
    import importlib, types
    _xla_stub = types.ModuleType("torch_xla")
    _xla_stub.core = types.ModuleType("torch_xla.core")
    _xla_stub.core.xla_model = types.ModuleType("torch_xla.core.xla_model")
    _xla_stub.core.xla_model.xla_device = lambda: None
    _xla_stub.core.xla_model.optimizer_step = lambda *a, **kw: None
    sys.modules.setdefault("torch_xla",            _xla_stub)
    sys.modules.setdefault("torch_xla.core",       _xla_stub.core)
    sys.modules.setdefault("torch_xla.core.xla_model", _xla_stub.core.xla_model)
except Exception:
    pass
# ─────────────────────────────────────────────────────────────────────────────

import argparse
import torch
from trainer import Trainer, TrainerArgs
from TTS.config.shared_configs import BaseDatasetConfig
from TTS.tts.datasets import load_tts_samples
from TTS.tts.layers.xtts.trainer.gpt_trainer import GPTArgs, GPTTrainer, GPTTrainerConfig, XttsAudioConfig
from TTS.utils.manage import ModelManager

# Set TOS agreement
os.environ["COQUI_TOS_AGREED"] = "1"


def train_xtts():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", type=str, required=True)
    parser.add_argument("--zip_path", type=str, required=True)
    parser.add_argument("--output_dir", type=str, required=True)
    parser.add_argument("--steps", type=int, default=15000)   # was 5000 — too few for XTTS fine-tuning
    parser.add_argument("--batch_size", type=int, default=4)   # was 2 — more stable gradient estimates
    parser.add_argument("--lr", type=float, default=5e-7)      # was 5e-6 — 10x reduction prevents GPT decoder divergence
    args = parser.parse_args()

    LOCAL_DATA_DIR = "/tmp/dataset"
    LOCAL_OUTPUT = "/tmp/output"
    BASE_MODEL_DIR = "/tmp/base_model"
    os.makedirs(LOCAL_DATA_DIR, exist_ok=True)
    os.makedirs(LOCAL_OUTPUT, exist_ok=True)
    os.makedirs(BASE_MODEL_DIR, exist_ok=True)

    # 1. Download & Extract Dataset
    print(f"--- Starting Fine-tuning for Maulana [{args.lang.upper()}] ---")
    local_zip = "/tmp/dataset.zip"
    print(f"> Downloading dataset from {args.zip_path}...")
    os.system(f"gcloud storage cp {args.zip_path} {local_zip}")
    os.system(f"unzip -q {local_zip} -d {LOCAL_DATA_DIR}")

    # 2. Download Base Model Files (Manual download to ensure compatibility)
    print("> Downloading base model files...")
    # These are the standard XTTS v2.0.2 URLs
    DVAE_CHECKPOINT_LINK = "https://coqui.gateway.scarf.sh/hf-coqui/XTTS-v2/main/dvae.pth"
    MEL_NORM_LINK = "https://coqui.gateway.scarf.sh/hf-coqui/XTTS-v2/main/mel_stats.pth"
    TOKENIZER_FILE_LINK = "https://coqui.gateway.scarf.sh/hf-coqui/XTTS-v2/main/vocab.json"
    XTTS_CHECKPOINT_LINK = "https://coqui.gateway.scarf.sh/hf-coqui/XTTS-v2/main/model.pth"

    ModelManager._download_model_files(
        [DVAE_CHECKPOINT_LINK, MEL_NORM_LINK, TOKENIZER_FILE_LINK, XTTS_CHECKPOINT_LINK],
        BASE_MODEL_DIR,
        progress_bar=True
    )

    DVAE_CHECKPOINT = os.path.join(BASE_MODEL_DIR, "dvae.pth")
    MEL_NORM_FILE = os.path.join(BASE_MODEL_DIR, "mel_stats.pth")
    TOKENIZER_FILE = os.path.join(BASE_MODEL_DIR, "vocab.json")
    XTTS_CHECKPOINT = os.path.join(BASE_MODEL_DIR, "model.pth")

    # 3. Setup Dataset Config
    dataset_config = BaseDatasetConfig(
        formatter="ljspeech",
        dataset_name="maulana_dataset",
        path=LOCAL_DATA_DIR,
        meta_file_train="metadata.csv",
        language=args.lang
    )

    # 4. Setup Model Args
    model_args = GPTArgs(
        max_conditioning_length=132300, # 6 secs
        min_conditioning_length=66150,  # 3 secs
        debug_loading_failures=False,
        max_wav_length=255995,          # ~11.6 seconds
        max_text_length=200,
        mel_norm_file=MEL_NORM_FILE,
        dvae_checkpoint=DVAE_CHECKPOINT,
        xtts_checkpoint=XTTS_CHECKPOINT,
        tokenizer_file=TOKENIZER_FILE,
        gpt_num_audio_tokens=1026,
        gpt_start_audio_token=1024,
        gpt_stop_audio_token=1025,
        gpt_use_masking_gt_prompt_approach=True,
        gpt_use_perceiver_resampler=True,
        gpt_loss_mel_ce_weight=10.0,    # Force gradients to prioritize audio reconstruction
        gpt_loss_text_ce_weight=0.001,  # Downscale text head to prevent rapid memorization
    )

    audio_config = XttsAudioConfig(sample_rate=22050, dvae_sample_rate=22050, output_sample_rate=24000)

    # 5. Setup Training Config
    config = GPTTrainerConfig(
        output_path=LOCAL_OUTPUT,
        model_args=model_args,
        run_name=f"maulana_{args.lang}_xtts",
        project_name="Maulana_AI",
        audio=audio_config,
        batch_size=args.batch_size,
        batch_group_size=48,
        num_loader_workers=0,
        eval_split_max_size=256,
        print_step=50,
        plot_step=100,
        log_model_step=500,
        save_step=1000,
        save_n_checkpoints=2,
        save_checkpoints=True,
        optimizer="AdamW",
        optimizer_params={"betas": [0.9, 0.96], "eps": 1e-8, "weight_decay": 1e-2},
        lr=args.lr,
        lr_scheduler="OneCycleLR",
        lr_scheduler_params={
            "max_lr": args.lr,
            "total_steps": args.steps,
            "pct_start": 0.05, # 5% warmup (750 steps for 15k steps)
            "anneal_strategy": "cos",
            "cycle_momentum": False
        },
        epochs=1000, # Will be recalculated below
    )

    # 6. Initialize Model & Samples
    print("> Loading samples...")
    train_samples, eval_samples = load_tts_samples(
        [dataset_config],
        eval_split=True,
        eval_split_max_size=config.eval_split_max_size,
        eval_split_size=0.05
    )

    # --- GUARD: Abort immediately if dataset wasn't loaded correctly ---
    print(f"> Loaded {len(train_samples)} train / {len(eval_samples)} eval samples.")
    assert len(train_samples) > 10, (
        f"ABORT: Only {len(train_samples)} training samples found. "
        "This almost certainly means the zip structure doesn't match LJSpeech format. "
        "Expected: metadata.csv at root + wavs/ subdirectory at the same level."
    )

    # Calculate epochs to reach desired steps
    steps_per_epoch = max(len(train_samples) // args.batch_size, 1)
    config.epochs = (args.steps // steps_per_epoch) + 1
    print(f"> Calculated Epochs: {config.epochs} (steps_per_epoch={steps_per_epoch}, target={args.steps} steps)")

    print("> Initializing GPTTrainer model...")
    model = GPTTrainer.init_from_config(config)

    # 7. Initialize Trainer
    print("> Initializing Trainer...")
    trainer_args = TrainerArgs(
        restore_path=None,
        skip_train_epoch=False,
        start_with_eval=False,
        grad_accum_steps=1, 
    )

    trainer = Trainer(
        trainer_args,
        config,
        output_path=LOCAL_OUTPUT,
        model=model,
        train_samples=train_samples,
        eval_samples=eval_samples
    )

    # 8. Start Training
    print("> Starting training loop...")
    trainer.fit()

    # 9. Sync results to GCS
    print(f"> Syncing results to {args.output_dir}...")
    os.system(f"gcloud storage cp -r {LOCAL_OUTPUT}/* {args.output_dir}")

if __name__ == "__main__":
    train_xtts()
