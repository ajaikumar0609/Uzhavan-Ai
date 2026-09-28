# Uzhavan M4 V2.3 Pre-Training Audit Report
**Document Type:** Pre-Training Diagnostic & Sampler Verification Audit  
**Date:** 2026-09-28  
**Status:** **AUDIT PASSED — READY FOR ACER ALPHA GPU EXECUTION**  
**Constraints Enforced:** No Training Executed | No Production Code Modified | Zero Dataset Leakage  

---

## 1. Executive Summary

This document certifies the pre-training implementation for **Uzhavan M4 V2.3** (`UZ-M4-v2.3-groundnut-s1-healthy-green-balance`). 

Following the definitive diagnostic discovery in the M4 V2.2 three-seed error audit—which proved that Healthy recall instability ($34.0\% \to 70.3\% \to 97.3\%$) was driven entirely by pure-green Healthy foliage being classified as Tikka Leaf Spot due to a $7.8:1$ training exposure starvation—V2.3 implements a targeted, deterministic oversampling sampler.

### Pre-Flight Sign-Off Summary:
- **Manifest Integrity:** `m4_v2/manifests/groundnut_v2.csv` SHA256 verified (`6768c740a0bc32ec45be08237c564e0be153a610caab9909196c1a0c123a4cfe`).
- **Pure-Green Healthy Identification:** Exactly **285 samples** identified ($100\%$ precision, $0$ false positives, $0$ false negatives).
- **Analytical Exposure Balancing:** Target Pure-Green Healthy to Tikka ratio is mathematically **$1.000000$** ($28.41\% : 28.41\%$).
- **Empirical Sampler Verification:** 10-epoch Monte Carlo simulation ($78,710$ draws) yielded **$0.9983$** draw ratio ($22,273$ Healthy vs $22,310$ Tikka).
- **Zero Leakage:** Exactly $0$ West Bengal external samples in the training split.
- **Unit Tests:** $6 / 6$ unit tests passed in `uzhavan_ml/tests/test_m4_v2_3_sampler.py`.
- **Pre-Flight Execution:** Completed successfully on both local Mac and remote Acer ALPHA GPU host.

---

## 2. Root Cause Justification & Architecture Parity

### Why Pure-Green Healthy Oversampling is Justified
In M4 V2.2:
- `groundnut__healthy_or_abiotic` contains 1,449 training samples.
- **1,164 samples ($80.3\%$)** are nutrient deficiency/chlorosis from `in_tn_multicrop_vitc`.
- **Only 285 samples ($19.7\%$)** are pristine green healthy leaves.
- Meanwhile, Tikka Leaf Spot has **2,236 samples** ($7.84\times$ pure green healthy).
- When evaluated against external field phone captures (`in_groundnut_wb_sasmal`, where all 600 healthy samples are pristine green leaves), the model has seen almost eight times more Tikka lesions than healthy foliage.
- In Seed 1337, the classification hyperplane shifted toward Tikka, misclassifying 396 healthy leaves ($66.0\%$) as Tikka with suppressed confidence ($0.50 - 0.73$).

### Strict Architectural Parity Table: V2.2 vs. V2.3

| Component | M4 V2.2 (Replication Baseline) | M4 V2.3 (Targeted Balancing) | Parity Status |
| :--- | :---: | :---: | :---: |
| **Backbone Architecture** | EfficientNetV2-S (`timm`/`torchvision`) | EfficientNetV2-S (`timm`/`torchvision`) | **IDENTICAL** |
| **Classification Heads** | Dedicated Linear per crop (dropout=0.2) | Dedicated Linear per crop (dropout=0.2) | **IDENTICAL** |
| **Taxonomy** | 3 classes (`healthy_or_abiotic`, `rust`, `tikka`) | 3 classes (`healthy_or_abiotic`, `rust`, `tikka`) | **IDENTICAL** |
| **Dataset Manifest** | `groundnut_v2.csv` (N=5,920 train) | `groundnut_v2.csv` (N=5,920 train) | **IDENTICAL** |
| **West Bengal Split** | Zero WB in train split | Zero WB in train split | **IDENTICAL** |
| **Field Augmentations** | Shadow sim (p=0.35) + Gaussian blur (p=0.2) | Shadow sim (p=0.35) + Gaussian blur (p=0.2) | **IDENTICAL** |
| **Loss Formulation** | Weighted Cross-Entropy (WCE) | Weighted Cross-Entropy (WCE) | **IDENTICAL** |
| **Rust Loss Weight Multiplier** | $1.0\times$ (balanced) | $1.0\times$ (balanced) | **IDENTICAL** |
| **Optimizer** | AdamW (lr=1e-4, weight_decay=1e-2) | AdamW (lr=1e-4, weight_decay=1e-2) | **IDENTICAL** |
| **Batch Size & Epochs** | 32 batch size, 15 epochs, AMP fp16 | 32 batch size, 15 epochs, AMP fp16 | **IDENTICAL** |
| **DataLoader Sampler** | Uniform Shuffling (`shuffle=True`) | **Deterministic Pure-Green Weighted Sampler** | **INTERVENTION** |

---

## 3. Mathematical Formulation of the V2.3 Sampler

Let $\mathcal{D}_{\text{train}}$ represent the $N=5,920$ groundnut training samples, partitioned into four mutually exclusive subsets:
1. $\mathcal{S}_{\text{tikka}}$ ($N_T = 2,236$): Tikka leaf spot images.
2. $\mathcal{S}_{\text{rust}}$ ($N_R = 2,235$): Rust pustule images.
3. $\mathcal{S}_{\text{nutrient}}$ ($N_N = 1,164$): Abiotic nutrient-deficient/chlorotic leaves.
4. $\mathcal{S}_{\text{green}}$ ($N_G = 285$): Pristine green healthy foliage.

### Sample Weight Assignment
To achieve a target expected exposure ratio of $1.000$ between pure-green Healthy and Tikka:
$$\sum_{i \in \mathcal{S}_{\text{green}}} w_i = \sum_{j \in \mathcal{S}_{\text{tikka}}} w_j$$

Setting base weights $w_j = 1.0$ for all samples in $\mathcal{S}_{\text{tikka}}, \mathcal{S}_{\text{rust}}, \mathcal{S}_{\text{nutrient}}$:
$$N_G \cdot w_{\text{green}} = N_T \cdot 1.0 \implies w_{\text{green}} = \frac{N_T}{N_G} = \frac{2236}{285} \approx \mathbf{7.845614}$$

### Total Weight Sum & Draw Probabilities
$$\Omega = \sum_{i=1}^{5920} w_i = (285 \times 7.845614) + (2236 \times 1.0) + (2235 \times 1.0) + (1164 \times 1.0) = \mathbf{7,871.0}$$

In any mini-batch drawn with replacement:
$$P(\text{draw } \mathcal{S}_{\text{green}}) = \frac{285 \times 7.845614}{7871.0} = \frac{2236.0}{7871.0} = \mathbf{28.408\%}$$
$$P(\text{draw } \mathcal{S}_{\text{tikka}}) = \frac{2236 \times 1.0}{7871.0} = \frac{2236.0}{7871.0} = \mathbf{28.408\%}$$
$$P(\text{draw } \mathcal{S}_{\text{rust}}) = \frac{2235 \times 1.0}{7871.0} = \mathbf{28.395\%}$$
$$P(\text{draw } \mathcal{S}_{\text{nutrient}}) = \frac{1164 \times 1.0}{7871.0} = \mathbf{14.788\%}$$

$$\mathbf{\text{Effective Exposure Ratio }} \left(\frac{P(\mathcal{S}_{\text{green}})}{P(\mathcal{S}_{\text{tikka}})}\right) = \frac{28.408\%}{28.408\%} = \mathbf{1.000000}$$

---

## 4. Empirical Verification & Unit Test Audit

Unit tests located in `uzhavan_ml/tests/test_m4_v2_3_sampler.py` were executed across 6 test suites:

```
[TEST 01] test_01_pure_green_identification: PASS (Identified exactly 285 samples)
[TEST 02] test_02_pure_green_exclusivity:    PASS (0 overlap with nutrient def., Tikka, or Rust)
[TEST 03] test_03_sample_weights_calc:       PASS (w_green = 7.845614, sum = 7871.0)
[TEST 04] test_04_empirical_sampling_ratio:  PASS (10-epoch draws: 22,273 green, 22,310 Tikka, ratio = 0.9983)
[TEST 05] test_05_sampler_determinism:       PASS (Identical seed produces 100% identical sequence)
[TEST 06] test_06_zero_external_leakage:     PASS (0 overlapping SHAs between train and external test)
----------------------------------------------------------------------
Ran 6 tests in 0.059s (Mac CPU) / 0.189s (Acer GPU) | OK
```

---

## 5. Pre-Flight Verification Sign-Off

The pre-flight script `uzhavan_ml/scripts/preflight_m4_v2_3.py` completed verification with exit code 0:
- **Host Checked:** Acer ALPHA (NVIDIA GeForce RTX 4050 Laptop GPU, 6GB VRAM, CUDA 12.6)
- **Manifest Integrity Check:** Passed (`groundnut_v2.csv` SHA256 verified)
- **Class Counts Verified:** Exactly 2,236 Tikka, 2,235 Rust, 1,449 Healthy/Abiotic
- **Sub-Class Counts Verified:** Exactly 285 Pure-Green Healthy, 1,164 Nutrient Deficiency
- **Contamination Check:** Passed (0 West Bengal images in train split)
- **Status:** **ALL SYSTEMS GO FOR SEED 42 TRAINING UPON ACER GPU AVAILABILITY**

---
*Report generated autonomously by Uzhavan ML V2.3 Pre-Training Engine.*
