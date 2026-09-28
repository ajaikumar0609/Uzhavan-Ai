# Uzhavan M4 V2.3.1 — Tri-Class Boundary Balance Specification
**Experiment Series:** M4 V2.3.1  
**Experiment Name:** `UZ-M4-v2.3.1-groundnut-s1-triclass-balance`  
**Execution Scope:** Seed 42 ONLY (No multi-seed replication until Seed 42 passes all gates)  
**Parent Baseline:** M4 V2.3 Seed 42 (`UZ-M4-v2.3-groundnut-s1-healthy-green-balance`)  
**Historical Control:** M4 V2.2 Seed 42 (`UZ-M4-v2.2-groundnut-s1-wce`)  

---

## 1. Context & Motivation

The empirical error audit of M4 V2.3 Seed 42 ([reports/M4_V2_3_S1_ERROR_AUDIT.md](file:///Users/ajaikumarn/Desktop/agri/reports/M4_V2_3_S1_ERROR_AUDIT.md)) identified:
1. **Target Achieved for Healthy Foliage:** Pure-green oversampling successfully re-established the green leaf manifold, driving Healthy recall from $70.33\% \to 84.67\%$ (+14.34 pts) and cutting Healthy $\to$ Tikka errors by $48.3\%$ ($178 \to 92$).
2. **Catastrophic Unilateral Collapse of Rust:** Rust recall collapsed from $95.00\% \to 60.00\%$ (-35.00 pts), dropping from 114 to 72 correct predictions.
3. **Rust $\to$ Tikka Error Absorption:** Out of 48 Rust errors, $47$ ($97.9\%$) were misclassified as **Tikka Leaf Spot**, while Rust $\to$ Healthy was virtually non-existent ($1 / 120, 0.83\%$).
4. **Failure of Confidence Safety Gate:** $74.5\%$ of the new Rust $\to$ Tikka errors had high confidence ($\ge 0.70$, median $0.795$), bypassing the $\tau=0.70$ selective classification rejection gate.

**Objective of V2.3.1:**  
Recover Rust recall ($\ge 90\%$) while retaining the Healthy recall gains ($\ge 80\%$) and high Tikka recall ($\ge 96\%$) to achieve a balanced Macro-F1 $\ge 0.86$.

---

## 2. Controlled Two-Variable Intervention

To address the boundary distortion without modifying the underlying architecture or training hyperparameters, V2.3.1 applies exactly **two controlled adjustments**:

### Intervention 1: Moderated Pure-Green Healthy Oversampling ($1:1 \longrightarrow 1:2$)
In V2.3, the 285 pure-green Healthy images were oversampled at $w_{green} = 2236 / 285 \approx 7.845614$, forcing a $1:1$ exposure ratio against the 2,236 Tikka images. This over-expanded the green feature manifold and compressed the non-Tikka disease logit space.

In V2.3.1, the exposure ratio of Pure-Green Healthy to Tikka is moderated to **$1:2$ ($0.500000$)**:
$$\begin{aligned}
N_{tikka} &= 2,236 \\
N_{green} &= 285 \\
\text{Target Ratio} &= \frac{\text{Exposure}_{green}}{\text{Exposure}_{tikka}} = \frac{1}{2} = 0.50 \\
\text{Total Weight}(\text{Tikka}) &= N_{tikka} \times 1.0 = 2,236.0 \\
\text{Total Weight}(\text{Green}) &= 0.50 \times 2,236.0 = 1,118.0 \\
w_{green} &= \frac{1,118.0}{285} = \frac{2,236}{2 \times 285} = \mathbf{3.9228070175...} \approx \mathbf{3.922807}
\end{aligned}$$

**Analytical Training Exposure Distribution:**
| Category | Sample Count ($N$) | Assigned Weight | Total Weight Sum | Batch Draw Probability | Relative Exposure to Tikka |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Pure-Green Healthy** | 285 | $3.922807$ | $1,118.0$ | **16.5556%** | **0.500000 (1:2)** |
| **Tikka Leaf Spot** | 2,236 | $1.000000$ | $2,236.0$ | **33.1112%** | **1.000000 (Reference)** |
| **Rust** | 2,235 | $1.000000$ | $2,235.0$ | **33.0964%** | **0.999553 (~1:1)** |
| **Nutrient Deficiency** | 1,164 | $1.000000$ | $1,164.0$ | **17.2368%** | **0.520572** |
| **Total** | **5,920** | — | **6,753.0** | **100.00%** | — |

---

### Intervention 2: Asymmetric Rust Loss Weight Multiplier ($1.0\times \longrightarrow 1.25\times$)
In V2.3, the loss function was standard unpenalized WCE ($\text{rust\_weight\_mult} = 1.0$). Without explicit loss penalties, the model allowed Tikka to freely absorb boundary-ambiguous Rust lesions.

In V2.3.1, a **$1.25\times$ WCE loss multiplier** is re-introduced for Rust (grounded in M4 V2.1 empirical findings where $1.25\times$ produced $95.8\%$ Rust recall):
$$\begin{aligned}
W_{raw}(c) &= \frac{N_{total}}{3 \times N_c} \\
W_{raw}(\text{Healthy}) &= \frac{5,920}{3 \times 1,449} \approx 1.36186 \\
W_{raw}(\text{Rust}) &= \left(\frac{5,920}{3 \times 2,235}\right) \times 1.25 \approx 0.88292 \times 1.25 \approx 1.10365 \\
W_{raw}(\text{Tikka}) &= \frac{5,920}{3 \times 2,236} \approx 0.88253 \\
\mu_W &= \frac{1.36186 + 1.10365 + 0.88253}{3} \approx 1.11601 \\
W_{norm}(\text{Healthy}) &= \frac{1.36186}{1.11601} \approx \mathbf{1.2203} \\
W_{norm}(\text{Rust}) &= \frac{1.10365}{1.11601} \approx \mathbf{0.9889} \\
W_{norm}(\text{Tikka}) &= \frac{0.88253}{1.11601} \approx \mathbf{0.7908}
\end{aligned}$$

---

## 3. Invariant Hyperparameters & Training Controls

| Hyperparameter | Value | Status |
| :--- | :--- | :--- |
| **Model Architecture** | `efficientnet_v2_s` (ImageNet-1k pretrained, dropout 0.2) | Strictly Invariant |
| **Input Resolution** | 256x256 resize $\to$ 224x224 RandomResizedCrop | Strictly Invariant |
| **Optimizer** | `AdamW` ($\text{lr} = 10^{-4}$, $\text{weight\_decay} = 10^{-2}$) | Strictly Invariant |
| **Batch Size** | 32 | Strictly Invariant |
| **Epochs** | 15 | Strictly Invariant |
| **Mixed Precision** | PyTorch AMP `float16` | Strictly Invariant |
| **Data Augmentations** | Flips, rotations ($\pm 20^\circ$), ColorJitter, FieldShadow ($p=0.35$), GaussianBlur ($p=0.20$) | Strictly Invariant |
| **Dataset Manifest** | `m4_v2/manifests/groundnut_v2.csv` (SHA256: `6768c74...`) | Strictly Invariant |
| **Random Seed** | **42 ONLY** | Strictly Invariant |

---

## 4. Evaluation Protocol & Primary Success Targets

Evaluated on:
1. **Canonical Historical Benchmark ($N=1,152$ scorable samples)**
2. **Untouched Final External Test Universe ($N=928$ scorable samples)**

### Primary Success Targets:
- **Healthy Recall:** $\ge 80.0\%$ (vs $70.33\%$ V2.2, $84.67\%$ V2.3)
- **Rust Recall:** $\ge 90.0\%$ (vs $95.00\%$ V2.2, $60.00\%$ V2.3)
- **Tikka Recall:** $\ge 96.0\%$ (vs $96.99\%$ V2.2, $99.07\%$ V2.3)
- **Macro-F1 (Canonical):** $\ge 0.8600$ (vs $0.8548$ V2.2, $0.8399$ V2.3)

### Decision Tree Following V2.3.1 Seed 42:
$$\begin{array}{ccc}
\text{All 4 Targets Met?} & \longrightarrow \text{YES} \longrightarrow & \text{Launch Seeds 1337 and 2024 for Multi-Seed Replication} \\
& \longrightarrow \text{NO} \longrightarrow & \text{STOP. Re-audit failure mode; do NOT replicate.}
\end{array}$$
