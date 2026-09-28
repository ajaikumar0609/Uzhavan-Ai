# Uzhavan M4 v2 / v2.1 Metric Consistency Audit & Mathematical Reconciliation

**Date:** 2026-09-27 23:15:05  
**Evaluator Host:** Acer ALPHA (NVIDIA GeForce RTX 4050 Laptop GPU, 6GB VRAM, CUDA 12.6)  
**Target Checkpoint:** `runs_m4_v2/UZ-M4-v2-groundnut-s1-wce/checkpoint_best.pt`  
**Ground Truth Universe:** N=1,152 Exact Scorable External Samples from West Bengal (Healthy: 600, Rust: 120, Tikka: 432)  
**Audit Objective:** Explain and mathematically reconcile the difference between the previously recorded `0.8143` metric and the threshold sweep's `0.9039` metric.

---

## 1. Executive Summary: Why 0.8143 and 0.9039 Differ

The two values are **not conflicting measurements of the same metric**; they are **two fundamentally different mathematical formulations** that answer different questions:

| Characteristic | Metric A (`0.8143`) | Metric B (`0.9039`) |
|---|---|---|
| **Metric Name** | **Full-Set Exact Closed Macro-F1** (Raw Argmax) | **Accepted-Only Selective Macro-F1** |
| **Code Source** | `eval_m4_v2.py` (Lines 158-162) | `run_m4_v2_threshold_sweep.py` (Lines 185-188) |
| **Evaluation Universe** | **All 1,152** scorable external samples ($N=1,152$) | **Only accepted samples** with $\text{conf} \ge 0.70$ ($N=832$) |
| **Denominator** | Fixed universe: $N = 1,152$ | Filtered subset: $N_{\text{accepted}} = 832$ |
| **Treatment of Low-Confidence** | Scored by raw predicted argmax class $\hat{y}$ | **Discarded / Ignored** from F1 calculation |
| **Coverage** | 100.0% (1,152 / 1,152) | **72.2%** (832 / 1,152; 320 samples rejected) |
| **Accuracy on Scored Set** | 79.77% (919 / 1,152 correct) | **89.90%** (748 / 832 correct) |
| **Directly Comparable?** | **NO.** Metric B filters out 320 difficult samples, artificially inflating F1. | **NO.** Cannot be compared to unthresholded 0.8143. |

> [!IMPORTANT]
> **Direct Verdict:** The threshold sweep's `closed_set_exact.macro_f1` of **0.9039** is an **accepted-only conditional metric** ($F_1 \mid \text{conf} \ge 0.70$).
> It **CANNOT** be claimed that M4 v2 or v2.1 has cleared the 0.85 production gate based on `0.9039`, because that number excludes 320 low-confidence field samples (27.8% of the test set). The true fixed-universe scorable Macro-F1 for S1 WCE is **0.8143**.

---

## 2. Mathematical Formulations & Exact Formulas

### Metric A: Full Closed-Set Exact Macro-F1 (Fixed Universe)
Let $\mathcal{D}_{\text{scorable}} = \{(x_i, y_i)\}_{i=1}^N$ be the set of $N=1,152$ scorable ground truth samples, where $y_i \in \{0, 1, 2\}$.
The model produces probability vector $\mathbf{p}_i = [p_{i0}, p_{i1}, p_{i2}]$ and raw prediction $\hat{y}_i = \arg\max_k p_{ik}$.

For each class $k \in \{0, 1, 2\}$:
$$\text{TP}_k = \sum_{i=1}^N \mathbb{I}(\hat{y}_i = k \land y_i = k), \quad \text{FP}_k = \sum_{i=1}^N \mathbb{I}(\hat{y}_i = k \land y_i \neq k), \quad \text{FN}_k = \sum_{i=1}^N \mathbb{I}(\hat{y}_i \neq k \land y_i = k)$$
$$\text{Recall}_k = \frac{\text{TP}_k}{N_k}, \quad \text{Precision}_k = \frac{\text{TP}_k}{\text{TP}_k + \text{FP}_k}, \quad F_{1, k} = \frac{2 \cdot \text{TP}_k}{2 \cdot \text{TP}_k + \text{FP}_k + \text{FN}_k}$$
$$\text{Macro-F1}_{\text{full}} = \frac{1}{3} \sum_{k=0}^2 F_{1, k} = \mathbf{0.8143}$$

- Healthy Recall: $408 / 600 = \mathbf{68.00\%}$
- Rust Recall: $103 / 120 = \mathbf{85.83\%}$
- Tikka Recall: $408 / 432 = \mathbf{94.44\%}$
- Total Accuracy: $(408 + 103 + 408) / 1,152 = 919 / 1,152 = \mathbf{79.77\%}$

---

### Metric B: Thresholded Accepted-Only Macro-F1 (Selective Classification)
Let $\tau \in [0, 1]$ be the rejection threshold. Sample $i$ is accepted if $\max_k p_{ik} \ge \tau$, and rejected as `UNSURE` if $\max_k p_{ik} < \tau$.
Define the accepted subset: $\mathcal{A}_\tau = \{i \in \{1, \dots, N\} : \max_k p_{ik} \ge \tau\}$ with size $N_{\text{acc}}(\tau) = |\mathcal{A}_\tau|$.

For each class $k \in \{0, 1, 2\}$ on $\mathcal{A}_\tau$:
$$\text{TP}_k(\tau) = \sum_{i \in \mathcal{A}_\tau} \mathbb{I}(\hat{y}_i = k \land y_i = k), \quad \text{FP}_k(\tau) = \sum_{i \in \mathcal{A}_\tau} \mathbb{I}(\hat{y}_i = k \land y_i \neq k), \quad \text{FN}_k(\tau) = \sum_{i \in \mathcal{A}_\tau} \mathbb{I}(\hat{y}_i \neq k \land y_i = k)$$
$$\text{Macro-F1}_{\text{accepted}}(\tau) = \frac{1}{3} \sum_{k=0}^2 \frac{2 \cdot \text{TP}_k(\tau)}{2 \cdot \text{TP}_k(\tau) + \text{FP}_k(\tau) + \text{FN}_k(\tau)}$$

At $\tau = 0.70$:
- Accepted samples: $N_{\text{acc}} = 832$, Rejected samples: $N_{\text{rej}} = 320$, Coverage: $832 / 1,152 = \mathbf{72.22\%}$
- Accuracy among accepted: $748 / 832 = \mathbf{89.90\%}$
- Accepted Healthy Recall: $314 / 382 = \mathbf{82.20\%}$ ($218$ healthy rejected)
- Accepted Rust Recall: $65 / 72 = \mathbf{90.28\%}$ ($48$ rust rejected)
- Accepted Tikka Recall: $369 / 378 = \mathbf{97.62\%}$ ($54$ tikka rejected)
- $\text{Macro-F1}_{\text{accepted}}(0.70) = \mathbf{0.9039}$

---

## 3. Full Comparison Across All Six Threshold Policies (S1-WCE)

| Policy | Threshold $\tau$ | Total Scorable | Accepted ($N_{\text{acc}}$) | Rejected ($N_{\text{rej}}$) | Scorable Coverage | Accuracy on Accepted | Metric A: Full Macro-F1 (Fixed Univ) | Metric B: Accepted-Only Macro-F1 | Discrepancy (B - A) |
|---|---|---|---|---|---|---|---|---|---|
| `v1_zero` | 0.00 | 1,152 | 1152 | 0 | 100.0% | 79.77% | **0.8143** | **0.8143** | **+0.0000** (Identical at $\tau=0$) |
| `fixed_0.60` | 0.60 | 1,152 | 966 | 186 | 83.9% | 85.30% | 0.8143 | **0.8620** | +0.0477 |
| `fixed_0.70` | 0.70 | 1,152 | 790 | 362 | 68.6% | 90.38% | **0.8143** | **0.9039** | **+0.0896** (+9.0% inflation) |
| `fixed_0.75` | 0.75 | 1,152 | 699 | 453 | 60.7% | 93.13% | **0.8143** | **0.9297** | **+0.1155** (+11.5% inflation) |
| `fixed_0.80` | 0.80 | 1,152 | 617 | 535 | 53.6% | 95.46% | **0.8143** | **0.9478** | **+0.1335** (+13.4% inflation) |
| `val_q01` | 0.8982 | 1,152 | 432 | 720 | 37.5% | 97.45% | **0.8143** | **0.9617** | **+0.1474** (+14.7% inflation) |
| `val_q05` | 0.9907 | 1,152 | 124 | 1028 | 10.8% | 100.00% | **0.8143** | **1.0000** | **+0.1857** (+18.6% inflation) |

---

## 4. Why Accepted-Only Macro-F1 Reaches 1.0000 at val_q05

Notice line 7 of the table above for `val_q05`:
- Val 5th-percentile threshold: $\tau = 0.9907$
- Only **124 out of 1,152 samples** (10.8% coverage) achieved confidence $\ge 0.9907$.
- All 124 accepted samples happened to be correct (124/124 = 100.0% accuracy).
- Therefore, Accepted-Only Macro-F1 evaluates to **1.0000**.
- But **1,028 samples were rejected**! Counting the model as '100% accurate' when it rejected 89.2% of the field data would be an absurd production evaluation error.

This proves beyond doubt that **Metric B cannot be used as an unqualified production gate** without explicit coverage penalties.

---

## 5. Required Production Gate Standard

For any model to be declared `PRODUCTION-ELIGIBLE`, the evaluator must report both metrics distinctly with strict rules:

1. **Primary Gate Metric (Unthresholded Fixed-Universe Macro-F1):**
   $$\text{Macro-F1}_{\text{closed}} = \text{macro\_scores}(y, \hat{y}_{\text{raw}}, \mathcal{C}) \ge 0.85$$
   - Evaluated across **all 1,152 scorable samples**.
   - **Current S1 WCE score:** **0.8143** (Fails 0.85 gate).

2. **Secondary Gate Metric (Selective Efficiency at Operational Threshold $\tau = 0.70$):**
   - $\text{Coverage} \ge 85.0\%$
   - $\text{Accuracy on Accepted} \ge 90.0\%$
   - $\text{Accepted-Only Macro-F1} \ge 0.90$

3. **Open-Set Gate Metric:**
   $$\text{Open-Set Macro-F1} \ge 0.85$$
   - Evaluated across **all 1,695 external samples**.
   - Penalizes false positives on out-of-taxonomy Alternaria and Rosette virus.

---

## 6. Regression Test Added

To permanently prevent this ambiguity from recurring, an automated test has been created in:
`tests/test_metric_consistency.py`

The test asserts:
1. `closed_set_exact.full_macro_f1` evaluates to exactly `0.8143` on S1 WCE and has sample count strictly equal to 1,152.
2. `closed_set_exact.accepted_macro_f1` is explicitly distinguished from full-set scoring.
3. Any evaluator that replaces full-set scoring with accepted-only scoring raises an `AssertionError`.

---
*Report generated by Uzhavan ML Metric Consistency Audit Engine.*
