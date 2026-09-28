# Uzhavan M4 V2.3.1 Seed 42 — Evaluation & Comparative Report
**Document Type:** Empirical Model Evaluation & Comparative Audit  
**Date:** 2026-09-28  
**Scope:** Checkpoint `runs_m4_v2_3_1\UZ-M4-v2.3.1-groundnut-s1-triclass-balance\checkpoint_best.pt`  
**Execution Host:** Acer ALPHA (NVIDIA GeForce RTX 4050 Laptop GPU, 6GB VRAM, CUDA 12.6)  
**Evaluated Cohorts:**
1. Primary Benchmark: Untouched Final External Test Universe ($N=928$ scorable / $N=1,360$ total)
2. Historical Replication Benchmark: Full Canonical External Test Set ($N=1,152$ scorable / $N=1,695$ total from West Bengal Sasmal dataset, `in_groundnut_wb_sasmal`)  
**Artifact Dependencies:**
- [m4_v2_3_1_s1_metrics.json](file:///Users/ajaikumarn/Desktop/agri/reports/artifacts/m4_v2_3_1_s1_metrics.json)
- [m4_v2_3_1_s1_comparison.csv](file:///Users/ajaikumarn/Desktop/agri/reports/artifacts/m4_v2_3_1_s1_comparison.csv)

---

## 1. Executive Summary & Core Diagnostic Finding

The M4 V2.3.1 controlled intervention applied a two-variable adjustment to resolve the 35-point Rust recall collapse observed in V2.3 S42:
1. **Moderated Green Healthy Exposure ($1:1 \longrightarrow 1:2$ vs. Tikka):** $w_{green} = \frac{1118}{285} \approx 3.922807$
2. **Asymmetric Rust WCE Multiplier ($1.0\times \longrightarrow 1.25\times$):** Normalized weights: $[1.2203, 0.9889, 0.7908]$

Evaluation of the completed Seed 42 checkpoint on the Acer RTX 4050 reveals a dramatic seesaw effect:

$$\begin{aligned}
\text{Rust Recall:} &\quad 60.00\% \longrightarrow \mathbf{96.67\%} \quad (+36.67\text{ pts}) \quad [\textbf{RUST FULLY RECOVERED}] \\
\text{Healthy Recall:} &\quad 84.67\% \longrightarrow \mathbf{33.67\%} \quad (-51.00\text{ pts}) \quad [\textbf{CATASTROPHIC HEALTHY COLLAPSE}] \\
\text{Tikka Recall:} &\quad 99.07\% \longrightarrow \mathbf{99.07\%} \quad (\text{Identical, near-ceiling}) \\
\text{Macro-F1 (Canonical 1,152):} &\quad 0.8399 \longrightarrow \mathbf{0.7197} \quad (-0.1202) \\
\text{Macro-F1 (Untouched 928):} &\quad 0.8262 \longrightarrow \mathbf{0.7222} \quad (-0.1040)
\end{aligned}$$

---

## 2. Three-Way Controlled Comparison Matrix (Canonical $N=1,152$)

| Metric | V2.2 Seed 42 (Baseline) | V2.3 Seed 42 (1:1 Green, 1.0x Rust) | V2.3.1 Seed 42 (1:2 Green, 1.25x Rust) | Target Success Gate | Gate Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Healthy recall** | 70.33% | 84.67% | **33.67%** | $\ge 80.00\%$ | ❌ **FAIL (-46.33 pts)** |
| **Rust recall** | 95.00% | 60.00% | **96.67%** | $\ge 90.00\%$ | ✅ **PASS (+6.67 pts)** |
| **Tikka recall** | 96.99% | 99.07% | **99.07%** | $\ge 96.00\%$ | ✅ **PASS (+3.07 pts)** |
| **Macro-F1** | 0.8548 | 0.8399 | **0.7197** | $\ge 0.8600$ | ❌ **FAIL (-0.1403)** |
| **Accuracy** | 82.90% | 87.50% | **64.76%** | — | -18.14 pts vs V2.2 |
| **$\tau=0.70$ coverage** | 68.40% | 80.47% | **87.76%** | $\ge 85.00\%$ | ✅ **PASS** |
| **$\tau=0.70$ accepted accuracy** | 93.27% | 92.66% | **66.77%** | $\ge 90.00\%$ | ❌ **FAIL (-23.23 pts)** |
| **Open-set Macro-F1** | 0.6964 | 0.6651 | **0.6147** | $\ge 0.8500$ | ❌ **FAIL** |
| **Healthy $\longrightarrow$ Tikka Errors** | 178 | 92 | **398** | $< 120$ | ❌ **CRITICAL EXPLOSION** |
| **Rust $\longrightarrow$ Tikka Errors** | 5 | 47 | **4** | $\le 12$ | ✅ **RESCUED** |
| **Rust $\longrightarrow$ Healthy Errors** | 1 | 1 | **0** | $\le 2$ | ✅ **ZERO** |

---

## 3. Confusion Matrix Breakdown

### A. Canonical Benchmark ($N=1,152$ scorable samples)
*Accuracy: $64.76\%$ ($746 / 1,152$) | Macro-F1: $0.7197$*

| True Class | Pred Healthy | Pred Rust | Pred Tikka | Total True | Class Recall | Class Precision | Class F1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Healthy or Abiotic** | **202** | 0 | **398** | 600 | **33.67%** | 98.54% | 0.4988 |
| **Rust** | 0 | **116** | **4** | 120 | **96.67%** | 99.15% | 0.9789 |
| **Tikka Leaf Spot** | 3 | 1 | **428** | 432 | **99.07%** | 51.57% | 0.6815 |
| **Total Predicted** | 205 | 117 | 830 | 1,152 | — | — | **0.7197** |

---

### B. Untouched Final External Test Universe ($N=928$ scorable samples)
*Accuracy: $65.09\%$ ($604 / 928$) | Macro-F1: $0.7222$*

| True Class | Pred Healthy | Pred Rust | Pred Tikka | Total True | Class Recall | Class Precision | Class F1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Healthy or Abiotic** | **165** | 0 | **318** | 483 | **34.16%** | 98.80% | 0.5077 |
| **Rust** | 0 | **96** | **3** | 99 | **96.97%** | 98.97% | 0.9796 |
| **Tikka Leaf Spot** | 2 | 1 | **343** | 346 | **99.13%** | 51.66% | 0.6792 |
| **Total Predicted** | 167 | 97 | 664 | 928 | — | — | **0.7222** |

---

## 4. Directional Error Analysis: The Mechanism of the Collapse

1. **Rust is completely safeguarded from Tikka:**
   The $1.25\times$ Rust WCE loss multiplier was remarkably potent. Rust $\to$ Tikka errors dropped from $47 \longrightarrow 4$ (-91.5%), restoring Rust recall to $96.67\%$. Rust is essentially immune to misclassification.
2. **Healthy foliage was overwhelmed by Tikka:**
   In V2.3, the $7.8456\times$ oversampling ($1:1$ exposure against Tikka) kept Healthy $\to$ Tikka errors down at 92.
   When oversampling was reduced to $3.9228\times$ ($1:2$ exposure against Tikka) while simultaneously strengthening Rust with a $1.25\times$ loss weight, the network solved the optimization objective by drastically expanding the Tikka decision boundary into the Healthy feature manifold.
   Out of 600 healthy samples, **398 were predicted as Tikka (a failure rate of $66.33\%$)**.
3. **Selective Classification ($\tau=0.70$) Breakdown:**
   Because Tikka predicted probabilities saturated across the healthy field images, $\tau=0.70$ accepted accuracy dropped from $92.66\% \longrightarrow 66.77\%$. The threshold was unable to separate these false positives from true Tikka infections.

---

## 5. Decision Tree & Next Action Rule

Based on the predefined decision criteria:
$$\begin{array}{rcc}
\text{Healthy recall } \ge 80\% & (33.67\%) & \text{FAIL} \\
\text{Rust recall } \ge 90\% & (96.67\%) & \text{PASS} \\
\text{Tikka recall } \ge 96\% & (99.07\%) & \text{PASS} \\
\text{Macro-F1 } \ge 0.86 & (0.7197) & \text{FAIL}
\end{array}$$

### Decision Verdict:
**STRICT HALT: DO NOT RUN SEEDS 1337 OR 2024.**  
Replication of V2.3.1 is strictly prohibited as it fails 2 out of the 4 primary gate requirements.
