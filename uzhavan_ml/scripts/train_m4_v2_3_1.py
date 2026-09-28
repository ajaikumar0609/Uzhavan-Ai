"""UZHAVAN AI - M4 V2.3.1 Groundnut Disease Model Training Script.
NO TRAINING - SCRIPT PREPARATION FOR ACER ALPHA GPU HOST ONLY.

Implements M4 V2.3.1: Tri-Class Boundary Balance.
- Pure-green Healthy oversampling moderated to 1:2 (~0.50) relative to Tikka (w_green = 1118/285 ≈ 3.9228).
- Asymmetric Rust WCE loss weight multiplier = 1.25x.
- Strictly identical architecture, optimizer, LR, augmentations, and hyperparameters as V2.2/V2.3.
"""

import argparse
import hashlib
import json
import math
import os
import random
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
import torchvision
import torchvision.transforms as T

sys.path.insert(0, "scripts")
import v2_3_1_sampler as v231s

IMNET_MEAN = [0.485, 0.456, 0.406]
IMNET_STD = [0.229, 0.224, 0.225]
EXPECTED_MANIFEST_SHA = "6768c740a0bc32ec45be08237c564e0be153a610caab9909196c1a0c123a4cfe"

AUG_CONFIG = {
    "resize": [256, 256],
    "crop_size": 224,
    "scale_range": [0.6, 1.0],
    "ratio_range": [0.8, 1.25],
    "hflip_prob": 0.5,
    "rotation_degrees": 20,
    "color_jitter": {
        "brightness": 0.2,
        "contrast": 0.2,
        "saturation": 0.2,
        "hue": 0.05
    },
    "gaussian_blur": {
        "prob": 0.20,
        "kernel_size": [3, 5],
        "sigma": [0.1, 1.5]
    },
    "shadow_simulation": {
        "prob": 0.35,
        "darkening_range": [0.35, 0.65],
        "area_range": [0.05, 0.35]
    },
    "rust_loss_weight_multiplier": 1.25
}


def seed_all(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


class SimulateFieldShadow:
    def __init__(self, p=0.35, darkening_range=(0.35, 0.65), area_range=(0.05, 0.35)):
        self.p = p
        self.darkening_range = darkening_range
        self.area_range = area_range

    def __call__(self, img: Image.Image) -> Image.Image:
        if random.random() > self.p:
            return img
        arr = np.array(img, dtype=np.float32)
        h, w, _ = arr.shape
        area = h * w * random.uniform(*self.area_range)
        aspect = random.uniform(0.5, 2.0)
        box_w = int(np.clip(np.sqrt(area * aspect), 10, w))
        box_h = int(np.clip(area / max(1, box_w), 10, h))
        x1 = random.randint(0, max(0, w - box_w))
        y1 = random.randint(0, max(0, h - box_h))
        darkening = random.uniform(*self.darkening_range)
        arr[y1:y1 + box_h, x1:x1 + box_w] *= darkening
        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


class M4V2_3_1_Dataset(Dataset):
    def __init__(self, df: pd.DataFrame, img_root: Path, class_list: list, is_train: bool, aug_cfg: dict = None):
        self.df = df.reset_index(drop=True)
        self.img_root = Path(img_root)
        self.class_to_idx = {c: i for i, c in enumerate(class_list)}
        cfg = aug_cfg or AUG_CONFIG

        if is_train:
            self.transform = T.Compose([
                T.Resize(cfg["resize"]),
                T.RandomResizedCrop(cfg["crop_size"], scale=tuple(cfg["scale_range"]), ratio=tuple(cfg["ratio_range"])),
                T.RandomHorizontalFlip(p=cfg["hflip_prob"]),
                T.RandomRotation(degrees=cfg["rotation_degrees"]),
                T.ColorJitter(
                    brightness=cfg["color_jitter"]["brightness"],
                    contrast=cfg["color_jitter"]["contrast"],
                    saturation=cfg["color_jitter"]["saturation"],
                    hue=cfg["color_jitter"]["hue"]
                ),
                SimulateFieldShadow(
                    p=cfg["shadow_simulation"]["prob"],
                    darkening_range=tuple(cfg["shadow_simulation"]["darkening_range"]),
                    area_range=tuple(cfg["shadow_simulation"]["area_range"])
                ),
                T.RandomApply([
                    T.GaussianBlur(
                        kernel_size=tuple(cfg["gaussian_blur"]["kernel_size"]),
                        sigma=tuple(cfg["gaussian_blur"]["sigma"])
                    )
                ], p=cfg["gaussian_blur"]["prob"]),
                T.ToTensor(),
                T.Normalize(mean=IMNET_MEAN, std=IMNET_STD),
            ])
        else:
            self.transform = T.Compose([
                T.Resize(cfg["resize"]),
                T.CenterCrop(cfg["crop_size"]),
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


class M4V2_3_1_Model(nn.Module):
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


def main():
    parser = argparse.ArgumentParser(description="Uzhavan M4 V2.3.1 Training Engine (Tri-Class Boundary Balance)")
    parser.add_argument("--pkg", type=str, default="m4_v1", help="Path to raw image package")
    parser.add_argument("--manifest", type=str, default="m4_v2/manifests/groundnut_v2.csv", help="Path to manifest")
    parser.add_argument("--classes", type=str, default="m4_v2/classes.json", help="Path to classes JSON")
    parser.add_argument("--out", type=str, default="runs_m4_v2_3_1", help="Output directory for runs")
    parser.add_argument("--exp-name", type=str, default="UZ-M4-v2.3.1-groundnut-s1-triclass-balance", help="Experiment name")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (Seed 42 ONLY)")
    parser.add_argument("--epochs", type=int, default=15, help="Number of training epochs")
    parser.add_argument("--bs", type=int, default=32, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate")
    parser.add_argument("--weight-decay", type=float, default=1e-2, help="AdamW weight decay")
    parser.add_argument("--workers", type=int, default=0, help="DataLoader workers (0 for Windows compatibility)")
    parser.add_argument("--resume", type=str, default="auto", choices=["auto", "none"], help="Resume policy")
    parser.add_argument("--smoke-test", action="store_true", help="Quick smoke test verification")
    parser.add_argument("--loss", type=str, default="wce", choices=["wce"], help="Loss formulation (Weighted Cross-Entropy)")
    parser.add_argument("--rust-weight-mult", type=float, default=1.25, help="Rust loss weight multiplier (1.25x for V2.3.1)")
    parser.add_argument("--target-ratio", type=float, default=0.5, help="Pure-green to Tikka exposure ratio (0.5 = 1:2)")
    parser.add_argument("--sampler-policy", type=str, default="dataset_size", choices=["dataset_size", "balanced"], help="Sampler epoch samples policy")

    args = parser.parse_args()

    print("=" * 75)
    print("  UZHAVAN M4 V2.3.1 TRAINING ENGINE: TRI-CLASS BOUNDARY BALANCE")
    print("  Intervention: 1:2 Green Oversampling + 1.25x Rust WCE Loss Protection")
    print("=" * 75)

    seed_all(args.seed)

    # 1. Environment & Pre-checks
    cuda_avail = torch.cuda.is_available()
    dev = torch.device("cuda" if cuda_avail else "cpu")
    if not cuda_avail and not args.smoke_test:
        raise RuntimeError("FATAL: CUDA is not available! Full training must run on Acer ALPHA GPU host.")

    manifest_path = Path(args.manifest)
    classes_path = Path(args.classes)
    pkg_path = Path(args.pkg)
    out_dir_root = Path(args.out)

    actual_sha = compute_sha256(manifest_path)
    if actual_sha != EXPECTED_MANIFEST_SHA:
        raise ValueError(f"Manifest SHA256 mismatch! Expected {EXPECTED_MANIFEST_SHA}, got {actual_sha}")
    print(f"[OK] Manifest SHA256 verified: {actual_sha}")

    with open(classes_path) as f:
        classes = json.load(f)
    crop_classes = classes["groundnut"]
    num_classes = len(crop_classes)
    assert crop_classes == ["groundnut__healthy_or_abiotic", "groundnut__rust", "groundnut__tikka_leaf_spot"]

    df = pd.read_csv(manifest_path)
    gn_df = df[df.crop == "groundnut"].copy().reset_index(drop=True)
    train_df = gn_df[gn_df.split == "train"].copy().reset_index(drop=True)
    val_df = gn_df[gn_df.split == "val"].copy().reset_index(drop=True)

    # Zero West Bengal check
    train_sources = train_df["source"].unique().tolist()
    if "in_groundnut_wb_sasmal" in train_sources:
        raise ValueError("FATAL: External West Bengal samples found in training split!")
    print("[OK] Zero external West Bengal samples in training split.")

    # 2. Targeted Sampler Initialization (1:2 exposure)
    print(f"\nInitializing Targeted Tri-Class Boundary Balancing Sampler (Target Ratio: {args.target_ratio})...")
    train_sampler, sample_weights, sampler_stats = v231s.build_v2_3_1_training_sampler(
        train_df, seed=args.seed, policy=args.sampler_policy, target_ratio=args.target_ratio
    )
    print(f"[OK] Pure-green healthy count : {sampler_stats['n_green']} / 1,449 healthy ({sampler_stats['n_green']/1449*100:.2f}%)")
    print(f"[OK] Tikka leaf spot count    : {sampler_stats['n_tikka']}")
    print(f"[OK] Sampler weight multiplier: w_green = {sampler_stats['w_green']:.6f}")
    print(f"[OK] Batch draw probability   : Green={sampler_stats['prob_green']*100:.2f}%, Tikka={sampler_stats['prob_tikka']*100:.2f}% (Ratio: {sampler_stats['exposure_ratio_green_to_tikka']:.6f})")
    print(f"[OK] Num samples per epoch    : {sampler_stats['num_samples_per_epoch']} (Policy: {args.sampler_policy})")

    # 3. Class Weights for WCE (with 1.25x Rust Multiplier)
    cls_counts = [int((train_df.canonical_id == c).sum()) for c in crop_classes]
    total_samples = len(train_df)
    raw_weights = [total_samples / (num_classes * max(cnt, 1)) for cnt in cls_counts]
    rust_idx = crop_classes.index("groundnut__rust")
    raw_weights[rust_idx] = raw_weights[rust_idx] * args.rust_weight_mult
    mean_w = sum(raw_weights) / len(raw_weights)
    norm_weights = [w / mean_w for w in raw_weights]
    weight_tensor = torch.tensor(norm_weights, dtype=torch.float32, device=dev)
    print(f"[OK] Loss formulation: WCE with normalized weights (Rust 1.25x): {dict(zip(crop_classes, [round(w, 4) for w in norm_weights]))}")

    # Output directory & Collision protection
    exp_id = args.exp_name + ("-SMOKE" if args.smoke_test else "")
    exp_dir = out_dir_root / exp_id
    exp_dir.mkdir(parents=True, exist_ok=True)
    exp_json_path = exp_dir / "experiment.json"
    ckpt_best_path = exp_dir / "checkpoint_best.pt"
    ckpt_last_path = exp_dir / "checkpoint_last.pt"

    if exp_json_path.exists() and not args.smoke_test:
        with open(exp_json_path) as f:
            prev = json.load(f)
        if prev.get("status") == "completed" and args.resume == "none":
            print(f"[COLLISION PROTECTION] Experiment {exp_id} is already COMPLETED. Refusing overwrite.")
            sys.exit(0)

    # Subsample if smoke test
    if args.smoke_test:
        train_df = train_df.groupby("canonical_id").head(8).reset_index(drop=True)
        val_df = val_df.groupby("canonical_id").head(4).reset_index(drop=True)
        epochs = 1
        num_workers = 0
        train_sampler = None
    else:
        epochs = args.epochs
        num_workers = args.workers

    train_ds = M4V2_3_1_Dataset(train_df, pkg_path, crop_classes, is_train=True, aug_cfg=AUG_CONFIG)
    val_ds = M4V2_3_1_Dataset(val_df, pkg_path, crop_classes, is_train=False, aug_cfg=AUG_CONFIG)

    train_loader = DataLoader(
        train_ds,
        batch_size=args.bs,
        sampler=train_sampler if train_sampler is not None else None,
        shuffle=(train_sampler is None),
        num_workers=num_workers,
        pin_memory=cuda_avail
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=args.bs,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=cuda_avail
    )

    # 4. Model & Optimizer
    model = M4V2_3_1_Model(classes, dropout=0.2).to(dev)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    scaler = torch.amp.GradScaler("cuda", enabled=cuda_avail)
    criterion = nn.CrossEntropyLoss(weight=weight_tensor)

    start_epoch = 0
    best_val_macro_f1 = 0.0
    history = []

    # Resume handling
    if args.resume == "auto" and ckpt_last_path.exists():
        print(f"\n[RESUME] Loading last checkpoint from {ckpt_last_path}...")
        ck = torch.load(ckpt_last_path, map_location="cpu", weights_only=False)
        model.load_state_dict(ck["model"])
        optimizer.load_state_dict(ck["optimizer"])
        if "scaler" in ck and cuda_avail:
            scaler.load_state_dict(ck["scaler"])
        start_epoch = ck["epoch"] + 1
        best_val_macro_f1 = ck.get("best_val_macro_f1", 0.0)
        history = ck.get("history", [])
        print(f"[RESUME] Resuming from epoch {start_epoch} (Best Val Macro-F1: {best_val_macro_f1:.4f})")

    # 5. Training Loop
    print(f"\n>>> Starting Training {exp_id} ({epochs} epochs, bs={args.bs}, seed={args.seed}) <<<")
    total_start_time = time.time()

    for epoch in range(start_epoch, epochs):
        epoch_start = time.time()
        model.train()
        running_loss = 0.0
        num_batches = 0

        for x, y in train_loader:
            x, y = x.to(dev), y.to(dev)
            optimizer.zero_grad(set_to_none=True)

            with torch.amp.autocast("cuda", enabled=cuda_avail):
                logits = model(x, "groundnut")
                loss = criterion(logits, y)

            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()

            running_loss += loss.item()
            num_batches += 1

        avg_train_loss = running_loss / max(num_batches, 1)

        # Validation evaluation
        val_res = evaluate_split(model, val_loader, dev, "groundnut", num_classes)
        val_loss = val_res["loss"]
        val_acc = val_res["accuracy"]
        val_f1 = val_res["macro_f1"]
        per_class_f1 = val_res["per_class_f1"]

        is_best = val_f1 > best_val_macro_f1
        if is_best:
            best_val_macro_f1 = val_f1

        ep_duration = time.time() - epoch_start
        print(f"Epoch {epoch:2d}/{epochs-1:2d} | Train Loss: {avg_train_loss:.4f} | Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.4f} | Val F1: {val_f1:.4f} | Best: {best_val_macro_f1:.4f} {'[BEST]' if is_best else ''} ({ep_duration:.1f}s)")

        ep_record = {
            "epoch": epoch,
            "train_loss": round(avg_train_loss, 4),
            "val_loss": round(val_loss, 4),
            "val_accuracy": round(val_acc, 4),
            "val_macro_f1": round(val_f1, 4),
            "val_per_class_f1": [round(f, 4) for f in per_class_f1],
            "lr": args.lr,
            "epoch_duration_s": round(ep_duration, 1),
            "time_elapsed_s": round(time.time() - total_start_time, 1),
        }
        history.append(ep_record)

        # Save checkpoint_last.pt
        last_state = {
            "epoch": epoch,
            "model": model.state_dict(),
            "optimizer": optimizer.state_dict(),
            "scaler": scaler.state_dict() if cuda_avail else None,
            "best_val_macro_f1": best_val_macro_f1,
            "history": history,
            "classes": classes,
            "args": vars(args),
            "sampler_stats": sampler_stats,
        }
        torch.save(last_state, ckpt_last_path)

        if is_best:
            torch.save(last_state, ckpt_best_path)

    # 6. Finalization
    total_time = time.time() - total_start_time
    print(f"\n[COMPLETED] Training finished in {total_time/60:.2f} minutes. Best Val Macro-F1: {best_val_macro_f1:.4f}")

    # Write history files
    with open(exp_dir / "history.json", "w") as f:
        json.dump(history, f, indent=2)

    df_hist = pd.DataFrame(history)
    df_hist.to_csv(exp_dir / "history.csv", index=False)

    exp_meta = {
        "experiment_id": exp_id,
        "status": "completed",
        "timestamp_completed": time.strftime("%Y-%m-%d %H:%M:%S"),
        "best_val_macro_f1": round(best_val_macro_f1, 4),
        "total_epochs": epochs,
        "total_time_seconds": round(total_time, 1),
        "sampler": sampler_stats,
        "args": vars(args),
    }
    with open(exp_json_path, "w") as f:
        json.dump(exp_meta, f, indent=2)

    print(f"[SUCCESS] Artifacts written to {exp_dir}")


if __name__ == "__main__":
    main()
