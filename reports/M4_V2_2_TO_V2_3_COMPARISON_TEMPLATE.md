# Uzhavan M4 V2.2 vs. V2.3 Head-to-Head Comparison Template
**Document Type:** Comparative Performance & Gate Assessment Report  
**Date Created:** 2026-09-28  
**Scope:** Controlled comparison of M4 V2.2 Baseline against M4 V2.3 (Targeted Pure-Green Healthy Balancing)  
**Evaluation Set:** Fixed Canonical Scorable External Test Universe ($N=1,152$) and Open-Set Universe ($N=1,695$)  

---

## 1. Executive Summary & Experiment Context

| Attribute | M4 V2.2 Baseline | M4 V2.3 (Targeted Balancing) |
| :--- | :--- | :--- |
| **Model Architecture** | EfficientNetV2-S | EfficientNetV2-S |
| **Taxonomy** | 3 Classes (`healthy_or_abiotic`, `rust`, `tikka`) | 3 Classes (`healthy_or_abiotic`, `rust`, `tikka`) |
| **Loss Function** | Weighted Cross-Entropy (WCE, Rust mult = $1.0\times$) | Weighted Cross-Entropy (WCE, Rust mult = $1.0\times$) |
| **Data Augmentations** | Shadow simulation ($p=0.35$) + Gaussian blur ($p=0.20$) | Shadow simulation ($p=0.35$) + Gaussian blur ($p=0.20$) |
| **Training Sampler** | Uniform Random Shuffle | **Targeted Pure-Green Healthy Weighted Sampler** |
| **Effective Exposure** | Pure-Green Healthy : Tikka = $1 : 7.84$ | **Pure-Green Healthy : Tikka = $1.000 : 1.000$** |
| **Status** | Replication Baseline Locked | *Awaiting Seed 42 Execution on Acer ALPHA* |

---

## 2. Core Metric Comparison Table

All metrics below are computed over the fixed unthresholded universe ($N=1,152$) and operational policy $\tau=0.70$:

| Metric | V2.2 S42 | V2.2 S1337 | V2.2 S2024 | V2.2 $\mu \pm \sigma$ | V2.3 S42 *(Target)* | V2.3 S42 *(Actual)* | Delta vs. V2.2 S42 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Full-Set Macro-F1** | 0.8548 | 0.7089 | 0.9388 | **0.8342 $\pm$ 0.1163** | $\ge 0.8800$ | `[ PENDING ]` | — |
| **Healthy Recall** | 70.33% | 34.00% | 97.33% | **67.22% $\pm$ 31.78%** | $\ge 85.00\%$ | `[ PENDING ]` | — |
| **Rust Recall** | 95.00% | 95.00% | 81.67% | **90.56% $\pm$ 7.70%** | $\ge 90.00\%$ | `[ PENDING ]` | — |
| **Tikka Recall** | 96.99% | 98.15% | 97.22% | **97.45% $\pm$ 0.61%** | $\ge 96.00\%$ | `[ PENDING ]` | — |
| **Full-Set Accuracy** | 82.90% | 64.41% | 95.66% | **80.99% $\pm$ 15.71%** | $\ge 88.00\%$ | `[ PENDING ]` | — |
| **Open-Set Macro-F1** | 0.6964 | 0.5872 | 0.7857 | **0.6898 $\pm$ 0.0994** | $\ge 0.7500$ | `[ PENDING ]` | — |
| **$\tau=0.70$ Coverage** | 68.40% | 73.96% | 92.36% | **78.24% $\pm$ 12.54%** | $\ge 85.00\%$ | `[ PENDING ]` | — |
| **$\tau=0.70$ Accepted Accuracy** | 93.27% | 72.42% | 97.65% | **87.78% $\pm$ 13.48%** | $\ge 93.00\%$ | `[ PENDING ]` | — |

---

## 3. Production Gate Assessment

### Gate 1: Full-Set Closed Macro-F1 $\ge 0.85$ (Over all 1,152 scorable samples)
- **V2.2 Baseline:** $0.8342 \pm 0.1163$ $\to$ **FAIL** (S42=0.8548, S1337=0.7089, S2024=0.9388)
- **V2.3 S42 Result:** `[ PENDING ]`
- **Gate 1 Status:** `[ PENDING ]`

### Gate 2: Selective Efficiency at $\tau=0.70$ (Coverage $\ge 85\%$ AND Accepted Accuracy $\ge 90\%$)
- **V2.2 Baseline:** Coverage $= 78.24\% \pm 12.54\%$, Accepted Accuracy $= 87.78\% \pm 13.48\%$ $\to$ **FAIL**
- **V2.3 S42 Result:** Coverage = `[ PENDING ]`, Accepted Accuracy = `[ PENDING ]`
- **Gate 2 Status:** `[ PENDING ]`

### Gate 3: Open-Set Discrimination Gate (Open Macro-F1 $\ge 0.85$ over all 1,695 samples)
- **V2.2 Baseline:** $0.6898 \pm 0.0994$ $\to$ **FAIL**
- **V2.3 S42 Result:** `[ PENDING ]`
- **Gate 3 Status:** `[ PENDING ]`

---

## 4. Error Flow & Boundary Shift Diagnosis

| Error Direction | V2.2 S42 Count (%) | V2.2 S1337 Count (%) | V2.2 S2024 Count (%) | V2.3 S42 Count (%) | Target Direction |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Healthy $\longrightarrow$ Tikka** | **178 (29.67%)** | **396 (66.00%)** | **16 (2.67%)** | `[ PENDING ]` | **Must drop below 60 (<10%)** |
| **Healthy $\longrightarrow$ Rust** | **0 (0.00%)** | **0 (0.00%)** | **0 (0.00%)** | `[ PENDING ]` | **Must remain near 0** |
| **Rust $\longrightarrow$ Healthy** | **1 (0.83%)** | **2 (1.67%)** | **1 (0.83%)** | `[ PENDING ]` | **Must remain near 0** |
| **Rust $\longrightarrow$ Tikka** | **5 (4.17%)** | **4 (3.33%)** | **21 (17.50%)** | `[ PENDING ]` | **Must remain below 10** |
| **Tikka $\longrightarrow$ Healthy** | **2 (0.46%)** | **1 (0.23%)** | **11 (2.55%)** | `[ PENDING ]` | **Must remain below 15** |
| **Tikka $\longrightarrow$ Rust** | **11 (2.55%)** | **7 (1.62%)** | **1 (0.23%)** | `[ PENDING ]` | **Must remain below 15** |

---

## 5. Evaluation & Verification Instructions
*Upon completion of V2.3 training on Acer ALPHA:*
1. Run standalone evaluation using `scripts/eval_m4_v2_3.py`.
2. Extract metrics from `reports/artifacts/m4_v2_3_s1_metrics.json`.
3. Populate Section 2 and Section 4 above.
4. If V2.3 S42 achieves Full Macro-F1 $\ge 0.88$ and Healthy Recall $\ge 85\%$, proceed to 3-seed replication (Seeds 1337 and 2024).
