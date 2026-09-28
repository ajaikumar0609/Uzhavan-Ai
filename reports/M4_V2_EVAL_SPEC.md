# UZHAVAN M4 v2 Evaluation Specification & Calibration Protocol

**Document Version:** 2.0  
**Date:** 2026-09-26  
**Status:** Approved Pre-Training Specification  
**Associated Implementation:** [eval_m4_v2.py](file:///Users/ajaikumarn/Desktop/agri/uzhavan_ml/scripts/eval_m4_v2.py)  
**Historical v1 Script (Preserved):** [eval_m4.py](file:///Users/ajaikumarn/Desktop/agri/uzhavan_ml/scripts/eval_m4.py)

---

## 1. Overview & Purpose

During the M4 v1 evaluation audit, two critical evaluation-code flaws were diagnosed in `eval_m4.py`:
1. **The Ascending Search Bug:** The UNSURE threshold selection loop searched upwards from 0.0 on clean in-distribution validation data, breaking immediately on step 0 (`thr = 0.0`) because validation accuracy exceeded 90%. This deactivated the UNSURE rejection mechanism for all crops and seeds.
2. **Subset False-Positive Masking:** In cross-source evaluation, the script calculated F1 strictly over the subset of scorable samples ($N = 720$), ignoring false alarms triggered on the remaining 975 external samples (e.g. 28 false healthy predictions on Alternaria, 23 false rust predictions on Rosette/Tikka), thereby artificially inflating closed-set precision.

`eval_m4_v2.py` resolves these issues while preserving historical comparability. It implements dual closed-set and open-set metric reporting, proper calibration policies, and explicit coarse Tikka accounting.

---

## 2. Mathematical Metric Formulation

Let $\mathcal{D}_{\text{ext}}$ be the full external cross-source test set ($N = 1,695$ for groundnut).  
Let $\mathcal{C}_{\text{train}} = \{c_1, \dots, c_K\}$ be the $K$ classes present in the model's output head ($K=5$ in v1).  
Let $\mathcal{S} \subset \mathcal{D}_{\text{ext}}$ be the scorable subset whose true labels belong to $\mathcal{C}_{\text{train}}$ ($N = 720$ for Groundnut Healthy + Rust).  
Let $\mathcal{T}_{\text{tikka}} \subset \mathcal{D}_{\text{ext}}$ be the Tikka leaf spot samples ($N = 432$).  
Let $\mathcal{O} \subset \mathcal{D}_{\text{ext}}$ be the out-of-taxonomy samples ($N = 543$: Alternaria + Rosette).

### 2.1 Closed-Set Scorable Metrics (Evaluated on $\mathcal{S}$, $N=720$)
For each scorable class $j \in \{\text{healthy}, \text{rust}\}$:
$$\text{TP}_j = \sum_{i \in \mathcal{S}} \mathbb{I}(y_i = j \land \hat{y}_i = j \land \text{conf}_i \ge \tau)$$
$$\text{FN}_j = \sum_{i \in \mathcal{S}} \mathbb{I}(y_i = j \land (\hat{y}_i \ne j \lor \text{conf}_i < \tau))$$
$$\text{FP}_{\text{closed}, j} = \sum_{i \in \mathcal{S}} \mathbb{I}(y_i \ne j \land \hat{y}_i = j \land \text{conf}_i \ge \tau)$$

$$\text{Recall}_{\text{closed}, j} = \frac{\text{TP}_j}{\sum_{i \in \mathcal{S}} \mathbb{I}(y_i = j)}$$
$$\text{Precision}_{\text{closed}, j} = \frac{\text{TP}_j}{\text{TP}_j + \text{FP}_{\text{closed}, j}}$$
$$\text{F1}_{\text{closed}, j} = \frac{2 \cdot \text{TP}_j}{2 \cdot \text{TP}_j + \text{FP}_{\text{closed}, j} + \text{FN}_j}$$
$$\text{Macro-F1}_{\text{closed}} = \frac{1}{|\mathcal{S}_{\text{classes}}|} \sum_{j \in \mathcal{S}_{\text{classes}}} \text{F1}_{\text{closed}, j}$$

### 2.2 Open-Set False-Positive Accounting (Evaluated on All $N=1,695$)
In open-set evaluation, false positives include **any sample in $\mathcal{D}_{\text{ext}}$** whose prediction is $j$, even if the true label is out-of-taxonomy or a coarse category:
$$\text{FP}_{\text{open}, j} = \sum_{i \in \mathcal{D}_{\text{ext}}} \mathbb{I}(y_i \ne j \land \hat{y}_i = j \land \text{conf}_i \ge \tau)$$

$$\text{Precision}_{\text{open}, j} = \frac{\text{TP}_j}{\text{TP}_j + \text{FP}_{\text{open}, j}}$$
$$\text{F1}_{\text{open}, j} = \frac{2 \cdot \text{TP}_j}{2 \cdot \text{TP}_j + \text{FP}_{\text{open}, j} + \text{FN}_j}$$
$$\text{Macro-F1}_{\text{open}} = \frac{1}{|\mathcal{S}_{\text{classes}}|} \sum_{j \in \mathcal{S}_{\text{classes}}} \text{F1}_{\text{open}, j}$$

### 2.3 Coarse Tikka Diagnostic Metric ($N=432$)
The Tikka complex is evaluated as an auxiliary coarse diagnostic:
$$\text{Acc}_{\text{coarse}} = \frac{1}{|\mathcal{T}_{\text{tikka}}|} \sum_{i \in \mathcal{T}_{\text{tikka}}} \mathbb{I}(\hat{y}_i \in \{\text{early\_leaf\_spot}, \text{late\_leaf\_spot}\})$$
$$\text{Acc}_{\text{coarse, accepted}} = \frac{\sum_{i \in \mathcal{T}_{\text{tikka}}} \mathbb{I}(\hat{y}_i \in \{\text{early\_leaf\_spot}, \text{late\_leaf\_spot}\} \land \text{conf}_i \ge \tau)}{\sum_{i \in \mathcal{T}_{\text{tikka}}} \mathbb{I}(\text{conf}_i \ge \tau)}$$

> **Critical Rule:** Coarse Tikka accuracy is an auxiliary diagnostic of canopy leaf spot pathology. It is **never** counted as exact early or late leaf spot ground truth, and cannot be used to certify single-disease recall gates.

### 2.4 Out-of-Taxonomy UNSURE Rejection Metric ($N=543$)
For samples whose true pathology does not exist in the training taxonomy (e.g. Alternaria leaf spot, Rosette virus):
$$\text{UNSURE Rate}_{\text{OOT}} = \frac{1}{|\mathcal{O}|} \sum_{i \in \mathcal{O}} \mathbb{I}(\text{conf}_i < \tau)$$

---

## 3. UNSURE Calibration Procedure & Policy Comparison

To establish an evidence-based rejection policy, four calibration strategies were evaluated using the held-out validation split (`val`) across all three v1 seeds:

1. **Policy `v1_zero` ($\tau = 0.0$):** Legacy baseline (broken ascending search).
2. **Policy `fixed_0.70` ($\tau = 0.70$):** Fixed unscaled softmax confidence floor.
3. **Policy `fixed_0.75` ($\tau = 0.75$):** Moderate unscaled confidence floor.
4. **Policy `val_q05`:** 5th percentile of softmax confidence among correctly classified validation predictions.
5. **Policy `val_q01`:** 1st percentile of softmax confidence among correctly classified validation predictions.
6. **Policy `temp_scaled_fixed_0.70`:** Logits scaled by optimal validation temperature $T \approx 0.44$, then thresholded at 0.70.

### Empirical Evaluation Across Seeds (Measured Results)

#### Seed 1 (`UZ-M4-v1.0-a898475e-s1`, $T_{\text{val}} = 0.4432$)
| Policy | Threshold $\tau$ | In-Dist Val Cov | In-Dist Val FRR | Test Cov | Test AccAcc | OOT Unsure Rate | Rust Prec (Closed) | Rust Prec (Open) | Tikka Coarse Acc |
|---|---|---|---|---|---|---|---|---|---|
| `v1_zero` | 0.000 | 100.0% | 0.0% | 100.0% | 100.0% | **0.0%** | 100.0% | **86.3%** | 96.5% |
| `fixed_0.70` | 0.700 | 100.0% | 0.0% | 100.0% | 100.0% | **63.4%** | 100.0% | **100.0%** | 100.0% |
| `fixed_0.75` | 0.750 | 100.0% | 0.0% | 100.0% | 100.0% | **68.9%** | 100.0% | **100.0%** | 100.0% |
| `val_q01` | 0.901 | 99.0% | 1.0% | 98.0% | 100.0% | **94.8%** | 100.0% | **100.0%** | 100.0% |
| `val_q05` | 0.908 | 94.9% | 5.1% | 93.1% | 100.0% | **96.3%** | 100.0% | **100.0%** | 100.0% |
| `temp_scaled_0.70` | 0.700 | 100.0% | 0.0% | 100.0% | 100.0% | **26.9%** | 100.0% | **92.2%** | 98.2% |

#### Seed 2 (`UZ-M4-v1.0-a898475e-s2`, $T_{\text{val}} = 0.4550$)
| Policy | Threshold $\tau$ | In-Dist Val Cov | In-Dist Val FRR | Test Cov | Test AccAcc | OOT Unsure Rate | Rust Prec (Closed) | Rust Prec (Open) | Tikka Coarse Acc |
|---|---|---|---|---|---|---|---|---|---|
| `v1_zero` | 0.000 | 100.0% | 0.0% | 100.0% | 99.9% | **0.0%** | 100.0% | **83.3%** | 99.8% |
| `fixed_0.70` | 0.700 | 99.8% | 0.2% | 99.9% | 99.9% | **68.3%** | 100.0% | **90.3%** | 99.7% |
| `fixed_0.75` | 0.750 | 99.7% | 0.3% | 99.8% | 99.9% | **77.3%** | 100.0% | **92.5%** | 99.7% |
| `val_q01` | 0.840 | 98.9% | 1.0% | 98.9% | 99.9% | **87.1%** | 100.0% | **96.7%** | 100.0% |
| `val_q05` | 0.892 | 94.8% | 5.1% | 95.5% | 100.0% | **93.6%** | 100.0% | **100.0%** | 100.0% |
| `temp_scaled_0.70` | 0.700 | 100.0% | 0.0% | 100.0% | 99.9% | **33.9%** | 100.0% | **85.4%** | 99.8% |

#### Seed 3 (`UZ-M4-v1.0-a898475e-s3`, $T_{\text{val}} = 0.4180$)
| Policy | Threshold $\tau$ | In-Dist Val Cov | In-Dist Val FRR | Test Cov | Test AccAcc | OOT Unsure Rate | Rust Prec (Closed) | Rust Prec (Open) | Tikka Coarse Acc |
|---|---|---|---|---|---|---|---|---|---|
| `v1_zero` | 0.000 | 100.0% | 0.0% | 100.0% | 99.8% | **0.0%** | 100.0% | **81.6%** | 94.0% |
| `fixed_0.70` | 0.700 | 99.9% | 0.1% | 99.8% | 99.9% | **74.4%** | 100.0% | **98.0%** | 99.6% |
| `fixed_0.75` | 0.750 | 99.8% | 0.2% | 99.6% | 100.0% | **79.4%** | 100.0% | **98.9%** | 99.6% |
| `val_q01` | 0.858 | 98.9% | 1.0% | 98.7% | 100.0% | **91.0%** | 100.0% | **100.0%** | 100.0% |
| `val_q05` | 0.900 | 94.9% | 5.1% | 95.3% | 100.0% | **97.1%** | 100.0% | **100.0%** | 100.0% |
| `temp_scaled_0.70` | 0.700 | 99.9% | 0.1% | 99.9% | 99.8% | **31.1%** | 100.0% | **86.0%** | 96.3% |

---

## 4. Key Protocol Decisions for M4 v2

1. **Default Policy Selection:**
   - **Recommended Default:** `fixed_0.70` or `fixed_0.75`.
   - **Rationale:** At $\tau = 0.70$, in-distribution coverage remains $\ge 99.8\%$ with false rejection rate $< 0.2\%$, while successfully filtering **$63.4\% - 74.4\%$ of out-of-taxonomy inputs** as UNSURE, and lifting open-set rust precision from $83\%$ to $90\%-100\%$.
   - Percentile policies (`val_q05`) set $\tau \approx 0.90$, which rejects $95\%$ of OOT samples but over-rejects external cross-source domain-shifted images where confidence hovers around $0.75-0.85$.
2. **Temperature Scaling Finding:**
   - Temperature scaling on validation with label-smoothed targets produces $T < 1.0$ ($T \approx 0.44$). This artificially sharpens logits, making out-of-distribution inputs appear *more* confident and reducing OOT rejection from $68\%$ down to $31\%$. Unscaled softmax with $\tau = 0.70$ is superior for open-set rejection when trained with label smoothing.
3. **Gating Mandate:**
   - A crop is declared `PRODUCTION-ELIGIBLE` **if and only if**:
     1. An independent cross-source test set exists.
     2. $\text{Macro-F1}_{\text{closed}} \ge 0.85$.
     3. $\text{Macro-F1}_{\text{open}} \ge 0.85$.
     4. $\min(\text{Recall}_j) \ge 0.70$ for all certified disease classes.
