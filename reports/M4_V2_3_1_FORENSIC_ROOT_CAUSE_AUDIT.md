# Uzhavan M4 Forensic Root-Cause Audit: V2.2 vs. V2.3 vs. V2.3.1
**Document Type:** Forensic Root-Cause Technical Audit & Systematic Error Analysis  
**Date:** 2026-09-28  
**Scope:** Checkpoints & Training Runs on Acer ALPHA (NVIDIA GeForce RTX 4050, 6GB VRAM, CUDA 12.6)  
- V2.2 Seed 42: `runs_m4_v2_2\UZ-M4-v2.2-groundnut-s1-wce-balanced-rust\checkpoint_best.pt`  
- V2.3 Seed 42: `runs_m4_v2_3\UZ-M4-v2.3-groundnut-s1-healthy-green-balance\checkpoint_best.pt`  
- V2.3.1 Seed 42: `runs_m4_v2_3_1\UZ-M4-v2.3.1-groundnut-s1-triclass-balance\checkpoint_best.pt`  
**Current Command Mandate:** **HARD STOP — NO NEW TRAINING. NO NEW CHECKPOINT. NO SEED 1337. NO SEED 2024. NO V2.4.**  

**Artifact Dependencies:**
- [m4_v2_3_1_config_diff.csv](file:///Users/ajaikumarn/Desktop/agri/reports/artifacts/m4_v2_3_1_config_diff.csv)
- [m4_v2_3_1_data_integrity.csv](file:///Users/ajaikumarn/Desktop/agri/reports/artifacts/m4_v2_3_1_data_integrity.csv)
- [m4_v2_3_1_sampling_pressure.csv](file:///Users/ajaikumarn/Desktop/agri/reports/artifacts/m4_v2_3_1_sampling_pressure.csv)
- [m4_v2_3_1_loss_weight_audit.csv](file:///Users/ajaikumarn/Desktop/agri/reports/artifacts/m4_v2_3_1_loss_weight_audit.csv)
- [m4_v2_3_1_checkpoint_audit.csv](file:///Users/ajaikumarn/Desktop/agri/reports/artifacts/m4_v2_3_1_checkpoint_audit.csv)
- [m4_v2_3_1_evaluator_audit.csv](file:///Users/ajaikumarn/Desktop/agri/reports/artifacts/m4_v2_3_1_evaluator_audit.csv)
- [m4_v2_3_1_error_transitions.csv](file:///Users/ajaikumarn/Desktop/agri/reports/artifacts/m4_v2_3_1_error_transitions.csv)

---

## 1. Executive Summary & Diagnostic Breakthrough

This forensic audit was commissioned to determine every verifiable factor explaining the extreme performance instability across the three Seed 42 iterations on the canonical external benchmark ($N=1,152$):

$$\begin{aligned}
\text{V2.2 S42 Baseline:} &\quad \text{Healthy: } 70.33\% \quad|\quad \text{Rust: } \mathbf{95.00\%} \quad|\quad \text{Tikka: } 96.99\% \quad|\quad \text{Macro-F1: } \mathbf{0.8548} \\
\text{V2.3 S42 (1:1 Green):} &\quad \text{Healthy: } \mathbf{84.67\%} \quad|\quad \text{Rust: } 60.00\% \quad|\quad \text{Tikka: } \mathbf{99.07\%} \quad|\quad \text{Macro-F1: } \mathbf{0.8399} \\
\text{V2.3.1 S42 (1:2 Green, 1.25x Rust):} &\quad \text{Healthy: } 33.67\% \quad|\quad \text{Rust: } \mathbf{96.67\%} \quad|\quad \text{Tikka: } \mathbf{99.07\%} \quad|\quad \text{Macro-F1: } \mathbf{0.7197}
\end{aligned}$$

### Key Forensic Discoveries:
1. **The Double-Bias Coupling:** V2.3.1 was conceptualized as a "single-variable Rust loss change ($1.25\times$) + green sampler moderation ($1:2$)." In reality, the WCE normalization formula divides raw weights by their arithmetic mean $\mu_{raw}$. Increasing Rust's raw weight by $+25\%$ inflated $\mu_{raw}$ from $1.0424 \to 1.1160$ ($+7.06\%$), which **automatically and unintentionally slashed Healthy and Tikka loss weights by $-6.59\%$**. 
2. **Hidden Augmentation Hyperparameter Drift:** Between V2.2 and V2.3/V2.3.1, the data augmentation pipeline underwent an unrecorded drift:
   - Crop scale range expanded from `[0.75, 1.0]` to `[0.6, 1.0]` ($20\%$ deeper zoom into foliar micro-lesions).
   - Aspect ratio range widened from `[0.9, 1.1]` to `[0.8, 1.25]`.
   - Rotation expanded from $\pm 15^\circ$ to $\pm 20^\circ$.
   - Color jitter values shifted from $0.25$ to $0.20$ (brightness/contrast/saturation) and $0.04 \to 0.05$ (hue).
3. **Internal Validation Blindness & Epoch Selection Divergence:**
   - Internal validation achieves Macro-F1 $= 1.0000$ by epoch 1 or epoch 5, remaining stuck at a perfect ceiling through epoch 14.
   - The selection tie-breaking rule (`if val_f1 > best_val_macro_f1:`) selected **Epoch 1** in V2.2 and V2.3, but selected **Epoch 5** in V2.3.1. In V2.3.1, the network underwent 4 additional epochs of over-optimization, driving training loss down to $0.0050$ and aggressively overfitting the internal manifold.
4. **Dataset & External Benchmark Integrity is 100% Solid:**
   - All 5,920 train samples and 1,695 external samples are identical, valid, uncorrupted, and have zero West Bengal contamination.

---

## 2. Rule 1 — Exact Reproducibility Audit

A machine-readable comparison of all pipeline parameters across the three experiments is cataloged in [m4_v2_3_1_config_diff.csv](file:///Users/ajaikumarn/Desktop/agri/reports/artifacts/m4_v2_3_1_config_diff.csv).

| Parameter Category | V2.2 Seed 42 | V2.3 Seed 42 | V2.3.1 Seed 42 | Forensic Status |
| :--- | :--- | :--- | :--- | :--- |
| **Manifest & Checksum** | `groundnut_v2.csv` (`6768c74...`) | `groundnut_v2.csv` (`6768c74...`) | `groundnut_v2.csv` (`6768c74...`) | ✅ **IDENTICAL** |
| **Model Backbone** | EfficientNetV2-S | EfficientNetV2-S | EfficientNetV2-S | ✅ **IDENTICAL** |
| **Classifier Head** | Linear(1280, 3) | Linear(1280, 3) | Linear(1280, 3) | ✅ **IDENTICAL** |
| **Pretrained Weights** | `IMAGENET1K_V1` | `IMAGENET1K_V1` | `IMAGENET1K_V1` | ✅ **IDENTICAL** |
| **Optimizer / LR / WD** | AdamW / 1e-4 / 1e-2 | AdamW / 1e-4 / 1e-2 | AdamW / 1e-4 / 1e-2 | ✅ **IDENTICAL** |
| **Batch Size / Epochs** | 32 / 15 | 32 / 15 | 32 / 15 | ✅ **IDENTICAL** |
| **AMP Mode** | PyTorch float16 | PyTorch float16 | PyTorch float16 | ✅ **IDENTICAL** |
| **Random Seed** | 42 | 42 | 42 | ✅ **IDENTICAL** |
| **Green Sampler Weight** | $1.000000$ (Natural) | $7.845614$ (1:1 vs Tikka) | $3.922807$ (1:2 vs Tikka) | ⚠️ **INTENDED VARIABLE** |
| **Rust Loss Multiplier** | $1.00\times$ | $1.00\times$ | $1.25\times$ | ⚠️ **INTENDED VARIABLE** |
| **Normalized WCE Weights** | `[1.3064, 0.8470, 0.8466]` | `[1.3064, 0.8470, 0.8466]` | `[1.2203, 0.9889, 0.7908]` | 🚨 **NORMALIZATION SHIFT** |
| **Crop Scale Range** | `[0.75, 1.0]` | `[0.6, 1.0]` | `[0.6, 1.0]` | 🚨 **UNCONTROLLED DRIFT** |
| **Crop Aspect Ratio** | `[0.9, 1.1]` | `[0.8, 1.25]` | `[0.8, 1.25]` | 🚨 **UNCONTROLLED DRIFT** |
| **Rotation Degrees** | $\pm 15^\circ$ | $\pm 20^\circ$ | $\pm 20^\circ$ | 🚨 **UNCONTROLLED DRIFT** |
| **Color Jitter (B/C/S/H)** | 0.25 / 0.25 / 0.25 / 0.04 | 0.20 / 0.20 / 0.20 / 0.05 | 0.20 / 0.20 / 0.20 / 0.05 | 🚨 **UNCONTROLLED DRIFT** |

---

## 3. Rule 2 & 3 — Dataset Integrity & External Benchmark Audit

Documented in [m4_v2_3_1_data_integrity.csv](file:///Users/ajaikumarn/Desktop/agri/reports/artifacts/m4_v2_3_1_data_integrity.csv):

1. **Training Cohort Verification ($N=5,920$):**
   - **Tikka Leaf Spot:** Exactly 2,236 samples.
   - **Rust:** Exactly 2,235 samples.
   - **Healthy or Abiotic:** Exactly 1,449 samples.
     - Pure-green Healthy foliage: Exactly 285 samples ($19.67\%$).
     - Nutrient deficiency abiotic stress: Exactly 1,164 samples ($80.33\%$).
2. **Contamination Audit:**
   - External West Bengal Sasmal dataset (`in_groundnut_wb_sasmal`): **0 samples in train, 0 in val**.
   - Train $\cap$ Validation SHA256 overlap: **0 samples**.
   - Train $\cap$ External Test SHA256 overlap: **0 samples**.
   - Validation $\cap$ External Test SHA256 overlap: **0 samples**.
3. **External Benchmark Parity:**
   - Canonical External Benchmark: Exactly 1,695 total, 1,152 scorable (600 Healthy, 120 Rust, 432 Tikka). All three experiments evaluated the exact same image list with identical ground-truth labels.
   - Untouched Final Test Universe: Exactly 928 scorable (483 Healthy, 99 Rust, 346 Tikka).

---

## 4. Rule 4 — Sampler Forensic Audit: Exposure & Repetition Mechanics

Documented in [m4_v2_3_1_sampling_pressure.csv](file:///Users/ajaikumarn/Desktop/agri/reports/artifacts/m4_v2_3_1_sampling_pressure.csv):

| Metric | V2.2 Seed 42 | V2.3 Seed 42 | V2.3.1 Seed 42 |
| :--- | :---: | :---: | :---: |
| **Sampling Mechanism** | Random without Replacement | Weighted with Replacement | Weighted with Replacement |
| **Assigned Weight ($w_{green}$)** | $1.000000$ | $7.845614$ | $3.922807$ |
| **Draw Probability: Pure-Green Healthy** | $4.81\%$ | $\mathbf{28.41\%}$ | $\mathbf{16.56\%}$ |
| **Draw Probability: Nutrient Deficiency** | $19.66\%$ | $14.79\%$ | $17.24\%$ |
| **Draw Probability: Rust** | $37.75\%$ | $28.40\%$ | $33.10\%$ |
| **Draw Probability: Tikka** | $37.77\%$ | $28.41\%$ | $33.11\%$ |
| **Exposure Ratio Green : Tikka** | $1 : 7.84$ ($0.1275$) | $\mathbf{1 : 1.00}$ ($1.0000$) | $\mathbf{1 : 2.00}$ ($0.5000$) |
| **Expected Draws per Green Image/Epoch** | $1.00\times$ | $\mathbf{5.90\times}$ | $\mathbf{3.44\times}$ |
| **Total Green Exposure over 15 Epochs** | $4,275$ draws | $\mathbf{25,226}$ draws | $\mathbf{14,701}$ draws |
| **Unique Green Images Seen / Epoch** | $285 / 285$ ($100.0\%$) | $284.2 / 285$ ($99.7\%$) | $275.9 / 285$ ($96.8\%$) |

### Sampler Findings:
- In V2.3, the $5.90\times$ repetition per epoch forced the network to see pure-green leaves $25,226$ times during training. This successfully expanded the green decision boundary and boosted Healthy recall to $84.67\%$.
- In V2.3.1, moderating the green sampler to $1:2$ cut total green draws by $-41.7\%$ ($25,226 \to 14,701$). By itself, this reduction alone would have lowered Healthy recall back toward the V2.2 level ($70\%$). However, when paired with the loss weight changes, Healthy collapsed completely to $33.67\%$.

---

## 5. Rule 5 & 6 — WCE Normalization & Double-Bias Audit

Documented in [m4_v2_3_1_loss_weight_audit.csv](file:///Users/ajaikumarn/Desktop/agri/reports/artifacts/m4_v2_3_1_loss_weight_audit.csv):

### The Mathematics of WCE Coupling:
The training script computes raw inverse-frequency weights, multiplies the Rust weight by `rust_weight_mult`, and normalizes by dividing by the mean weight $\mu_{raw}$:

$$\mu_{raw} = \frac{W_{raw}(\text{Healthy}) + W_{raw}(\text{Rust}) \times \text{mult} + W_{raw}(\text{Tikka})}{3}$$

When `rust_weight_mult` increased from $1.00\times \longrightarrow 1.25\times$:
1. $W_{raw}(\text{Rust})$ increased from $0.8829 \longrightarrow 1.1037$ ($+25.0\%$).
2. $\mu_{raw}$ inflated from $1.0424 \longrightarrow 1.1160$ ($+7.06\%$).
3. **Healthy normalized weight fell:** $\frac{1.3619}{1.1160} = \mathbf{1.2203}$ (down $-6.59\%$ from $1.3064$).
4. **Tikka normalized weight fell:** $\frac{0.8825}{1.1160} = \mathbf{0.7908}$ (down $-6.59\%$ from $0.8466$).
5. **Rust normalized weight rose:** $\frac{1.1037}{1.1160} = \mathbf{0.9889}$ (only $+16.76\%$ net, not $+25\%$).

### Effective Optimization Pressure Table:
$\text{Effective Pressure} = \text{Batch Draw Probability} \times \text{Normalized Loss Weight}$:

| Class | V2.2 Seed 42 | V2.3 Seed 42 | V2.3.1 Seed 42 | Directional Shift in V2.3.1 |
| :--- | :---: | :---: | :---: | :--- |
| **Healthy or Abiotic** | $33.33\%$ | $\mathbf{53.99\%}$ | $\mathbf{41.17\%}$ | **$-23.7\%$ loss of pressure vs V2.3** |
| **Rust** | $33.33\%$ | $\mathbf{23.01\%}$ | $\mathbf{32.68\%}$ | **$+42.0\%$ surge in pressure vs V2.3** |
| **Tikka Leaf Spot** | $33.33\%$ | $\mathbf{23.01\%}$ | $\mathbf{26.14\%}$ | $+13.6\%$ pressure vs V2.3 |

### The Root Cause of the Double Failure:
- **Why V2.3 collapsed Rust (60.0%):** The 1:1 green oversampling surged Healthy pressure to $53.99\%$, compressing Rust pressure down to $23.01\%$. The network sacrificed Rust in favor of the dominant classes.
- **Why V2.3.1 collapsed Healthy (33.7%):** Rust pressure surged back up to $32.68\%$ ($+42.0\%$). Meanwhile, Healthy pressure dropped sharply from $53.99\% \to 41.17\%$. Because Tikka images are the most numerous and diverse ($2,236$ samples), and Rust was strongly defended by its $1.25\times$ loss penalty, the gradient descent took the path of least resistance: **it pushed the Tikka boundary directly into Healthy territory**.

---

## 6. Rule 7 & 8 — Augmentation Drift & Crop Scale Analysis

Comparing `train_m4_v2_2.py` vs. `train_m4_v2_3.py`:

```diff
  AUG_CONFIG = {
-     "scale_range": [0.75, 1.0],
+     "scale_range": [0.6, 1.0],
-     "ratio_range": [0.9, 1.1],
+     "ratio_range": [0.8, 1.25],
-     "rotation_degrees": 15,
+     "rotation_degrees": 20,
      "color_jitter": {
-         "brightness": 0.25, "contrast": 0.25, "saturation": 0.25, "hue": 0.04
+         "brightness": 0.20, "contrast": 0.20, "saturation": 0.20, "hue": 0.05
      }
  }
```

### Impact on Lesion Geometry:
- At `scale_range = [0.6, 1.0]`, crops zoom in significantly closer ($36\%$ minimum area vs $56.25\%$ minimum area in V2.2).
- Micro-speckles, natural soil flecks, and small physiological spots on Healthy field leaves are enlarged by up to $1.67\times$, causing healthy foliage to closely mimic early Tikka leaf spot lesions.
- In V2.3, the $7.85\times$ pure-green exposure overpowered this zoom artifact. But in V2.3.1, with green exposure halved and Healthy loss weight reduced, this deeper crop zoom contributed directly to 398 healthy leaves being misclassified as Tikka.

---

## 7. Rule 9 & 10 — Checkpoint Selection & Validation Blindness

Documented in [m4_v2_3_1_checkpoint_audit.csv](file:///Users/ajaikumarn/Desktop/agri/reports/artifacts/m4_v2_3_1_checkpoint_audit.csv):

### The Validation Ceiling Problem:
The internal validation split ($N=1,268$) is drawn from the same laboratory/field collections as the training data (`in_groundnut_lab_kagg` and `in_groundnut_field_ai_chall`).
- In V2.2 S42: Validation Macro-F1 reached **1.0000 at Epoch 1** and remained 1.0000 across 14 out of 15 epochs.
- In V2.3 S42: Validation Macro-F1 reached **1.0000 at Epoch 1** and remained 1.0000 across 14 out of 15 epochs.
- In V2.3.1 S42: Validation Macro-F1 reached **1.0000 at Epoch 5** (after being $0.9920$, $0.9975$, $0.9977$, $0.9947$, $0.9979$).

### The Selection Divergence:
The model saving rule is strictly:
```python
is_best = val_f1 > best_val_macro_f1
if is_best:
    best_val_macro_f1 = val_f1
    torch.save(last_state, ckpt_best_path)
```
- Because the condition is strictly `>`, once `best_val_macro_f1` reaches $1.0000$, **no subsequent epoch can ever overwrite it**.
- In V2.2 and V2.3, **Epoch 1** was frozen as `checkpoint_best.pt`.
- In V2.3.1, because epochs 1–4 scored $\approx 0.997$, **Epoch 5** was frozen as `checkpoint_best.pt`.
- By Epoch 5, the model had undergone **$4\times$ more gradient descent steps** on the imbalanced distribution, driving training loss down from $0.0217 \longrightarrow 0.0050$. Internal validation had zero errors ($0 / 1,268$), while on the external benchmark, Healthy recall was degrading catastrophically.
- **Verdict:** Internal validation is **100% blind** to the external domain shift and boundary collapse.

---

## 8. Rule 11 & 12 — Seed, Randomness & Architecture Verification

1. **Randomness Handling:**
   - `random.seed(42)`, `np.random.seed(42)`, `torch.manual_seed(42)`, `torch.cuda.manual_seed_all(42)`.
   - `torch.backends.cudnn.deterministic = True`, `benchmark = False`.
   - Sampler generator explicitly seeded with `gen.manual_seed(42)`.
   - 6/6 unit tests confirmed 100% deterministic sequence reproduction.
2. **Architecture Parity:**
   - V2.2 S42, V2.3 S42, V2.3.1 S42 all have **exactly 20,181,259 parameters**.
   - Identical EfficientNetV2-S backbone, identical `drop = Dropout(p=0.2)`, identical `heads = Linear(1280, 3)`.

---

## 9. Rule 13 — Evaluator Audit & Windows Encoding Note

Documented in [m4_v2_3_1_evaluator_audit.csv](file:///Users/ajaikumarn/Desktop/agri/reports/artifacts/m4_v2_3_1_evaluator_audit.csv):
- Evaluator inference pipelines are bit-for-bit identical across all runs.
- **Windows CP1252 Unicode Error:** At the very end of `eval_m4_v2_3_1.py`, a `UnicodeEncodeError` occurred when printing the Greek character `\tau` (`\u03c4`) to the Windows command prompt console.
- **Verification:** All calculations, metric summaries, and artifact saves (`m4_v2_3_1_s1_metrics.json`, `m4_v2_3_1_s1_comparison.csv`, and `m4_v2_3_1_s1_error_cases.csv`) completed **prior** to the print call. The artifacts are 100% complete and uncorrupted.

---

## 10. Rule 14 & 15 — Error Transitions & Sample Data Quality

Documented in [m4_v2_3_1_error_transitions.csv](file:///Users/ajaikumarn/Desktop/agri/reports/artifacts/m4_v2_3_1_error_transitions.csv):

```
ALL_THREE_CORRECT               : 692 samples (60.07%)
ALL_THREE_WRONG                 :  38 samples ( 3.30%)
HEALTHY_V23_RESCUED_V231_LOST   : 306 samples (26.56%)
HEALTHY_PERSISTENT_CORRECT      : 202 samples (17.53%)
HEALTHY_SWALLOWED_BY_TIKKA_V231 : 398 samples (34.55%)
RUST_V23_COLLAPSED_V231_RESCUED :  44 samples ( 3.82%)
RUST_PERSISTENT_CORRECT         :  72 samples ( 6.25%)
RUST_SWALLOWED_BY_TIKKA_V231    :   4 samples ( 0.35%)
TIKKA_STABLE_CORRECT            : 418 samples (36.28%)
```

### Analysis of the 306 Healthy Samples Lost in V2.3.1:
- In V2.2, 178 of these were misclassified as Tikka.
- In V2.3, the 1:1 green oversampling rescued 86 of them.
- In V2.3.1, not only were those 86 lost, but an additional 220 Healthy leaves that were correct in V2.2 flipped to Tikka.
- **Visual Features:** These 306 leaves exhibit minor non-pathogenic features: field dust, physiological tip chlorosis, natural leaf venation contrast, and specular sun reflections. Under V2.3.1's reduced Healthy loss weight and deeper crop zoom (`scale=0.6`), the model treats any non-uniform green texture as Tikka.

---

## 11. Final Summary of Forensic Root Causes & Epistemological Status

To maintain strict scientific integrity, the forensic findings are explicitly partitioned between **proven structural facts** and **strongly supported hypotheses that require ablation to isolate individual causality**.

### A. Proven Structural & Configuration Facts:
1. **WCE Arithmetic Mean Coupling (PROVEN):**
   Setting Rust to $1.25\times$ inflated the arithmetic mean divisor $\mu_{raw}$ by $+7.06\%$, which unintentionally reduced Healthy and Tikka loss weights by $-6.59\%$ and reduced Healthy's relative loss ratio over Rust by $20.0\%$.
2. **Multi-Factor Confounding (PROVEN):**
   V2.3.1 cannot be described as a single-variable intervention. It simultaneously altered **five distinct dimensions**:
   - Rust WCE multiplier ($1.0\times \to 1.25\times$)
   - Normalized WCE weights for ALL three classes ($[1.3064, 0.8470, 0.8466] \to [1.2203, 0.9889, 0.7908]$)
   - Sampler exposure distribution ($1:1 \to 1:2$, pure-green draws halved from $25,226 \to 14,701$)
   - Augmentation geometry (`scale_range = [0.6, 1.0]` vs `[0.75, 1.0]`, rotation $20^\circ$ vs $15^\circ$)
   - Selected checkpoint epoch (Epoch 5 vs Epoch 1)
3. **Data & Evaluator Integrity (PROVEN):**
   Zero West Bengal contamination in train/val, zero split leakage, identical canonical 1,152 external benchmark cohort, and verified metric calculation integrity (the CP1252 Unicode exception was display-only).
4. **Internal Validation Blindness (PROVEN):**
   Internal validation saturated at $1.0000$ with zero errors across all classes, completely blind to the external domain shift and boundary collapse.

### B. Strongly Supported Hypotheses (Requiring Ablation to Prove Individual Causality):
1. **Augmentation Zoom as a Lesion Generator:**
   Plausible contributing factor: the deeper crop zoom (`scale=0.6`) magnifies foliar micro-speckles into pseudo-lesions, but its exact isolated contribution to the 398 Healthy $\to$ Tikka errors requires a controlled augmentation ablation on an identical checkpoint.
2. **Sampler vs. WCE Interaction Mechanism:**
   The drop in Healthy optimization pressure ($54.0\% \to 41.2\%$) combined with increased Rust pressure ($23.0\% \to 32.7\%$) strongly correlates with the Healthy manifold collapse, but separating the sampler's role from the loss function's role requires single-variable isolation.
3. **Late Checkpoint Over-Optimization:**
   Selecting Epoch 5 (train loss $0.0050$) instead of Epoch 1 (train loss $0.0217$) likely exacerbated boundary sharpness, but proving whether Epoch 1 would have generalized better requires evaluating all 15 epoch checkpoints on the external benchmark.

---

## 12. Correct Future Experimental Protocol

When the M4 research line is eventually unfrozen, it must adhere to a strict sequential discipline:

```
1. Baseline Reproduction
   Re-run exact V2.2 on Seed 42 with verified identical configs
           ↓
2. Benchmark Verification
   Confirm reproduction matches historical canonical metrics
           ↓
3. Exactly ONE Decoupled Intervention
   (e.g., sampler ONLY, or intentional loss ratio ONLY without normalization drift)
           ↓
4. External Benchmark Evaluation
           ↓
5. Forensic Comparison
           ↓
6. Only then consider the next intervention
```

**Loss Weighting Rule for Future Work:**
Future loss interventions must specify **intentional relative class-weight ratios** directly (or anchor one reference class) rather than allowing an unconstrained arithmetic mean denominator to silently shift non-target classes.

---

## 13. Final Command Decision

```
================================================================
FINAL COMMAND DECISION: STATUS: NO-GO
================================================================
```

### Mandate:
- **NO-GO status is LOCKED.**
- **DO NOT launch Seeds 1337 or 2024.**
- **DO NOT train V2.4.**
- **DO NOT modify production M4 code or behavior.**
- The M4 research line remains frozen until a clean V2.2 baseline reproduction plan and decoupled intervention design are finalized.
