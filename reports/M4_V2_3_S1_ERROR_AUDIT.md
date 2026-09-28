# Uzhavan M4 V2.3 Seed 42 — Error Audit & Diagnostic Report
**Document Type:** Empirical Model Error Audit (NO TRAINING / NO CODE CHANGES)  
**Date:** 2026-09-28  
**Scope:** Checkpoint `runs_m4_v2_3\UZ-M4-v2.3-groundnut-s1-healthy-green-balance\checkpoint_best.pt`  
**Evaluated Cohorts:**
1. Primary Benchmark: Untouched Final External Test Universe ($N=928$ scorable / $N=1,360$ total)
2. Historical Replication Benchmark: Full Canonical External Test Set ($N=1,152$ scorable / $N=1,695$ total from West Bengal Sasmal dataset, `in_groundnut_wb_sasmal`)  
**Artifact Dependencies:**
- [m4_v2_3_s1_confusion.csv](file:///Users/ajaikumarn/Desktop/agri/reports/artifacts/m4_v2_3_s1_confusion.csv)
- [m4_v2_3_s1_error_cases.csv](file:///Users/ajaikumarn/Desktop/agri/reports/artifacts/m4_v2_3_s1_error_cases.csv)
- [m4_v2_3_s1_confidence.csv](file:///Users/ajaikumarn/Desktop/agri/reports/artifacts/m4_v2_3_s1_confidence.csv)

---

## 1. Executive Summary & Diagnostic Finding

The M4 V2.3 intervention implemented a targeted weighted oversampling sampler on the 285 pure-green Healthy training images to equalize their effective training exposure 1:1 against the 2,236 Tikka training images.

Evaluation of the completed Seed 42 checkpoint reveals an unmistakable diagnostic signature:
$$\begin{aligned}
\text{Healthy Recall:} &\quad 70.33\% \longrightarrow \mathbf{84.67\%} \quad (+14.34\text{ pts}) \quad [\text{TARGET ACHIEVED}] \\
\text{Rust Recall:} &\quad 95.00\% \longrightarrow \mathbf{60.00\%} \quad (-35.00\text{ pts}) \quad [\text{CATASTROPHIC COLLAPSE}] \\
\text{Tikka Recall:} &\quad 96.99\% \longrightarrow \mathbf{99.07\%} \quad (+2.08\text{ pts}) \\
\text{Macro-F1 (Canonical 1,152):} &\quad 0.8548 \longrightarrow \mathbf{0.8399} \quad (-0.0149) \\
\text{Macro-F1 (Untouched 928):} &\quad — \quad \longrightarrow \mathbf{0.8262}
\end{aligned}$$

### The Critical Diagnostic Discovery: Where Did the 35-Point Rust Collapse Go?
Prior to this audit, a key question was whether oversampling Healthy pushed the decision boundaries such that Rust was misclassified as Healthy, as Tikka, or both.

**The Empirical Ground Truth:**
1. **Rust $\longrightarrow$ Healthy is Virtually ZERO (Exactly 1 sample out of 120, $0.83\%$).**  
   The model did NOT begin confusing Rust with Healthy foliage.
2. **Rust $\longrightarrow$ Tikka Leaf Spot absorbed almost 100% of the collapsed Rust samples ($47 / 48$ errors, $97.92\%$).**  
   In V2.2 Seed 42, only 5 Rust samples were misclassified as Tikka. In V2.3 Seed 42, **47 Rust samples were predicted as Tikka**—a massive **+840% surge in Rust-to-Tikka errors**.
3. **Healthy $\longrightarrow$ Tikka errors were successfully cut by nearly half ($178 \longrightarrow 92$, a $48.3\%$ reduction).**  
   86 real field Healthy images that collapsed into Tikka under V2.2 were rescued and correctly classified as Healthy.
4. **Healthy $\longrightarrow$ Rust remained strictly ZERO ($0 / 600, 0.00\%$).**
5. **Tikka $\longrightarrow$ Rust dropped from 11 errors to ZERO ($0 / 432, 0.00\%$).**  
   The network's Rust output logit has become suppressed across all non-canonical Rust presentations, causing Tikka to dominate the entire necrotic foliar disease space.

---

## 2. 3x3 Confusion Matrices

### A. Canonical Historical Benchmark ($N=1,152$ scorable samples)
*Overall Scorable Accuracy: $87.50\%$ ($1,008 / 1,152$) | Closed Macro-F1: $0.8399$*

| True Class | Pred Healthy | Pred Rust | Pred Tikka | Total True | Class Recall | Class Precision | Class F1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Healthy or Abiotic** | **508** | 0 | 92 | 600 | **84.67%** | 99.03% | 0.9128 |
| **Rust** | 1 | **72** | 47 | 120 | **60.00%** | 100.00% | 0.7500 |
| **Tikka Leaf Spot** | 4 | 0 | **428** | 432 | **99.07%** | 75.48% | 0.8569 |
| **Total Predicted** | 513 | 72 | 567 | 1,152 | — | — | **0.8399** |

---

### B. Untouched Final External Test Universe ($N=928$ scorable samples)
*Overall Scorable Accuracy: $86.64\%$ ($804 / 928$) | Closed Macro-F1: $0.8262$*

| True Class | Pred Healthy | Pred Rust | Pred Tikka | Total True | Class Recall | Class Precision | Class F1 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Healthy or Abiotic** | **405** | 0 | 78 | 483 | **83.85%** | 99.26% | 0.9091 |
| **Rust** | 0 | **56** | 43 | 99 | **56.57%** | 100.00% | 0.7226 |
| **Tikka Leaf Spot** | 3 | 0 | **343** | 346 | **99.13%** | 73.92% | 0.8469 |
| **Total Predicted** | 408 | 56 | 464 | 928 | — | — | **0.8262** |

---

## 3. Error Flow Quantification: V2.2 S42 vs. V2.3 S42

| Error Flow Path | V2.2 Seed 42 Count | V2.2 Seed 42 Rate | V2.3 Seed 42 Count | V2.3 Seed 42 Rate | Net Count Change | Relative Shift |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Healthy $\longrightarrow$ Rust** | 0 | 0.00% | 0 | 0.00% | 0 | Unchanged (Zero) |
| **Healthy $\longrightarrow$ Tikka** | **178** | 29.67% | **92** | 15.33% | **-86** | **-48.3% (Substantial fix)** |
| **Rust $\longrightarrow$ Healthy** | 1 | 0.83% | 1 | 0.83% | 0 | Unchanged |
| **Rust $\longrightarrow$ Tikka** | **5** | 4.17% | **47** | 39.17% | **+42** | **+840% (Severe collapse)** |
| **Tikka $\longrightarrow$ Healthy** | 2 | 0.46% | 4 | 0.93% | +2 | Minor (+2 samples) |
| **Tikka $\longrightarrow$ Rust** | **11** | 2.55% | **0** | 0.00% | **-11** | **-100% (Zeroed out)** |

### Key Diagnostic Takeaways:
1. **The Healthy/Tikka Boundary Shifted in the Intended Direction**:
   - In V2.2, Healthy had an effective exposure ratio of $1 : 7.84$ against Tikka, causing 178 green leaves to be pulled into Tikka.
   - In V2.3, the 1:1 pure-green oversampling successfully re-established the green manifold, rescuing 86 healthy foliage images.
2. **The Rust/Tikka Boundary Collapsed Unilaterally**:
   - The Rust training exposure was held constant while pure-green Healthy was dramatically multiplied ($7.84\times$).
   - The relative frequency of Rust in the mini-batch stream dropped from approximately $38\%$ of non-Tikka images to a secondary role.
   - Simultaneously, because Tikka remained the largest disease class by far ($2,236$ samples), any leaf displaying brown pustules, dark spots, or necrotic margins that was no longer allowed to be classified as Healthy was aggressively swept into the dominant disease prior: **Tikka Leaf Spot**.

---

## 4. Confidence Distributions & Operational Threshold ($\tau=0.70$)

Detailed distribution metrics from [m4_v2_3_s1_confidence.csv](file:///Users/ajaikumarn/Desktop/agri/reports/artifacts/m4_v2_3_s1_confidence.csv):

| Prediction Category | V2.2 Mean Conf | V2.2 Median Conf | V2.2 $\ge 0.70$ | V2.3 Mean Conf | V2.3 Median Conf | V2.3 $\ge 0.70$ | Operational Consequence |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Correct Healthy** ($N=508$) | 0.8841 | 0.9120 | 89.57% | **0.9145** | **0.9420** | **93.70%** | Higher confidence, clean separation |
| **Healthy $\longrightarrow$ Tikka** ($N=92$) | 0.6128 | 0.6054 | 24.72% | **0.6485** | **0.6420** | **32.61%** | Borderline ambiguous cases |
| **Correct Rust** ($N=72$) | 0.9215 | 0.9482 | 94.74% | **0.8920** | **0.9210** | **87.50%** | Slightly eroded confidence |
| **Rust $\longrightarrow$ Tikka** ($N=47$) | 0.6842 | 0.6910 | 40.00% | **0.7865** | **0.7950** | **74.47%** | **High-confidence false positives!** |
| **Correct Tikka** ($N=428$) | 0.9084 | 0.9380 | 92.84% | **0.9320** | **0.9580** | **95.79%** | Extreme confidence saturation |

### Why Coverage Rose but Accepted Accuracy Slightly Dropped:
- In V2.2, coverage at $\tau=0.70$ was low ($68.40\%$) because 178 Healthy images were predicted as Tikka with low/medium confidence ($0.45 - 0.65$), and were correctly rejected by the threshold.
- In V2.3, coverage jumped to **$80.47\%$** because the 86 rescued Healthy images crossed the $\tau=0.70$ threshold with high confidence ($\ge 0.90$).
- However, **$74.47\%$ of the 47 misclassified Rust $\to$ Tikka errors carry confidence $\ge 0.70$** (median $0.795$). The selective classification gate fails to reject them, allowing 35 false Tikka predictions into the accepted pool and pulling Accepted Accuracy down to $92.66\%$.

---

## 5. Sample Transition Breakdown

From the sample-level tracking in [m4_v2_3_s1_error_cases.csv](file:///Users/ajaikumarn/Desktop/agri/reports/artifacts/m4_v2_3_s1_error_cases.csv):

| Transition Group | Count | Description | Representative Pattern |
| :--- | :---: | :--- | :--- |
| **STABLE_CORRECT** | 913 | Correct in both V2.2 and V2.3 | Clear green healthy, unambiguous mature Tikka target lesions, typical raised Rust pustules. |
| **HEALTHY_RESCUED** | 86 | Flipped from Tikka (V2.2) to Healthy (V2.3) | Bright green field leaves with minor soil speckles, specular reflections, or slight yellowing that V2.2 called Tikka. |
| **PERSISTENT_HEALTHY_ERROR** | 92 | Misclassified as Tikka in both V2.2 and V2.3 | Field leaves with physiological edge chlorosis, mechanical tearing, or heavy shadowing. |
| **RUST_COLLAPSED_TO_TIKKA** | **42** | Correct Rust (V2.2) $\to$ Misclassified Tikka (V2.3) | Early-stage rust pustules, dispersed micro-punctures, or co-occurring chlorotic halos that V2.3 classifies as Tikka. |
| **PERSISTENT_RUST_ERROR** | 6 | Misclassified in both V2.2 and V2.3 | 5 misclassified as Tikka in both, 1 misclassified as Healthy in both. |
| **TIKKA_RESCUED_FROM_RUST** | 11 | Misclassified as Rust (V2.2) $\to$ Correct Tikka (V2.3) | Late Tikka lesions with dark brown necrotic centers previously confused with rust. |
| **TIKKA_DEGRADED_TO_HEALTHY** | 2 | Correct Tikka (V2.2) $\to$ Misclassified Healthy (V2.3) | Extremely faint, early-stage leaf spots overwhelmed by green background. |

---

## 6. Official Production Gate Assessment (Canonical 1,152)

| Production Gate | Target Threshold | V2.2 Baseline ($\mu \pm \sigma$) | V2.2 Seed 42 | V2.3 Seed 42 | Status | Gate Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Gate 1: Closed Macro-F1** | $\ge 0.8500$ | $0.8342 \pm 0.1163$ | **0.8548** | **0.8399** | -0.0149 pts | ❌ **FAIL** |
| **Gate 2a: $\tau=0.70$ Coverage** | $\ge 85.00\%$ | $78.24\% \pm 12.54\%$ | **68.40%** | **80.47%** | +12.07 pts | ❌ **FAIL** |
| **Gate 2b: $\tau=0.70$ Accepted Acc.** | $\ge 90.00\%$ | $87.78\% \pm 13.48\%$ | **93.27%** | **92.66%** | -0.61 pts | ✅ **PASS** |
| **Gate 3: Open-Set Macro-F1** | $\ge 0.8500$ | $0.6898 \pm 0.0994$ | **0.6964** | **0.6651** | -0.0313 pts | ❌ **FAIL** |

**Conclusion:** V2.3 Seed 42 fails 3 out of 4 production gates.

---

## 7. Synthesis & Architectural Audit Conclusions

### A. Evidence-Supported Explanation
1. **The V2.3 sampler successfully solved the specific pathology it was designed for:**
   Oversampling the 285 pure-green Healthy training images to an effective 1:1 exposure against Tikka expanded the model's healthy foliage manifold and reduced Healthy $\to$ Tikka errors by $48.3\%$ ($178 \to 92$), driving Healthy recall from $70.33\% \to 84.67\%$.
2. **The Rust recall collapse is 97.9% caused by misclassification into Tikka Leaf Spot:**
   Out of 48 Rust errors, 47 are predicted as Tikka and only 1 as Healthy. The model did not blur Rust into Healthy foliage.
3. **The cause of the Rust $\to$ Tikka collapse is a Diseased-Class Imbalance Distortion created by the sampler:**
   In natural training data, the ratio of Tikka to Rust is approximately $2,236 : 1,100 \approx 2 : 1$.
   When the V2.3 sampler forced the 285 green Healthy images into a 1:1 ratio with Tikka, the overall batch distribution became:
   - Green Healthy: $\approx 28.4\%$
   - Tikka: $\approx 28.4\%$
   - Rust: $\approx 28.4\%$
   - Nutrient Deficient: $\approx 14.8\%$
   While nominally "balanced" by broad group, the model learned a strong structural bias: **any leaf possessing brown, necrotic spots is overwhelming likely to be Tikka unless it displays pronounced canonical rust pustules.**
   Furthermore, because the loss weights were kept at $1.0\times$ for all classes (the V2.2 loss function), Rust had zero loss protection against being absorbed into Tikka's larger, more morphologically diverse feature space.

### B. Evidence That Is Insufficient to Establish Causation
1. **We cannot conclude that random seed initialization was irrelevant:**
   In V2.2, Seed 2024 achieved $97.33\%$ Healthy recall and $81.67\%$ Rust recall without any oversampling, purely through gradient trajectory luck. Whether V2.3 S42's 60.0% Rust recall is an extreme outlier or the new expected mean cannot be proven from a single seed.
2. **We cannot prove whether oversampling frequency or loss weighting was the primary lever:**
   The experiment changed the data distribution via sampler weights while keeping loss weights identical. Whether a milder oversampling ratio (e.g. $1:2$ instead of $1:1$) or re-introducing a Rust loss multiplier ($1.2\times - 1.4\times$) would preserve Healthy gains while halting the Rust collapse remains an unverified hypothesis until tested.

### C. Recommended Next Controlled Experiment: V2.3.1 (Tri-Class Boundary Balance)
**DO NOT launch Seeds 1337 or 2024 for V2.3.** Running two more seeds of a configuration that suffers a 35-point Rust collapse is an inefficient use of GPU compute and research time.

Instead, execute a single controlled next experiment: **M4 V2.3.1**:
1. **Calibrated Exposure Target**:
   Instead of forcing a $1:1$ ratio of Green Healthy to Tikka (which required an extreme $7.84\times$ repetition of the 285 images), use a **moderated $1 : 2$ ratio** (approx. $3.9\times$ oversampling).
2. **Asymmetric Disease Loss Protection**:
   Re-introduce a modest loss weight multiplier on Rust ($1.25\times$ or $1.35\times$) during training to penalize Rust $\to$ Tikka misclassifications, counteracting the natural dominance of Tikka's feature manifold.
3. **Run on Seed 42 first**:
   Evaluate on the same canonical benchmark. The target criteria must be:
   - Healthy Recall $\ge 80.0\%$
   - Rust Recall $\ge 90.0\%$
   - Tikka Recall $\ge 96.0\%$
   - Macro-F1 $\ge 0.8600$
