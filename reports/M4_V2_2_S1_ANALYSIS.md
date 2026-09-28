# Uzhavan M4 V2.2 Controlled Training Experiment Analysis

**Date:** 2026-09-28 00:16:18  
**Host:** Acer ALPHA (NVIDIA GeForce RTX 4050 Laptop GPU, 6GB VRAM, CUDA 12.6)  
**Experiment Target:** `UZ-M4-v2.2-groundnut-s1-wce-balanced-rust`  
**Comparison Set:**
1. `V2 Baseline S1 WCE` (`runs_m4_v2/UZ-M4-v2-groundnut-s1-wce`)
2. `V2.1 S1 WCE RustRobust` (`runs_m4_v2_1/UZ-M4-v2.1-groundnut-s1-wce-rustrobust`, Rust weight = 1.25x)
3. `V2.2 S1 WCE Balanced` (`runs_m4_v2_2/UZ-M4-v2.2-groundnut-s1-wce-balanced-rust`, Rust weight = 1.0x)

---

## 1. Controlled Experiment Hypothesis & Variable Isolation

| Factor | V2 Baseline S1 | V2.1 S1 RustRobust | V2.2 S1 Balanced | Status |
|---|---|---|---|---|
| **Architecture** | EfficientNetV2-S | EfficientNetV2-S | EfficientNetV2-S | Strictly identical |
| **Field-Robust Augmentation** | None (standard crop/flip) | Full (shadow, blur, color jitter) | Full (shadow, blur, color jitter) | **Identical to V2.1** |
| **Rust Loss Weight Multiplier** | 1.0x (standard) | 1.25x (boosted) | **1.0x (balanced standard)** | **Single variable changed** |
| **Optimizer / LR / Epochs** | AdamW / 1e-4 / 15 eps | AdamW / 1e-4 / 15 eps | AdamW / 1e-4 / 15 eps | Strictly identical |
| **Random Seed** | 42 | 42 | 42 | Strictly identical |

> **Hypothesis:** Resetting Rust loss weight from 1.25x to 1.0x while retaining the field-robust augmentations will recover the Healthy recall loss of V2.1 while preserving the external Rust recall improvements.

---

## 2. Three-Way Metric Comparison at Operational tau=0.70

| Metric | V2 Baseline S1 | V2.1 S1 (1.25x Rust) | V2.2 S1 (1.0x Rust) | Delta (V2.2 - V2.1) | Delta (V2.2 - Base) |
|---|---|---|---|---|---|
| **Full-Set Exact Macro-F1** (N=1152) | **0.8143** | **0.8108** | **0.8548** | +0.0440 | +0.0405 |
| **Healthy Recall (Full-Set)** | 68.0% | 55.5% | **70.3%** | +14.8% | +2.3% |
| **Rust Recall (Full-Set)** | 85.8% | 95.8% | **95.0%** | -0.8% | +9.2% |
| **Tikka Recall (Full-Set)** | 94.4% | 99.1% | **97.0%** | -2.1% | +2.5% |
| **Overall Accuracy (Full-Set)** | 79.8% | 76.0% | **82.9%** | +6.9% | +3.1% |
| **Accepted Macro-F1** (tau=0.70) | 0.9039 | 0.8845 | **0.9380** | +0.0535 | +0.0341 |
| **Accepted Accuracy** (tau=0.70) | 90.4% | 88.6% | **93.3%** | +4.7% | +2.9% |
| **Scorable Coverage** (tau=0.70) | 68.6% | 64.0% | **68.4%** | +4.4% | -0.2% |
| **Open-Set Macro-F1** (N=1695) | 0.6590 | 0.6403 | **0.6964** | +0.0561 | +0.0374 |
| **OOD UNSURE Rate** (tau=0.70) | 20.3% | 21.9% | **22.5%** | +0.6% | +2.2% |

---

## 3. Policy Sweep Breakdown across All Thresholds

| Policy | Model | Full-Set Macro-F1 | Healthy Recall | Rust Recall | Tikka Recall | Coverage | Accepted Acc | Accepted F1 | Open-Set F1 |
|---|---|---|---|---|---|---|---|---|---|
| `fixed_0.60` | V2_Base | **0.8143** | 68.0% | 85.8% | 94.4% | 83.9% | 85.3% | 0.8620 | 0.6870 |
| `fixed_0.60` | V2.1 | **0.8108** | 55.5% | 95.8% | 99.1% | 80.1% | 81.9% | 0.8496 | 0.6767 |
| `fixed_0.60` | V2.2 | **0.8548** | 70.3% | 95.0% | 97.0% | 81.4% | 89.8% | 0.9115 | 0.7293 |
| `fixed_0.70` | V2_Base | **0.8143** | 68.0% | 85.8% | 94.4% | 68.6% | 90.4% | 0.9039 | 0.6590 |
| `fixed_0.70` | V2.1 | **0.8108** | 55.5% | 95.8% | 99.1% | 64.0% | 88.6% | 0.8845 | 0.6403 |
| `fixed_0.70` | V2.2 | **0.8548** | 70.3% | 95.0% | 97.0% | 68.4% | 93.3% | 0.9380 | 0.6964 |
| `fixed_0.75` | V2_Base | **0.8143** | 68.0% | 85.8% | 94.4% | 60.7% | 93.1% | 0.9297 | 0.6409 |
| `fixed_0.75` | V2.1 | **0.8108** | 55.5% | 95.8% | 99.1% | 56.9% | 92.2% | 0.9052 | 0.6175 |
| `fixed_0.75` | V2.2 | **0.8548** | 70.3% | 95.0% | 97.0% | 60.6% | 95.7% | 0.9584 | 0.6746 |
| `fixed_0.80` | V2_Base | **0.8143** | 68.0% | 85.8% | 94.4% | 53.6% | 95.5% | 0.9478 | 0.6084 |
| `fixed_0.80` | V2.1 | **0.8108** | 55.5% | 95.8% | 99.1% | 51.0% | 94.9% | 0.9212 | 0.5946 |
| `fixed_0.80` | V2.2 | **0.8548** | 70.3% | 95.0% | 97.0% | 54.4% | 97.3% | 0.9726 | 0.6564 |
| `val_q01` | V2_Base | **0.8143** | 68.0% | 85.8% | 94.4% | 37.5% | 97.5% | 0.9617 | 0.4825 |
| `val_q01` | V2.1 | **0.8108** | 55.5% | 95.8% | 99.1% | 37.5% | 99.3% | 0.9812 | 0.5168 |
| `val_q01` | V2.2 | **0.8548** | 70.3% | 95.0% | 97.0% | 36.8% | 99.8% | 0.9962 | 0.5520 |
| `val_q05` | V2_Base | **0.8143** | 68.0% | 85.8% | 94.4% | 10.8% | 100.0% | 1.0000 | 0.1638 |
| `val_q05` | V2.1 | **0.8108** | 55.5% | 95.8% | 99.1% | 20.8% | 100.0% | 1.0000 | 0.3183 |
| `val_q05` | V2.2 | **0.8548** | 70.3% | 95.0% | 97.0% | 10.3% | 100.0% | 1.0000 | 0.2087 |

---

## 4. Production Gate Evaluation & Decision Criteria

### Production Gates Status for V2.2 Seed 1
1. **Primary Gate: Full-Set Exact Closed Macro-F1 $\ge 0.85$ (over all 1,152 external samples)**
   - **Result: 0.8548** — **PASS** (+0.0048 margin over threshold; absolute improvement of +0.0405 over V2 Baseline, relative +4.97%).
2. **Secondary Gate: Selective Efficiency at $\tau=0.70$ (Coverage $\ge 85\%$ AND Accepted Accuracy $\ge 90\%$)**
   - **Coverage: 68.4%** — **FAIL** (below 85% requirement by 16.6 percentage points; slightly below V2 Baseline's 68.6%).
   - **Accepted Accuracy: 93.3%** — **PASS** ($\ge 90\%$).
3. **Open-Set Gate: Open-Set Macro-F1 $\ge 0.85$ (over all 1,695 external samples)**
   - **Result: 0.6964** — **FAIL** (improved from 0.6590 base and 0.6403 V2.1, but remains far below the 0.85 threshold).

**Overall Gate Verdict: NOT PRODUCTION READY.**  
V2.2 is a promising research candidate that demonstrates a significantly improved Pareto frontier, but fails operational coverage at $\tau=0.70$ and open-set discrimination gates.

### Systematic Answers to Key Hypotheses
1. **Did V2.2 recover Healthy recall relative to V2.1?**
   - **YES (+14.8 percentage points)**. Healthy recall surged from 55.5% in V2.1 to **70.3%** in V2.2 (+2.3 points above V2 Baseline's 68.0%).
2. **Did V2.2 retain the Rust recall improvement?**
   - **YES (9.2 percentage points retained)**. V2.2 achieved **95.0%** Rust recall (vs 85.8% Baseline and 95.8% V2.1). V2.2 retained 92% of the augmentation-driven gain (+9.2 of +10.0 points) while eliminating the destructive Healthy trade-off.
3. **Did V2.2 preserve Tikka performance?**
   - **YES**. Tikka recall remains high at **97.0%** (+2.6 points over Baseline 94.4%, though slightly lower than V2.1's 99.1%). Tikka accepted accuracy at $\tau=0.70$ is **98.5%**.
4. **Did full-set Macro-F1 improve?**
   - **YES (+0.0405 absolute)**. Reached **0.8548** (vs 0.8143 Baseline and 0.8108 V2.1).
5. **Does V2.2 meet selective coverage/accuracy at $\tau=0.70$?**
   - **PARTIALLY**. Accepted Accuracy is high (93.3%), but Coverage (68.4%) fails the $\ge 85\%$ operational threshold.
6. **Did open-set behavior improve?**
   - **YES (+0.0374 over Base)**. Rose to 0.6964 with 22.5% OOD rejection, but fails the $\ge 0.85$ production gate.

---

## 5. Decision on Seeds 2 and 3

> **Verdict: PROCEED with Seeds 2 (1337) and 3 (2024) under the identical V2.2 configuration.**  
>
> *Rationale:*  
> Because the single Seed-42 score (0.8548) is only 0.0048 above the 0.85 primary gate threshold, Seed 42 alone cannot establish whether the threshold is statistically robust. Running Seeds 1337 and 2024 without altering any architecture, augmentation, loss weights, or optimizer hyperparameters will yield the critical empirical bounds ($\mu \pm \sigma$) needed to confirm whether the V2.2 configuration consistently clears the primary gate.
>
> **Strict Operational Constraints:**
> - NO production deployment.
> - NO backbone changes (EfficientNetV2-S remains fixed).
> - NO hyperparameter or augmentation modifications.

---
*Report generated by Uzhavan ML V2.2 Evaluation Engine.*
