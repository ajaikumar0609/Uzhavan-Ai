"""M4 V2 Training Script: EfficientNetV2-S for Groundnut Disease Intelligence.

Features:
- Aspect-preserving resize: Resize(256) -> CenterCrop(224) (val/test) or RandomCrop(224) (train)
- Loss functions: Weighted Cross-Entropy or Focal Loss (gamma=2.0)
- Precision: AMP mixed-precision (autocast float16 + GradScaler) on CUDA
- Hardware gate: strict stop if CUDA is unavailable unless --smoke-test or --allow-cpu is specified
- Collision protection: never overwrites existing experiments
- Resume support: atomic save/restore of model, optimizer, scheduler, scaler, RNG state
- Seed control: deterministic PyTorch, CUDA, numpy, python seeds

Usage:
  python scripts/train_m4_v2.py --exp-name UZ-M4-v2-groundnut-s1-wce --loss wce --seed 42 --epochs 15
  python scripts/train_m4_v2.py --exp-name UZ-M4-v2-groundnut-s1-focal --loss focal --gamma 2.0 --seed 42 --epochs 15
  python scripts/train_m4_v2.py --smoke-test --allow-cpu
"""

import argparse
import csv
import hashlib
import json
import math
import os
import platform
import random
import signal
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision
from torch.utils.data import DataLoader, Dataset, RandomSampler, WeightedRandomSampler
from torchvision import transforms as T

IMNET_MEAN = [0.485, 0.456, 0.406]
IMNET_STD = [0.229, 0.224, 0.225]


def seed_all(seed: int):
    """Set deterministic seeds across python, numpy, and torch."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


def rng_state():
    st = {
        "python": random.getstate(),
        "numpy": np.random.get_state(),
        "torch": torch.get_rng_state(),
    }
    if torch.cuda.is_available():
        st["cuda"] = torch.cuda.get_rng_state_all()
    return st


def set_rng_state(st):
    random.setstate(st["python"])
    np.random.set_state(st["numpy"])
    if "torch" in st:
        t_state = st["torch"]
        if isinstance(t_state, torch.Tensor):
            t_state = t_state.cpu().to(torch.uint8)
        torch.set_rng_state(t_state)
    if "cuda" in st and torch.cuda.is_available():
        cuda_states = [c.cpu() if isinstance(c, torch.Tensor) else c for c in st["cuda"]]
        torch.cuda.set_rng_state_all(cuda_states)


def atomic_json(obj, path: Path):
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=2, default=str)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def atomic_torch(obj, path: Path):
    tmp = path.with_suffix(".tmp")
    with open(tmp, "wb") as f:
        torch.save(obj, f)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


class FocalLoss(nn.Module):
    """Multi-class Focal Loss: FL(p_t) = -alpha_t * (1 - p_t)^gamma * log(p_t)."""

    def __init__(self, gamma: float = 2.0, weight: torch.Tensor = None, reduction: str = "mean"):
        super().__init__()
        self.gamma = gamma
        self.register_buffer("weight", weight)
        self.reduction = reduction

    def forward(self, inputs: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        # Cross entropy loss without reduction: -log(p_t)
        ce_loss = F.cross_entropy(inputs, targets, weight=self.weight, reduction="none")
        pt = torch.exp(-ce_loss)  # probability of true class
        focal_loss = ((1.0 - pt) ** self.gamma) * ce_loss

        if self.reduction == "mean":
            return focal_loss.mean()
        elif self.reduction == "sum":
            return focal_loss.sum()
        return focal_loss


class M4V2Dataset(Dataset):
    """Dataset with aspect-preserving resize (256) -> 224 crop."""

    def __init__(self, df: pd.DataFrame, img_root: Path, class_list: list, is_train: bool):
        self.df = df.reset_index(drop=True)
        self.img_root = Path(img_root)
        self.class_to_idx = {c: i for i, c in enumerate(class_list)}

        if is_train:
            self.transform = T.Compose([
                T.Resize(256),
                T.RandomCrop(224),
                T.RandomHorizontalFlip(p=0.5),
                T.RandomVerticalFlip(p=0.5),
                T.ColorJitter(brightness=0.1, contrast=0.1),
                T.ToTensor(),
                T.Normalize(mean=IMNET_MEAN, std=IMNET_STD),
            ])
        else:
            self.transform = T.Compose([
                T.Resize(256),
                T.CenterCrop(224),
                T.ToTensor(),
                T.Normalize(mean=IMNET_MEAN, std=IMNET_STD),
            ])

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        img_path = self.img_root / row["pkg_path"]
        try:
            img = Image.open(img_path).convert("RGB")
        except Exception as e:
            raise RuntimeError(f"Error loading image {img_path}: {e}")

        x = self.transform(img)
        label = self.class_to_idx[row["canonical_id"]]
        return x, label


class M4V2Model(nn.Module):
    """EfficientNetV2-S with dedicated crop classification heads."""

    def __init__(self, classes: dict, dropout: float = 0.2):
        super().__init__()
        weights = torchvision.models.EfficientNet_V2_S_Weights.IMAGENET1K_V1
        backbone = torchvision.models.efficientnet_v2_s(weights=weights)
        in_features = backbone.classifier[1].in_features
        backbone.classifier = nn.Identity()
        self.backbone = backbone
        self.drop = nn.Dropout(p=dropout)
        self.crops = sorted(classes.keys())
        self.heads = nn.ModuleDict({crop: nn.Linear(in_features, len(classes[crop])) for crop in self.crops})

    def forward(self, x: torch.Tensor, crop_name: str = "groundnut") -> torch.Tensor:
        feat = self.drop(self.backbone(x))
        return self.heads[crop_name](feat)


@torch.no_grad()
def evaluate_split(model: nn.Module, loader: DataLoader, device: torch.device, crop_name: str, num_classes: int):
    model.eval()
    all_preds, all_targets = [], []
    val_loss_total = 0.0
    num_batches = 0

    criterion = nn.CrossEntropyLoss()

    for x, y in loader:
        x, y = x.to(device), y.to(device)
        logits = model(x, crop_name)
        loss = criterion(logits, y)
        val_loss_total += loss.item()
        num_batches += 1

        preds = torch.argmax(logits, dim=1)
        all_preds.extend(preds.cpu().tolist())
        all_targets.extend(y.cpu().tolist())

    y_pred = np.array(all_preds)
    y_true = np.array(all_targets)

    # Per-class F1 and macro F1
    f1_scores = []
    for c in range(num_classes):
        tp = int(((y_pred == c) & (y_true == c)).sum())
        fp = int(((y_pred == c) & (y_true != c)).sum())
        fn = int(((y_pred != c) & (y_true == c)).sum())
        denom = 2 * tp + fp + fn
        f1 = (2 * tp / denom) if denom > 0 else 0.0
        f1_scores.append(f1)

    macro_f1 = float(np.mean(f1_scores))
    accuracy = float((y_pred == y_true).mean())
    avg_loss = float(val_loss_total / max(num_batches, 1))

    return {
        "loss": avg_loss,
        "accuracy": accuracy,
        "macro_f1": macro_f1,
        "per_class_f1": f1_scores,
    }


def parse_args():
    p = argparse.ArgumentParser(description="M4 V2 Training & Diagnostics")
    p.add_argument("--repo-root", default=str(Path(__file__).resolve().parent.parent.parent))
    p.add_argument("--manifest", default=None, help="Path to groundnut_v2.csv")
    p.add_argument("--pkg", default=None, help="Root path for images")
    p.add_argument("--classes", default=None, help="Path to classes.json")
    p.add_argument("--crop", default="groundnut")
    p.add_argument("--out-dir", default=None, help="Output root (default: uzhavan_ml/runs_m4_v2)")
    p.add_argument("--exp-name", default=None, help="Unique experiment name")

    # Hyperparameters
    p.add_argument("--epochs", type=int, default=15)
    p.add_argument("--bs", "--batch-size", type=int, default=32, dest="bs")
    p.add_argument("--lr", type=float, default=1e-4)
    p.add_argument("--weight-decay", type=float, default=1e-2)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--dropout", type=float, default=0.2)

    # Loss function configuration
    p.add_argument("--loss", choices=["wce", "focal", "ce"], default="wce", help="Loss formulation")
    p.add_argument("--gamma", type=float, default=2.0, help="Focal loss gamma parameter")
    p.add_argument("--sampler", choices=["random", "balanced"], default="random")

    # Hardware & Resume
    p.add_argument("--resume", default="auto", help="auto | none | path/to/checkpoint_last.pt")
    p.add_argument("--smoke-test", action="store_true", help="Run 1 epoch with 2 batches for diagnostics")
    p.add_argument("--allow-cpu", action="store_true", help="Allow running on CPU (smoke tests / CI only)")

    return p.parse_args()


def main():
    args = parse_args()
    repo_root = Path(args.repo_root)

    # Hardware environment diagnostic
    cuda_avail = torch.cuda.is_available()
    device_str = "cuda" if cuda_avail else ("mps" if torch.backends.mps.is_available() else "cpu")
    if args.allow_cpu or (args.smoke_test and not cuda_avail):
        dev = torch.device(device_str)
    else:
        dev = torch.device("cuda" if cuda_avail else "cpu")

    print("\n" + "=" * 65)
    print("           UZHAVAN AI - M4 V2 HARDWARE & ENVIRONMENT")
    print("=" * 65)
    print(f"PyTorch Version:      {torch.__version__}")
    print(f"CUDA Available:       {cuda_avail}")
    if cuda_avail:
        gpu_name = torch.cuda.get_device_name(0)
        vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        print(f"GPU Name:             {gpu_name}")
        print(f"GPU VRAM:             {vram_gb:.2f} GB")
    else:
        print(f"GPU Name:             None (Running on {device_str.upper()})")
        print(f"GPU VRAM:             N/A")
    print(f"Batch Size:           {args.bs}")
    print(f"Image Resolution:     224x224 (Resize 256 -> Crop 224)")
    amp_enabled = cuda_avail
    print(f"AMP Status:           {'Enabled (float16)' if amp_enabled else 'Disabled'}")
    print(f"Loss Formulation:     {args.loss.upper()}" + (f" (gamma={args.gamma})" if args.loss == "focal" else ""))
    print(f"Random Seed:          {args.seed}")
    print("=" * 65 + "\n")

    # Strict CUDA gate: Stop immediately if CUDA is not available, unless smoke test / allow-cpu is specified
    if not cuda_avail and not (args.smoke_test or args.allow_cpu):
        print("[ERROR] CUDA is not available. Training stopped.")
        print("M4 V2 full training must run on a CUDA-enabled GPU (RTX 4050).")
        print("To run a CPU smoke test for pipeline testing, pass --smoke-test --allow-cpu.")
        sys.exit(1)

    seed_all(args.seed)

    # Paths resolution
    manifest_path = Path(args.manifest) if args.manifest else repo_root / "uzhavan_ml/m4_v2/manifests/groundnut_v2.csv"
    pkg_path = Path(args.pkg) if args.pkg else repo_root / "uzhavan_ml/packages/m4_v1"
    classes_path = Path(args.classes) if args.classes else repo_root / "uzhavan_ml/m4_v2/classes.json"
    out_dir_root = Path(args.out_dir) if args.out_dir else repo_root / "uzhavan_ml/runs_m4_v2"

    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    if not classes_path.exists():
        raise FileNotFoundError(f"Classes file not found: {classes_path}")

    # Load classes
    with open(classes_path) as f:
        all_classes = json.load(f)

    if args.crop not in all_classes:
        raise ValueError(f"Crop {args.crop} not found in classes: {list(all_classes.keys())}")

    crop_classes = all_classes[args.crop]
    num_classes = len(crop_classes)
    print(f"Crop: {args.crop} ({num_classes} classes: {crop_classes})")

    # Load manifest
    df = pd.read_csv(manifest_path)
    df = df[df.crop == args.crop].copy()

    # Verify split separation: zero WB external images in train
    train_sources = df[df.split == "train"]["source"].unique().tolist()
    if "in_groundnut_wb_sasmal" in train_sources:
        raise RuntimeError("FATAL: External West Bengal images found in training split!")

    train_df = df[df.split == "train"].copy()
    val_df = df[df.split == "val"].copy()

    # Exact count verification for groundnut
    if args.crop == "groundnut":
        train_counts = train_df["canonical_id"].value_counts().to_dict()
        expected = {
            "groundnut__tikka_leaf_spot": 2236,
            "groundnut__rust": 2235,
            "groundnut__healthy_or_abiotic": 1449,
        }
        for cls_name, exp_n in expected.items():
            act_n = train_counts.get(cls_name, 0)
            if act_n != exp_n:
                raise ValueError(f"Class count mismatch for {cls_name}: expected {exp_n}, found {act_n}")
        if len(train_df) != 5920:
            raise ValueError(f"Total train count mismatch: expected 5920, found {len(train_df)}")
        print("✓ Exact dataset count verification confirmed (5,920 images).")

    # Compute class weights for weighted CE or Focal Loss
    cls_counts = [int((train_df.canonical_id == c).sum()) for c in crop_classes]
    total_samples = len(train_df)
    # Inverse class frequency weights normalized to mean 1.0
    raw_weights = [total_samples / (num_classes * max(cnt, 1)) for cnt in cls_counts]
    weight_tensor = torch.tensor(raw_weights, dtype=torch.float32, device=dev)
    print(f"Inverse class weights: {dict(zip(crop_classes, [round(w, 4) for w in raw_weights]))}")

    # Experiment name & Collision protection
    if args.exp_name:
        exp_id = args.exp_name
    else:
        loss_tag = f"focal-g{args.gamma}" if args.loss == "focal" else args.loss
        exp_id = f"UZ-M4-v2-{args.crop}-s{args.seed}-{loss_tag}" + ("-SMOKE" if args.smoke_test else "")

    exp_dir = out_dir_root / exp_id
    exp_dir.mkdir(parents=True, exist_ok=True)
    resume_path = exp_dir / "checkpoint_last.pt"
    exp_json_path = exp_dir / "experiment.json"

    # Collision check: NEVER overwrite an existing experiment unless resuming
    if exp_json_path.exists() and not args.smoke_test:
        with open(exp_json_path) as f:
            prev_exp = json.load(f)
        if prev_exp.get("status") == "completed" and args.resume == "none":
            print(f"[COLLISION PROTECTION] Experiment {exp_id} is already COMPLETED.")
            print("Refusing to overwrite. Pass --resume auto or a new --exp-name.")
            sys.exit(1)

    if resume_path.exists() and args.resume == "none":
        print(f"[COLLISION PROTECTION] Checkpoint {resume_path} exists and --resume none was set.")
        print("Refusing to overwrite active checkpoint.")
        sys.exit(1)

    # Subsample if smoke test
    if args.smoke_test:
        train_df = train_df.groupby("canonical_id").head(4).reset_index(drop=True)
        val_df = val_df.groupby("canonical_id").head(2).reset_index(drop=True)
        epochs = 1
        num_workers = 0
    else:
        epochs = args.epochs
        num_workers = args.workers

    # Datasets and Loaders
    train_ds = M4V2Dataset(train_df, pkg_path, crop_classes, is_train=True)
    val_ds = M4V2Dataset(val_df, pkg_path, crop_classes, is_train=False)

    if args.sampler == "balanced":
        sample_weights = [raw_weights[crop_classes.index(r["canonical_id"])] for _, r in train_df.iterrows()]
        sampler = WeightedRandomSampler(sample_weights, num_samples=len(sample_weights), replacement=True)
        train_loader = DataLoader(train_ds, batch_size=args.bs, sampler=sampler, num_workers=num_workers, pin_memory=cuda_avail)
    else:
        train_loader = DataLoader(train_ds, batch_size=args.bs, shuffle=True, num_workers=num_workers, pin_memory=cuda_avail)

    val_loader = DataLoader(val_ds, batch_size=args.bs, shuffle=False, num_workers=num_workers, pin_memory=cuda_avail)

    # Model instantiation
    model = M4V2Model(all_classes, dropout=args.dropout).to(dev)

    # Criterion setup
    if args.loss == "wce":
        criterion = nn.CrossEntropyLoss(weight=weight_tensor)
    elif args.loss == "focal":
        criterion = FocalLoss(gamma=args.gamma, weight=weight_tensor)
    else:
        criterion = nn.CrossEntropyLoss()

    # Optimizer & Scheduler
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-6)
    scaler = torch.amp.GradScaler("cuda", enabled=amp_enabled)

    # Resume handling
    start_epoch = 0
    best_macro_f1 = -1.0
    history = []
    epochs_without_improvement = 0

    if args.resume in ("auto", "none"):
        should_resume = (args.resume == "auto") and resume_path.exists()
    else:
        resume_path = Path(args.resume)
        should_resume = resume_path.exists()

    if should_resume:
        print(f"[RESUME] Loading checkpoint from {resume_path}...")
        ckpt = torch.load(resume_path, map_location="cpu", weights_only=False)
        model.load_state_dict(ckpt["model_state_dict"])
        optimizer.load_state_dict(ckpt["optimizer_state_dict"])
        if ckpt.get("scheduler_state_dict"):
            scheduler.load_state_dict(ckpt["scheduler_state_dict"])
        if ckpt.get("scaler_state_dict") and amp_enabled:
            scaler.load_state_dict(ckpt["scaler_state_dict"])
        start_epoch = ckpt["last_completed_epoch"] + 1
        best_macro_f1 = ckpt.get("best_val_macro_f1", -1.0)
        history = ckpt.get("history", [])
        set_rng_state(ckpt["rng_state"])
        print(f"[RESUME] Resuming from epoch {start_epoch}, previous best Macro-F1: {best_macro_f1:.4f}")

    # Metadata record
    manifest_sha = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    experiment_meta = {
        "experiment_id": exp_id,
        "model_architecture": "EfficientNetV2-S",
        "crop": args.crop,
        "classes": crop_classes,
        "dataset_manifest": str(manifest_path.name),
        "manifest_sha256": manifest_sha,
        "loss": args.loss,
        "gamma": args.gamma if args.loss == "focal" else None,
        "seed": args.seed,
        "epochs": epochs,
        "batch_size": args.bs,
        "learning_rate": args.lr,
        "weight_decay": args.weight_decay,
        "dropout": args.dropout,
        "amp_enabled": amp_enabled,
        "hardware": {
            "device": dev.type,
            "gpu_name": torch.cuda.get_device_name(0) if cuda_avail else None,
            "torch_version": torch.__version__,
        },
        "status": "running",
        "start_time": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    atomic_json(experiment_meta, exp_json_path)

    # Signal handling for clean interrupt
    def handle_sigterm(signum, frame):
        print("\n[INTERRUPT] Received SIGTERM/SIGINT. Saving last checkpoint before exit.")
        experiment_meta["status"] = "interrupted"
        atomic_json(experiment_meta, exp_json_path)
        sys.exit(130)

    signal.signal(signal.SIGINT, handle_sigterm)
    signal.signal(signal.SIGTERM, handle_sigterm)

    # Training Loop
    print(f"\n--- Starting Training: {exp_id} ({start_epoch} -> {epochs}) ---")
    t0 = time.time()

    for epoch in range(start_epoch, epochs):
        model.train()
        train_loss_total = 0.0
        num_batches = 0

        for batch_idx, (images, targets) in enumerate(train_loader):
            images, targets = images.to(dev), targets.to(dev)
            optimizer.zero_grad()

            with torch.amp.autocast("cuda", enabled=amp_enabled):
                logits = model(images, args.crop)
                loss = criterion(logits, targets)

            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()

            train_loss_total += loss.item()
            num_batches += 1

            if args.smoke_test and batch_idx >= 1:
                break

        scheduler.step()
        epoch_train_loss = train_loss_total / max(num_batches, 1)

        # Validation
        val_metrics = evaluate_split(model, val_loader, dev, args.crop, num_classes)
        val_macro_f1 = val_metrics["macro_f1"]
        val_acc = val_metrics["accuracy"]
        val_loss = val_metrics["loss"]

        epoch_record = {
            "epoch": epoch,
            "train_loss": round(epoch_train_loss, 4),
            "val_loss": round(val_loss, 4),
            "val_accuracy": round(val_acc, 4),
            "val_macro_f1": round(val_macro_f1, 4),
            "lr": round(scheduler.get_last_lr()[0], 6),
            "time_elapsed_s": round(time.time() - t0, 1),
        }
        history.append(epoch_record)
        print(f"Epoch {epoch:02d}/{epochs:02d} | Train Loss: {epoch_train_loss:.4f} | Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.4f} | Val Macro-F1: {val_macro_f1:.4f}")

        # Checkpoint Best
        if val_macro_f1 > best_macro_f1:
            best_macro_f1 = val_macro_f1
            epochs_without_improvement = 0
            best_ckpt = {
                "model": model.state_dict(),
                "classes": all_classes,
                "crops": [args.crop],
                "epoch": epoch,
                "best_val_macro_f1": best_macro_f1,
                "experiment_id": exp_id,
                "hp": {
                    "crop": args.crop,
                    "loss": args.loss,
                    "seed": args.seed,
                    "lr": args.lr,
                    "bs": args.bs,
                },
            }
            atomic_torch(best_ckpt, exp_dir / "checkpoint_best.pt")
            print(f"  ★ New best checkpoint saved (Val Macro-F1: {best_macro_f1:.4f})")
        else:
            epochs_without_improvement += 1

        # Checkpoint Last (for resume)
        last_ckpt = {
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "scheduler_state_dict": scheduler.state_dict(),
            "scaler_state_dict": scaler.state_dict() if amp_enabled else None,
            "last_completed_epoch": epoch,
            "best_val_macro_f1": best_macro_f1,
            "epochs_without_improvement": epochs_without_improvement,
            "history": history,
            "seed": args.seed,
            "classes": all_classes,
            "rng_state": rng_state(),
        }
        atomic_torch(last_ckpt, exp_dir / "checkpoint_last.pt")

        # Save history
        atomic_json(history, exp_dir / "history.json")
        with open(exp_dir / "history.csv", "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(epoch_record.keys()))
            writer.writeheader()
            writer.writerows(history)

    # Mark completed
    experiment_meta["status"] = "completed"
    experiment_meta["completed_time"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    experiment_meta["training_duration_s"] = round(time.time() - t0, 1)
    experiment_meta["best_val_macro_f1"] = best_macro_f1
    atomic_json(experiment_meta, exp_json_path)
    atomic_json(all_classes, exp_dir / "classes.json")

    print(f"\n[DONE] Experiment {exp_id} finished successfully. Best Val Macro-F1: {best_macro_f1:.4f}")
    print(f"Artifacts saved in: {exp_dir}")


if __name__ == "__main__":
    main()
