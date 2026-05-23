import os
import sys

# ── XLA / TPU KILL SWITCH ─────────────────────────────────────────────────────
os.environ["USE_XLA"]              = "0"
os.environ["PJRT_DEVICE"]         = "cpu"
os.environ["XLA_USE_BF16"]        = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["ACCELERATE_USE_XLA"]  = "0"
os.environ["COQUI_TOS_AGREED"]    = "1"

# Monkey-patch torch_xla before it can raise at import time
try:
    import types
    _xla_stub = types.ModuleType("torch_xla")
    _xla_stub.core = types.ModuleType("torch_xla.core")
    _xla_stub.core.xla_model = types.ModuleType("torch_xla.core.xla_model")
    _xla_stub.core.xla_model.xla_device = lambda: None
    _xla_stub.core.xla_model.optimizer_step = lambda *a, **kw: None
    sys.modules.setdefault("torch_xla",                _xla_stub)
    sys.modules.setdefault("torch_xla.core",           _xla_stub.core)
    sys.modules.setdefault("torch_xla.core.xla_model", _xla_stub.core.xla_model)
except Exception:
    pass
# ─────────────────────────────────────────────────────────────────────────────

import argparse
import re
import unicodedata
import torch

print(f"> PyTorch version: {torch.__version__}")
print(f"> CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"> GPU: {torch.cuda.get_device_name(0)}")

from trainer import Trainer, TrainerArgs
from TTS.config.shared_configs import BaseDatasetConfig
from TTS.tts.datasets import load_tts_samples
from TTS.tts.layers.xtts.trainer.gpt_trainer import GPTArgs, GPTTrainer, GPTTrainerConfig, XttsAudioConfig
from TTS.utils.manage import ModelManager


# ── Arabic text cleaner ────────────────────────────────────────────────────────
# XTTS v2 tokenizer handles Arabic but struggles with:
#  1. Diacritics (tashkeel: harakat) → optional marks that the phonemizer is not
#     trained on. Strip them to normalise the token sequence.
#  2. Tatweel / kashida elongation character (U+0640) → purely visual, remove.
#  3. Arabic numerals vs Eastern Arabic digits → normalise to Western digits.
#  4. Punctuation overload → keep only what the tokenizer sees.
ARABIC_DIACRITICS = re.compile(
    r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E4\u06E7\u06E8\u06EA-\u06ED]"
)
ARABIC_TATWEEL  = re.compile(r"\u0640")
EASTERN_DIGITS  = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")


def clean_arabic(text: str) -> str:
    text = ARABIC_DIACRITICS.sub("", text)       # strip tashkeel
    text = ARABIC_TATWEEL.sub("", text)           # strip kashida
    text = text.translate(EASTERN_DIGITS)         # normalise digits
    text = unicodedata.normalize("NFC", text)     # canonical compose
    text = re.sub(r"\s+", " ", text).strip()
    return text


def patch_arabic_samples(samples):
    """Apply Arabic cleaning to every sample's 'text' field in-place."""
    patched = 0
    for s in samples:
        raw = s.get("text", "")
        cleaned = clean_arabic(raw)
        if cleaned != raw:
            s["text"] = cleaned
            patched += 1
    print(f"> Arabic text cleaning: {patched}/{len(samples)} samples modified.")
    return samples


def train_xtts():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang",        type=str,   required=True)
    parser.add_argument("--zip_path",    type=str,   required=True)
    parser.add_argument("--output_dir",  type=str,   required=True)
    # ── v76 KEY CHANGES ──────────────────────────────────────────────────────
    # LR: 5e-6 (10× higher than v75's 5e-7).
    #   Reasoning: The Coqui XTTS official fine-tuning demo uses 5e-6.
    #   At 5e-7 + mel_weight=10.0 the effective gradient signal was too tiny
    #   for the AdamW moment accumulators to move the weights meaningfully
    #   in 18k steps. Grad norm appeared 0 all run because the Coqui Trainer
    #   only computes grad norm AFTER clipping fires — and with near-zero
    #   gradients the clip threshold was never crossed.
    parser.add_argument("--steps",       type=int,   default=20000)
    parser.add_argument("--batch_size",  type=int,   default=2)   # keep 2 for VRAM safety
    parser.add_argument("--lr",          type=float, default=5e-6) # 10× higher than v75
    args = parser.parse_args()

    LOCAL_DATA_DIR = "/tmp/dataset"
    LOCAL_OUTPUT   = "/tmp/output"
    BASE_MODEL_DIR = "/tmp/base_model"
    os.makedirs(LOCAL_DATA_DIR, exist_ok=True)
    os.makedirs(LOCAL_OUTPUT,   exist_ok=True)
    os.makedirs(BASE_MODEL_DIR, exist_ok=True)

    # 1. Download & Extract Dataset
    print(f"--- Starting Fine-tuning for Maulana [{args.lang.upper()}] v76 ---")
    local_zip = "/tmp/dataset.zip"
    print(f"> Downloading dataset from {args.zip_path}...")
    ret = os.system(f"gcloud storage cp {args.zip_path} {local_zip}")
    assert ret == 0, "Dataset download FAILED"
    ret = os.system(f"unzip -q {local_zip} -d {LOCAL_DATA_DIR}")
    assert ret == 0, "Dataset extraction FAILED"

    # ── DATASET AUDIT ─────────────────────────────────────────────────────────
    meta_path = os.path.join(LOCAL_DATA_DIR, "metadata.csv")
    wavs_path = os.path.join(LOCAL_DATA_DIR, "wavs")
    assert os.path.exists(meta_path), f"metadata.csv not found in {LOCAL_DATA_DIR}"
    assert os.path.isdir(wavs_path),  f"wavs/ directory not found in {LOCAL_DATA_DIR}"
    with open(meta_path, "r", encoding="utf-8") as f:
        rows = f.readlines()
    print(f"> Dataset audit: {len(rows)} rows in metadata.csv")
    empty_text = [r for r in rows if r.count("|") >= 1 and r.split("|")[1].strip() == ""]
    if empty_text:
        print(f"  WARNING: {len(empty_text)} rows have empty text — will be skipped by loader.")
    print(f"  Sample row: {rows[0][:120]}")
    # ──────────────────────────────────────────────────────────────────────────

    # 2. Download Base Model
    print("> Downloading XTTS v2 base model files...")
    DVAE_CHECKPOINT_LINK  = "https://coqui.gateway.scarf.sh/hf-coqui/XTTS-v2/main/dvae.pth"
    MEL_NORM_LINK         = "https://coqui.gateway.scarf.sh/hf-coqui/XTTS-v2/main/mel_stats.pth"
    TOKENIZER_FILE_LINK   = "https://coqui.gateway.scarf.sh/hf-coqui/XTTS-v2/main/vocab.json"
    XTTS_CHECKPOINT_LINK  = "https://coqui.gateway.scarf.sh/hf-coqui/XTTS-v2/main/model.pth"

    ModelManager._download_model_files(
        [DVAE_CHECKPOINT_LINK, MEL_NORM_LINK, TOKENIZER_FILE_LINK, XTTS_CHECKPOINT_LINK],
        BASE_MODEL_DIR,
        progress_bar=True,
    )

    DVAE_CHECKPOINT = os.path.join(BASE_MODEL_DIR, "dvae.pth")
    MEL_NORM_FILE   = os.path.join(BASE_MODEL_DIR, "mel_stats.pth")
    TOKENIZER_FILE  = os.path.join(BASE_MODEL_DIR, "vocab.json")
    XTTS_CHECKPOINT = os.path.join(BASE_MODEL_DIR, "model.pth")

    for fp in [DVAE_CHECKPOINT, MEL_NORM_FILE, TOKENIZER_FILE, XTTS_CHECKPOINT]:
        size_mb = os.path.getsize(fp) / 1e6
        print(f"  {os.path.basename(fp)}: {size_mb:.1f} MB")

    # 3. Dataset config
    dataset_config = BaseDatasetConfig(
        formatter="ljspeech",
        dataset_name="maulana_dataset",
        path=LOCAL_DATA_DIR,
        meta_file_train="metadata.csv",
        language=args.lang,
    )

    # 4. Model args — v76 CRITICAL CHANGES
    model_args = GPTArgs(
        max_conditioning_length=132300,   # 6 secs
        min_conditioning_length=66150,    # 3 secs
        debug_loading_failures=False,
        max_wav_length=255995,            # ~11.6 seconds
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
        # v76: REVERT to Coqui defaults (1.0 / 1.0).
        # v75 used mel=10.0 / text=0.001. With LR=5e-7 this caused
        # the mel gradient to be enormous relative to the parameter update
        # scale → gradient clipping zeroed every step.
        gpt_loss_mel_ce_weight=1.0,
        gpt_loss_text_ce_weight=1.0,
    )

    audio_config = XttsAudioConfig(
        sample_rate=22050, dvae_sample_rate=22050, output_sample_rate=24000
    )

    # 5. Training config — v76 CRITICAL CHANGES
    config = GPTTrainerConfig(
        output_path=LOCAL_OUTPUT,
        model_args=model_args,
        run_name=f"maulana_{args.lang}_xtts_v76",
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
        # v76: Use AdamW with standard Coqui XTTS recommended betas.
        # weight_decay reduced from 1e-2 to 1e-4: aggressive L2 was
        # fighting the tiny LR in v75, slowing convergence.
        optimizer="AdamW",
        optimizer_params={
            "betas": [0.9, 0.96],
            "eps": 1e-8,
            "weight_decay": 1e-4,   # ← was 1e-2 in v75
        },
        lr=args.lr,
        # v76: NO OneCycleLR. Use a simple MultiStepLR decay instead.
        # OneCycleLR in v75 fired with total_steps=15000 but the job
        # ran 18170 steps, so the LR had already annealed to near-zero
        # before the last 3000 steps. Also, OneCycleLR's momentum cycling
        # interacts badly with the very small LR range here.
        lr_scheduler="MultiStepLR",
        lr_scheduler_params={
            "milestones": [args.steps // 2, int(args.steps * 0.8)],
            "gamma": 0.5,           # halve LR at 50% and 80% of training
        },
        # v76: Explicit gradient clipping.
        # The Coqui Trainer supports grad_clip. Setting it to 1.0 (the
        # standard NLP value) prevents exploding gradients while keeping
        # the signal alive. This is the Coqui recommended value for XTTS.
        grad_clip=1.0,
        epochs=1000,  # recalculated below
    )

    # 6. Load samples
    print("> Loading samples...")
    train_samples, eval_samples = load_tts_samples(
        [dataset_config],
        eval_split=True,
        eval_split_max_size=config.eval_split_max_size,
        eval_split_size=0.05,
    )

    print(f"> Loaded {len(train_samples)} train / {len(eval_samples)} eval samples.")
    assert len(train_samples) > 10, (
        f"ABORT: Only {len(train_samples)} training samples found. "
        "Check zip structure: metadata.csv at root + wavs/ at root level."
    )

    # v76: Apply Arabic text cleaning AFTER loading samples
    if args.lang == "ar":
        print("> Applying Arabic diacritic / tatweel cleaning...")
        train_samples = patch_arabic_samples(train_samples)
        eval_samples  = patch_arabic_samples(eval_samples)

        # Print a few cleaned samples so the log shows us the text going in
        print("> Sample texts after cleaning (first 5):")
        for s in train_samples[:5]:
            print(f"  {s['text'][:100]}")

    # Calculate epochs
    steps_per_epoch = max(len(train_samples) // args.batch_size, 1)
    config.epochs = (args.steps // steps_per_epoch) + 1
    print(
        f"> Calculated Epochs: {config.epochs} "
        f"(steps_per_epoch={steps_per_epoch}, target={args.steps} steps)"
    )

    # 7. Init model
    print("> Initializing GPTTrainer model...")
    model = GPTTrainer.init_from_config(config)

    # v76: Sanity check — print parameter count & verify CUDA is used
    total_params = sum(p.numel() for p in model.parameters())
    trainable    = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"> Model parameters: {total_params:,} total, {trainable:,} trainable")
    print(f"> Training device: {'CUDA' if torch.cuda.is_available() else 'CPU'}")

    # 8. Init Trainer
    print("> Initializing Trainer...")
    trainer_args = TrainerArgs(
        restore_path=None,
        skip_train_epoch=False,
        start_with_eval=True,   # v76: run eval BEFORE first step so we see baseline loss
        grad_accum_steps=1,
    )

    trainer = Trainer(
        trainer_args,
        config,
        output_path=LOCAL_OUTPUT,
        model=model,
        train_samples=train_samples,
        eval_samples=eval_samples,
    )

    # 9. Train
    print("> Starting training loop (v76 — fixed LR, grad_clip, Arabic cleaning)...")
    trainer.fit()

    # 10. Upload
    print(f"> Syncing results to {args.output_dir}...")
    ret = os.system(f"gcloud storage cp -r {LOCAL_OUTPUT}/* {args.output_dir}")
    print(f"> Upload exit code: {ret}")


if __name__ == "__main__":
    train_xtts()
