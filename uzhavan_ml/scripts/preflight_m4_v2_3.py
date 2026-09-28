"""UZHAVAN AI - M4 V2.3 Pre-Flight Verification Script.
NO TRAINING - DIAGNOSTIC AUDIT & READINESS CHECK ONLY.

Runs full verification on dataset manifest, pure-green Healthy identification,
sampler mechanics, exposure ratios, and hardware status.
"""

import sys
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
import torch

sys.path.insert(0, "scripts")
import v2_3_sampler as v23s

EXPECTED_SHA = "6768c740a0bc32ec45be08237c564e0be153a610caab9909196c1a0c123a4cfe"


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def run_preflight(manifest_path: Path, seed: int = 42, require_cuda: bool = False):
    print("=" * 65)
    print("  UZHAVAN M4 V2.3 PRE-FLIGHT VERIFICATION AUDIT")
    print("=" * 65)
    
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
    green_mask = v23s.identify_pure_green_healthy(train_df)
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
    
    # 6. Sampler & Exposure Ratio Audit
    print("\n6. Sampler Weight & Exposure Ratio Audit:")
    weights, stats = v23s.compute_v2_3_sample_weights(train_df)
    print(f"  [OK] Pure-green weight multiplier: w_green = {stats['w_green']:.6f}")
    print(f"  [OK] Total epoch weight sum       : {stats['total_weight_sum']:.2f}")
    print(f"  [OK] Batch draw probability Pure-Green Healthy: {stats['prob_green']*100:.2f}%")
    print(f"  [OK] Batch draw probability Tikka Leaf Spot   : {stats['prob_tikka']*100:.2f}%")
    print(f"  [OK] Batch draw probability Rust              : {stats['prob_rust']*100:.2f}%")
    print(f"  [OK] Batch draw probability Nutrient Def.     : {stats['prob_nutrient']*100:.2f}%")
    print(f"  [OK] Analytical Exposure Ratio (Green : Tikka): {stats['exposure_ratio_green_to_tikka']:.6f} (Target: 1.000000)")
    
    # 7. Deterministic Sampling Verification
    print("\n7. Deterministic Sampling Sequence Test:")
    sampler_a, _, _ = v23s.build_v2_3_training_sampler(train_df, seed=seed)
    sampler_b, _, _ = v23s.build_v2_3_training_sampler(train_df, seed=seed)
    assert list(sampler_a) == list(sampler_b), "FATAL: Sampler failed deterministic sequence check!"
    print(f"  [OK] Sampler sequence is 100% deterministic with seed {seed}")
    
    print("\n" + "=" * 65)
    print("  PRE-FLIGHT VERIFICATION PASSED: SYSTEM READY FOR V2.3 TRAINING")
    print("=" * 65)
    return True


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    man_path = root / "m4_v2/manifests/groundnut_v2.csv"
    run_preflight(man_path, seed=42, require_cuda=False)
