"""UZHAVAN AI - M4 V2.3.1 Targeted Tri-Class Boundary Balancing Sampler.
NO TRAINING - DATA PIPELINE & SAMPLER MODULE.

Implements the deterministic targeted oversampling of the 285 pure-green Healthy
training samples to achieve exactly 1:2 (~0.50) effective exposure relative to the 2,236 Tikka samples.
"""

from typing import Dict, Tuple, Any
import numpy as np
import pandas as pd
import torch
from torch.utils.data import WeightedRandomSampler


def identify_pure_green_healthy(df: pd.DataFrame) -> pd.Series:
    """Identify the 285 pure-green healthy groundnut samples.
    
    In groundnut_v2.csv, the training samples for groundnut__healthy_or_abiotic
    are composed of:
    1. groundnut__nutrient_deficiency (1,164 samples - chlorotic/necrotic abiotic stress)
    2. groundnut__healthy (285 samples - pristine green foliage)
    
    Both v1_canonical_id == 'groundnut__healthy' and original_label == 'groundnut_healthy'
    uniquely and unambiguously isolate these 285 samples.
    """
    is_healthy_abiotic = (df["canonical_id"] == "groundnut__healthy_or_abiotic")
    is_green_v1 = (df["v1_canonical_id"] == "groundnut__healthy")
    is_green_orig = (df["original_label"] == "groundnut_healthy")
    
    mask = is_healthy_abiotic & (is_green_v1 | is_green_orig)
    return mask


def compute_v2_3_1_sample_weights(
    train_df: pd.DataFrame,
    target_ratio: float = 0.5
) -> Tuple[torch.Tensor, Dict[str, Any]]:
    """Compute exact sample weights for the V2.3.1 targeted 1:2 oversampler.
    
    Args:
        train_df: Groundnut training split DataFrame (N=5,920).
        target_ratio: Desired exposure ratio of pure-green Healthy to Tikka (default 0.5 = 1:2).
        
    Returns:
        weights_tensor: 1D torch.Tensor of shape (len(train_df),)
        stats: Dictionary containing analytical exposure percentages and sample counts.
    """
    # 1. Masks for sub-classes
    green_mask = identify_pure_green_healthy(train_df).to_numpy()
    tikka_mask = (train_df["canonical_id"] == "groundnut__tikka_leaf_spot").to_numpy()
    rust_mask = (train_df["canonical_id"] == "groundnut__rust").to_numpy()
    nutrient_mask = ((train_df["canonical_id"] == "groundnut__healthy_or_abiotic") & (~green_mask)).to_numpy()
    
    n_green = int(green_mask.sum())
    n_tikka = int(tikka_mask.sum())
    n_rust = int(rust_mask.sum())
    n_nutrient = int(nutrient_mask.sum())
    n_total = len(train_df)
    
    # Assert expected counts on training split
    if n_total == 5920:
        assert n_green == 285, f"Expected 285 pure-green healthy samples, got {n_green}"
        assert n_tikka == 2236, f"Expected 2,236 Tikka samples, got {n_tikka}"
        assert n_rust == 2235, f"Expected 2,235 Rust samples, got {n_rust}"
        assert n_nutrient == 1164, f"Expected 1,164 nutrient deficiency samples, got {n_nutrient}"
    
    # 2. Weight multiplier calculation:
    # total_weight(green) = target_ratio * total_weight(tikka)
    # n_green * w_green = target_ratio * n_tikka * 1.0  =>  w_green = (target_ratio * n_tikka) / n_green
    w_green = float((target_ratio * n_tikka) / max(1, n_green))
    
    weights = np.ones(n_total, dtype=np.float32)
    weights[green_mask] = w_green
    
    total_weight = float(np.sum(weights))
    
    prob_green = float((n_green * w_green) / total_weight)
    prob_tikka = float((n_tikka * 1.0) / total_weight)
    prob_rust = float((n_rust * 1.0) / total_weight)
    prob_nutrient = float((n_nutrient * 1.0) / total_weight)
    
    exposure_ratio_green_to_tikka = float(prob_green / prob_tikka) if prob_tikka > 0 else 0.0
    
    stats = {
        "n_total": n_total,
        "n_green": n_green,
        "n_tikka": n_tikka,
        "n_rust": n_rust,
        "n_nutrient": n_nutrient,
        "target_ratio": target_ratio,
        "w_green": round(w_green, 6),
        "w_green_exact": w_green,
        "total_weight_sum": round(total_weight, 2),
        "prob_green": round(prob_green, 6),
        "prob_tikka": round(prob_tikka, 6),
        "prob_rust": round(prob_rust, 6),
        "prob_nutrient": round(prob_nutrient, 6),
        "exposure_ratio_green_to_tikka": round(exposure_ratio_green_to_tikka, 6),
    }
    
    return torch.tensor(weights, dtype=torch.float32), stats


def build_v2_3_1_training_sampler(
    train_df: pd.DataFrame,
    seed: int = 42,
    policy: str = "dataset_size",
    target_ratio: float = 0.5
) -> Tuple[WeightedRandomSampler, torch.Tensor, Dict[str, Any]]:
    """Build a deterministic WeightedRandomSampler for V2.3.1.
    
    Args:
        train_df: Groundnut training split DataFrame.
        seed: Random seed for exact determinism.
        policy: 'dataset_size' sets num_samples = len(train_df) (5,920).
                'balanced' sets num_samples = int(total_weight_sum) (6,753).
        target_ratio: Target green-to-tikka exposure ratio (default 0.5 = 1:2).
    """
    weights, stats = compute_v2_3_1_sample_weights(train_df, target_ratio=target_ratio)
    
    if policy == "balanced":
        num_samples = int(round(stats["total_weight_sum"]))
    else:  # 'dataset_size'
        num_samples = len(train_df)
    
    gen = torch.Generator()
    gen.manual_seed(seed)
    
    sampler = WeightedRandomSampler(
        weights=weights,
        num_samples=num_samples,
        replacement=True,
        generator=gen
    )
    
    stats["num_samples_per_epoch"] = num_samples
    stats["policy"] = policy
    stats["seed"] = seed
    
    return sampler, weights, stats
