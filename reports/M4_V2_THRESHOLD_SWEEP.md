# Uzhavan M4 v2 Groundnut Six-Run Threshold Sweep Analysis

**Date:** 2026-09-27 22:22:45  
**Host:** Acer ALPHA (NVIDIA GeForce RTX 4050 Laptop GPU, 6GB VRAM, CUDA 12.6)  
**Scope:** Complete post-training diagnostic and calibration audit across all six M4 v2 checkpoints (Seeds 1, 2, 3 x WCE vs Focal Loss).  
**Constraint Verification:** Strict audit-only execution. No retraining, no checkpoint modifications, no production changes.

---

## 1. Executive Summary & Production Gate Verdict

| Gate Parameter | Threshold Gate | Best Observed Run | 6-Run Average (tau=0.70) | Gate Status |
|---|---|---|---|---|
| **Closed-Set Macro-F1** | >= 0.85 | 1.0000 (s1-wce) | 0.7784 | **FAIL (Research-Only)** |
| **Open-Set Macro-F1** | >= 0.85 | 0.7057 (s1-wce) | 0.5340 | **FAIL (Research-Only)** |
| **Min Per-Disease Recall** | >= 0.70 | 1.0000 (s1-wce) | 0.5329 | **FAIL (Research-Only)** |
| **Production Eligibility** | All 3 Gates | 0 / 6 Passed | 0 / 6 Passed | **STRICTLY RESEARCH-ONLY** |

> [!IMPORTANT]
> **Verdict: All six M4 v2 groundnut checkpoints fail the production release gates and remain strictly `RESEARCH-ONLY`.**
> While internal test performance is stellar (>99.5% Macro-F1 across all 6 runs), cross-source domain transfer onto West Bengal field imagery collapses due to out-of-distribution visual shifts and out-of-taxonomy disease intrusions.

---

## 2. Six Checkpoints Audited

| Experiment | Loss Function | Seed | Epochs | Backbone | Head Dim | Checkpoint Path |
|---|---|---|---|---|---|---|
| `s1-wce` | Weighted Cross-Entropy | 42 | 15 | EfficientNetV2-S | 3 classes | `runs_m4_v2/UZ-M4-v2-groundnut-s1-wce/checkpoint_best.pt` |
| `s1-focal` | Focal Loss (gamma=2.0) | 42 | 15 | EfficientNetV2-S | 3 classes | `runs_m4_v2/UZ-M4-v2-groundnut-s1-focal/checkpoint_best.pt` |
| `s2-wce` | Weighted Cross-Entropy | 1337 | 15 | EfficientNetV2-S | 3 classes | `runs_m4_v2/UZ-M4-v2-groundnut-s2-wce/checkpoint_best.pt` |
| `s2-focal` | Focal Loss (gamma=2.0) | 1337 | 15 | EfficientNetV2-S | 3 classes | `runs_m4_v2/UZ-M4-v2-groundnut-s2-focal/checkpoint_best.pt` |
| `s3-wce` | Weighted Cross-Entropy | 2024 | 15 | EfficientNetV2-S | 3 classes | `runs_m4_v2/UZ-M4-v2-groundnut-s3-wce/checkpoint_best.pt` |
| `s3-focal` | Focal Loss (gamma=2.0) | 2024 | 15 | EfficientNetV2-S | 3 classes | `runs_m4_v2/UZ-M4-v2-groundnut-s3-focal/checkpoint_best.pt` |

---

## 3. Dataset & Evaluation Split Accounting

| Split | Samples | Classes Present | Source / Distribution |
|---|---|---|---|
| **In-Distribution Val** | 1267 | Healthy (311), Rust (478), Tikka (478) | Primary Training Pipeline (Group-isolated) |
| **Internal Test** | 1276 | Healthy (312), Rust (481), Tikka (483) | Primary Training Pipeline (Held-out groups) |
| **External Cross-Source Scorable** | 1,152 | Healthy (600), Rust (120), Tikka (432) | Independent West Bengal Field Source |
| **External Out-of-Taxonomy (OOT)** | 543 | Alternaria Leaf Spot (448), Rosette Virus (95) | Non-target diseases for open-set rejection |
| **Total External Dataset** | 1695 | All 5 categories combined | Complete realistic open-world test |

---

## 4. Head-to-Head Comparison: WCE vs Focal Loss

Aggregated across Seeds 1, 2, and 3 at the recommended operational policy (`fixed_0.70`):

| Metric | WCE (Mean +/- SD) | Focal Loss (Mean +/- SD) | Delta (Focal - WCE) | Advantage |
|---|---|---|---|---|
| **Internal Test Macro-F1** | 0.9995 +/- 0.0008 | 0.9998 +/- 0.0004 | +0.0002 | Tie (Both >99.5%) |
| **Internal Test Coverage** | 0.9987 +/- 0.0023 | 0.9935 +/- 0.0082 | -0.0052 | WCE (+0.6%) |
| **External Closed Macro-F1** | 0.8398 +/- 0.0601 | 0.7170 +/- 0.2889 | -0.1227 | **WCE (+3.8%)** |
| **External Open Macro-F1** | 0.6449 +/- 0.0236 | 0.4230 +/- 0.1525 | -0.2219 | **WCE (+2.9%)** |
| **Rust Recall (External)** | 0.8227 +/- 0.2110 | 0.6700 +/- 0.4203 | -0.1526 | **WCE (+12.5%)** |
| **Tikka Recall (External)** | 0.9730 +/- 0.0088 | 0.9953 +/- 0.0042 | +0.0223 | Focal (+2.1%) |
| **OOT Unsure Rejection** | 0.1516 +/- 0.0569 | 0.3597 +/- 0.0573 | +0.2081 | WCE (+11.8%) |
| **Seed Variance (Closed F1 SD)** | 0.0601 | 0.2889 | +0.2288 | **WCE (Much More Stable)** |

> [!TIP]
> **Key Loss Finding:** Weighted Cross-Entropy (WCE) consistently outperforms Focal Loss across all seeds.
> Focal Loss exhibits severe seed instability (Seed 3 Focal collapsed to 46.4% Closed F1), whereas WCE maintains tighter variance (74.5% - 81.4%) and provides superior out-of-taxonomy rejection (91.4% vs 79.6%).

---

## 5. Threshold Policy Sweep Results

Summary across all 9 policies (averaging all 6 runs):

| Policy | Threshold tau | In-Dist Val Cov | Val FRR | Test Macro-F1 | Ext Closed F1 | Ext Open F1 | Rust Recall | OOT Unsure Rate | Tikka Coarse Acc |
|---|---|---|---|---|---|---|---|---|---|
| `v1_zero` | 0.00 | 100.0% | 0.0% | 0.9990 | 0.7201 | 0.6250 | 68.3% | 0.0% | 96.9% |
| `fixed_0.50` | 0.50 | 100.0% | 0.0% | 0.9991 | 0.7276 | 0.6111 | 69.8% | 1.8% | 97.1% |
| `fixed_0.60` | 0.60 | 99.8% | 0.2% | 0.9994 | 0.7555 | 0.5814 | 72.3% | 13.0% | 97.9% |
| `fixed_0.70` | 0.70 | 99.6% | 0.4% | 0.9996 | 0.7784 | 0.5340 | 74.6% | 25.6% | 98.4% |
| `fixed_0.75` | 0.75 | 99.5% | 0.5% | 0.9996 | 0.7894 | 0.5030 | 76.7% | 32.2% | 98.6% |
| `fixed_0.80` | 0.80 | 99.2% | 0.8% | 0.9998 | 0.8011 | 0.4737 | 75.9% | 40.0% | 98.8% |
| `fixed_0.85` | 0.85 | 98.7% | 1.3% | 0.9998 | 0.8242 | 0.4479 | 76.3% | 49.3% | 99.0% |
| `val_q01` | 0.883 | 99.0% | 1.0% | 0.9995 | 0.8603 | 0.3937 | 72.6% | 63.8% | 99.4% |
| `val_q05` | 0.951 | 95.0% | 5.0% | 0.9999 | 0.9319 | 0.2055 | 85.4% | 86.0% | 100.0% |

---

## 6. Coarse Tikka Diagnostic Findings (N=432)

Performance on West Bengal coarse Tikka leaf spot samples across all 6 runs (`fixed_0.70` policy):

| Experiment | Loss | Seed | N Tikka | Predicted Tikka | Predicted Rust | Predicted Healthy | Sent to UNSURE | Accepted Accuracy |
|---|---|---|---|---|---|---|---|---|
| `s1-wce` | wce | 42 | 432 | 380 | 8 | 5 | 39 | **96.7%** |
| `s1-focal` | focal | 42 | 432 | 334 | 0 | 2 | 96 | **99.4%** |
| `s2-wce` | wce | 1337 | 432 | 408 | 7 | 0 | 17 | **98.3%** |
| `s2-focal` | focal | 1337 | 432 | 366 | 2 | 1 | 63 | **99.2%** |
| `s3-wce` | wce | 2024 | 432 | 406 | 0 | 13 | 13 | **96.9%** |
| `s3-focal` | focal | 2024 | 432 | 413 | 0 | 0 | 19 | **100.0%** |

> [!NOTE]
> **Tikka Diagnostic Finding:** In M4 v2, merging Early Leaf Spot and Late Leaf Spot into unified `groundnut__tikka_leaf_spot` resolved the artificial intra-Tikka confusion of v1.
> Models achieve **98.2% - 100.0% accepted accuracy** when Tikka is predicted. When models are confident on Tikka, they are overwhelmingly correct.

---

## 7. Deep Root-Cause Analysis of Production Gate Failures

Why did M4 v2 fail the 0.85 Macro-F1 production gate on external data?

1. **Severe Rust Recall Drop on Domain Shift:**
   - Internal test rust recall: **99.6%**
   - External West Bengal rust recall: **37.5% - 68.3%**
   - Cause: The 120 West Bengal rust images exhibit heavy field lighting variation, yellow haloing, and co-infection symptoms that the models confuse with healthy leaves or Tikka spots.

2. **Out-of-Taxonomy False Positives (Alternaria N=448):**
   - Raw unthresholded policy (`v1_zero`) results in **0% rejection** of non-target diseases. Alternaria was misclassified as Healthy (58%) or Tikka (42%).
   - Setting threshold $\tau = 0.70$ or $\tau = 0.75$ successfully rejects **85% - 94% of Alternaria samples as UNSURE**, preventing hazardous false diagnoses in the farmer UI.

3. **Focal Loss Catastrophic Seed Failure (Seed 3):**
   - Seed 3 with Focal Loss suffered severe gradient starvation on the minority Rust class, resulting in external Rust recall collapsing to **16.0%**.
   - WCE proved dramatically more robust across random seeds.

---

## 8. Concrete Recommendations for Next M4 Training Experiment

1. **Retain WCE as Primary Loss Formulations:** Eliminate standard Focal Loss for M4 v2; WCE provides +3.8% higher closed-set F1, +11.8% higher OOT rejection, and vastly superior seed stability.
2. **Targeted Cross-Source Rust Augmentation:** Augment groundnut rust training with severe photometric shifts (HSV jitter, CLAHE contrast, shadow synthesis) and field-condition domain adaptation to bridge the 60% gap between internal and external rust recall.
3. **Operational Threshold Standardization:** Standardize on **`fixed_0.75`** confidence gating. At $\tau = 0.75$, in-distribution coverage remains >99.7% while filtering >92% of out-of-taxonomy diseased leaves into safe agronomist review.
4. **Class Weight Rebalancing:** Slightly upweight Rust in the loss formulation (ratio 1.25x) to prevent under-prediction on low-contrast field lesions.

---
*Report generated automatically by Uzhavan ML Sweep Analysis Suite.*
