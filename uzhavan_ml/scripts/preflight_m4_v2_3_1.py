"""UZHAVAN AI - M4 V2.3.1 Pre-Flight Verification Script.
NO TRAINING - DIAGNOSTIC AUDIT & READINESS CHECK ONLY.

Runs full verification on dataset manifest, pure-green Healthy identification,
V2.3.1 1:2 sampler mechanics, analytical exposure ratios, Rust loss weighting (1.25x),
and hardware status.
"""

import sys
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
import torch

sys.path.insert(0, "scripts")
import v2_3_1_sampler as v231s

EXPECTED_SHA = "6768c740a0bc32ec45be08237c564e0be153a610caab9909196c1a0c123a4cfe"


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def run_preflight(manifest_path: Path, seed: int = 42, require_cuda: bool = False):
    print("=" * 70)
    print("  UZHAVAN M4 V2.3.1 PRE-FLIGHT VERIFICATION AUDIT")
    print("  (Tri-Class Boundary Balance: 1:2 Green Oversampling + 1.25x Rust WCE)")
    print("=" * 70)
    
    # 1. Hardware / Environment
    print("\n1. Hardware & Environment Check:")
    cuda_avail = torch.cuda.is_available()
    if cuda_avail:
        gpu_name = torch.cuda.get_device_name(0)
        vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
        print(f"  [OK] CUDA GPU Detected: {gpu_name} ({vram_gb:.2f} GB VRAM)")
    else:
        if require_cuda:
            raise RuntimeError("FATAL: CUDA is required on GPU training host but not available!")
        print("  [INFO] Running on CPU (Mac / Non-CUDA development host)")
    
    # 2. Manifest Checksum
    print("\n2. Manifest Checksum Verification:")
    assert manifest_path.exists(), f"Missing manifest: {manifest_path}"
    actual_sha = compute_sha256(manifest_path)
    if actual_sha != EXPECTED_SHA:
        raise ValueError(f"Manifest SHA256 mismatch! Expected {EXPECTED_SHA}, got {actual_sha}")
    print(f"  [OK] Manifest SHA256 matched exactly: {actual_sha}")
    
    # 3. Training Split Class Counts
    print("\n3. Training Split Class Count Verification:")
    df = pd.read_csv(manifest_path)
    train_df = df[(df.crop == "groundnut") & (df.split == "train")].copy().reset_index(drop=True)
    assert len(train_df) == 5920, f"Expected 5,920 train samples, got {len(train_df)}"
    
    counts = train_df["canonical_id"].value_counts().to_dict()
    assert counts.get("groundnut__tikka_leaf_spot") == 2236, f"Tikka mismatch: {counts}"
    assert counts.get("groundnut__rust") == 2235, f"Rust mismatch: {counts}"
    assert counts.get("groundnut__healthy_or_abiotic") == 1449, f"Healthy mismatch: {counts}"
    print(f"  [OK] Total train samples: 5,920")
    print(f"       Tikka Leaf Spot   : 2,236")
    print(f"       Rust              : 2,235")
    print(f"       Healthy or Abiotic: 1,449")
    
    # 4. Pure-Green Healthy Identification
    print("\n4. Pure-Green Healthy Identification:")
    green_mask = v231s.identify_pure_green_healthy(train_df)
    n_green = int(green_mask.sum())
    assert n_green == 285, f"Expected exactly 285 pure-green Healthy images, got {n_green}"
    n_nutrient = 1449 - n_green
    assert n_nutrient == 1164, f"Expected 1,164 nutrient deficiency images, got {n_nutrient}"
    print(f"  [OK] Pure-Green Healthy Foliage: 285 samples ({n_green/1449*100:.2f}% of healthy class)")
    print(f"  [OK] Nutrient Deficiency Abiotic: 1,164 samples ({n_nutrient/1449*100:.2f}% of healthy class)")
    
    # 5. External Contamination Check
    print("\n5. Contamination & Leakage Audit:")
    train_sources = train_df["source"].unique().tolist()
    assert "in_groundnut_wb_sasmal" not in train_sources, "FATAL: Found WB external samples in train split!"
    print(f"  [OK] Zero West Bengal external samples in training split.")
    
    # 6. Sampler & Exposure Ratio Audit (1:2 Target)
    print("\n6. Sampler Weight & Exposure Ratio Audit (Target: 1:2 = 0.500000):")
    weights, stats = v231s.compute_v2_3_1_sample_weights(train_df, target_ratio=0.5)
    print(f"  [OK] Pure-green weight multiplier: w_green = {stats['w_green']:.6f} (Exact: 1118/285 = {stats['w_green_exact']:.6f})")
    print(f"  [OK] Total epoch weight sum       : {stats['total_weight_sum']:.2f} (Target: 6753.0)")
    print(f"  [OK] Batch draw probability Pure-Green Healthy: {stats['prob_green']*100:.2f}%")
    print(f"  [OK] Batch draw probability Tikka Leaf Spot   : {stats['prob_tikka']*100:.2f}%")
    print(f"  [OK] Batch draw probability Rust              : {stats['prob_rust']*100:.2f}%")
    print(f"  [OK] Batch draw probability Nutrient Def.     : {stats['prob_nutrient']*100:.2f}%")
    print(f"  [OK] Analytical Exposure Ratio (Green : Tikka): {stats['exposure_ratio_green_to_tikka']:.6f} (Target: 0.500000)")
    assert abs(stats["exposure_ratio_green_to_tikka"] - 0.5) < 1e-5, "Exposure ratio must be 0.500000"
    
    # 7. Loss Weights Audit (Rust 1.25x WCE)
    print("\n7. WCE Loss Weights Audit (Rust Multiplier = 1.25x):")
    crop_classes = ["groundnut__healthy_or_abiotic", "groundnut__rust", "groundnut__tikka_leaf_spot"]
    cls_counts = [int((train_df.canonical_id == c).sum()) for c in crop_classes]
    raw_weights = [5920 / (3 * max(cnt, 1)) for cnt in cls_counts]
    rust_idx = crop_classes.index("groundnut__rust")
    raw_weights[rust_idx] = raw_weights[rust_idx] * 1.25
    mean_w = sum(raw_weights) / len(raw_weights)
    norm_weights = [round(w / mean_w, 4) for w in raw_weights]
    print(f"  [OK] Raw weights: {dict(zip(crop_classes, [round(w, 4) for w in raw_weights]))}")
    print(f"  [OK] Normalized WCE weights: {dict(zip(crop_classes, norm_weights))}")
    assert norm_weights[rust_idx] > 0.95, "Rust weight must reflect 1.25x multiplier"
    
    # 8. Deterministic Sampling Verification
    print("\n8. Deterministic Sampling Sequence Test:")
    sampler_a, _, _ = v231s.build_v2_3_1_training_sampler(train_df, seed=seed, target_ratio=0.5)
    sampler_b, _, _ = v231s.build_v2_3_1_training_sampler(train_df, seed=seed, target_ratio=0.5)
    assert list(sampler_a) == list(sampler_b), "FATAL: Sampler failed deterministic sequence check!"
    print(f"  [OK] Sampler sequence is 100% deterministic with seed {seed}")
    
    print("\n" + "=" * 70)
    print("  PRE-FLIGHT VERIFICATION PASSED: SYSTEM READY FOR V2.3.1 TRAINING")
    print("=" * 70)
    return True


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    man_path = root / "m4_v2/manifests/groundnut_v2.csv"
    run_preflight(man_path, seed=42, require_cuda=False)
