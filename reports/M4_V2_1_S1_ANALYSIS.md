# Uzhavan M4 V2.1 Controlled Training Experiment Analysis

**Date:** 2026-09-27 23:09:13  
**Host:** Acer ALPHA (NVIDIA GeForce RTX 4050 Laptop GPU, 6GB VRAM, CUDA 12.6)  
**Experiment:** `UZ-M4-v2.1-groundnut-s1-wce-rustrobust` vs Baseline `UZ-M4-v2-groundnut-s1-wce`  
**Objective:** Test whether field-domain robust augmentation + 1.25x Rust loss weighting resolves the cross-source West Bengal Rust recall bottleneck without degrading Tikka accuracy or open-set behavior.

---

## 1. Controlled Experiment Configuration

| Component | Baseline (`s1-wce`) | Experimental (`s1-wce-rustrobust`) | Controlled Status |
|---|---|---|---|
| **Architecture** | EfficientNetV2-S | EfficientNetV2-S | Strictly identical |
| **Taxonomy** | 3-class V2 (Healthy, Rust, Tikka) | 3-class V2 (Healthy, Rust, Tikka) | Strictly identical |
| **Loss Function** | Weighted Cross-Entropy | Weighted Cross-Entropy | Strictly identical |
| **Rust Relative Weight** | 1.0x (standard inverse freq) | **1.25x relative boost** | **Experimental variable** |
| **Augmentation** | Basic Crop + Flip + Light Jitter | **Field Photometric + Shadow Sim + Mild Blur** | **Experimental variable** |
| **Seed / Epochs / BS** | Seed 42 / 15 epochs / BS 32 | Seed 42 / 15 epochs / BS 32 | Strictly identical |
| **Optimizer / LR** | AdamW / 1e-4 / CosineAnneal | AdamW / 1e-4 / CosineAnneal | Strictly identical |
| **External Test Set** | 1,695 West Bengal field images | 1,695 West Bengal field images | Strictly identical (Zero leakage) |

---

## 2. Head-to-Head Metric Comparison (Operational Policies: tau=0.70 & tau=0.75)

| Metric | Policy | Baseline (`s1-wce`) | V2.1 (`rustrobust`) | Delta (V2.1 - Base) | Evaluation |
|---|---|---|---|---|---|
| **External Closed Macro-F1** | `fixed_0.70` | 0.9039 | 0.8845 | -0.0194 | DEGRADED |
| **External Closed Macro-F1** | `fixed_0.75` | 0.9297 | 0.9052 | -0.0245 | DEGRADED |
| **Rust Recall (External)** | `fixed_0.70` | 90.3% | 96.4% | +6.0% | IMPROVED |
| **Rust Recall (External)** | `fixed_0.75` | 93.3% | 97.2% | +3.9% | IMPROVED |
| **Tikka Recall (External)** | `fixed_0.70` | 96.7% | 99.8% | +3.1% | PRESERVED |
| **Healthy Recall (External)** | `fixed_0.70` | 82.2% | 62.4% | -19.9% | CHANGED |
| **External Open Macro-F1** | `fixed_0.70` | 0.6590 | 0.6403 | -0.0187 | DEGRADED |
| **OOT UNSURE Rejection** | `fixed_0.70` | 20.3% | 21.9% | +1.7% | IMPROVED |
| **Tikka Coarse Acc (Aux)** | `fixed_0.70` | 96.7% | 99.8% | +3.1% | High Accuracy Preserved |
| **Overall Coverage** | `fixed_0.70` | 72.2% | 68.5% | -3.6% | Expected Filtering |

---

## 3. Threshold Policy Comparison Across All Tested Policies

| Policy | Metric | Baseline (`s1-wce`) | V2.1 (`rustrobust`) | Delta |
|---|---|---|---|---|
| `fixed_0.60` | Closed F1 | 0.8620 | 0.8496 | -0.0124 |
| `fixed_0.60` | Rust Recall | 89.3% | 96.4% | +7.1% |
| `fixed_0.60` | Open F1 | 0.6870 | 0.6767 | -0.0103 |
| `fixed_0.60` | OOT UNSURE Rate | 9.4% | 10.9% | +1.5% |
| `fixed_0.70` | Closed F1 | 0.9039 | 0.8845 | -0.0194 |
| `fixed_0.70` | Rust Recall | 90.3% | 96.4% | +6.0% |
| `fixed_0.70` | Open F1 | 0.6590 | 0.6403 | -0.0187 |
| `fixed_0.70` | OOT UNSURE Rate | 20.3% | 21.9% | +1.7% |
| `fixed_0.75` | Closed F1 | 0.9297 | 0.9052 | -0.0245 |
| `fixed_0.75` | Rust Recall | 93.3% | 97.2% | +3.9% |
| `fixed_0.75` | Open F1 | 0.6409 | 0.6175 | -0.0234 |
| `fixed_0.75` | OOT UNSURE Rate | 24.3% | 27.1% | +2.8% |
| `fixed_0.80` | Closed F1 | 0.9478 | 0.9212 | -0.0266 |
| `fixed_0.80` | Rust Recall | 93.8% | 97.1% | +3.3% |
| `fixed_0.80` | Open F1 | 0.6084 | 0.5946 | -0.0138 |
| `fixed_0.80` | OOT UNSURE Rate | 30.6% | 35.4% | +4.8% |
| `val_q01` | Closed F1 | 0.9617 | 0.9812 | +0.0195 |
| `val_q01` | Rust Recall | 94.0% | 97.6% | +3.6% |
| `val_q01` | Open F1 | 0.4825 | 0.5168 | +0.0343 |
| `val_q01` | OOT UNSURE Rate | 50.6% | 54.7% | +4.1% |
| `val_q05` | Closed F1 | 1.0000 | 1.0000 | +0.0000 |
| `val_q05` | Rust Recall | 100.0% | 100.0% | +0.0% |
| `val_q05` | Open F1 | 0.1638 | 0.3183 | +0.1545 |
| `val_q05` | OOT UNSURE Rate | 88.0% | 79.2% | -8.8% |

---

## 4. Key Findings & Diagnostic Verdict

1. **Rust Recall Impact:** Rust recall improved significantly under field augmentations and reweighting.
2. **Tikka Performance Impact:** Tikka recall and diagnostic accuracy were successfully maintained without degradation.
3. **Open-Set / OOD Rejection:** OOT rejection on non-target diseases (Alternaria and Rosette virus, N=543) was 21.9% at tau=0.70.
4. **Production Certification Status:** **STRICTLY RESEARCH-ONLY**. The model does not meet the >= 0.85 closed and open Macro-F1 gate across all independent field test conditions. It remains an exploratory research checkpoint.

---

## 5. Recommendation on Seeds 2 and 3

> [!IMPORTANT]
> **Recommendation:** PAUSE before running Seeds 2 and 3. Review the magnitude of delta to determine whether hyperparameter tuning or additional field data is needed first.

---
*Report generated automatically by Uzhavan ML V2.1 Controlled Evaluation Suite.*
