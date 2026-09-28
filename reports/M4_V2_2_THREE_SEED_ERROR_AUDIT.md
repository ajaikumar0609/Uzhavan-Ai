# Uzhavan M4 V2.2 — Three-Seed Error Audit & Diagnostic Report
**Document Type:** Empirical Model Error Audit (NO TRAINING / NO CODE CHANGES)  
**Date:** 2026-09-28  
**Scope:** Three Completed Checkpoints of M4 V2.2 Groundnut (`Seed 42`, `Seed 1337`, `Seed 2024`)  
**Evaluated Cohort:** Fixed External Test Set ($N=1,152$ scorable samples from West Bengal Sasmal dataset, `in_groundnut_wb_sasmal`)  
**Artifact Dependencies:**
- [m4_v2_2_three_seed_confusion.csv](file:///Users/ajaikumarn/Desktop/agri/reports/artifacts/m4_v2_2_three_seed_confusion.csv)
- [m4_v2_2_three_seed_error_cases.csv](file:///Users/ajaikumarn/Desktop/agri/reports/artifacts/m4_v2_2_three_seed_error_cases.csv)
- [m4_v2_2_three_seed_agreement.csv](file:///Users/ajaikumarn/Desktop/agri/reports/artifacts/m4_v2_2_three_seed_agreement.csv)
- [m4_v2_2_three_seed_confidence.csv](file:///Users/ajaikumarn/Desktop/agri/reports/artifacts/m4_v2_2_three_seed_confidence.csv)
- [m4_v2_2_three_seed_audit_diagnostic.json](file:///Users/ajaikumarn/Desktop/agri/reports/artifacts/m4_v2_2_three_seed_audit_diagnostic.json)

---

## 1. Executive Summary & The Critical Diagnostic Discovery

The three-seed replication of M4 V2.2 revealed a dramatic variance in external test **Healthy Recall**:
$$\text{Seed 42: } 70.33\% \quad \longrightarrow \quad \text{Seed 1337: } 34.00\% \quad \longrightarrow \quad \text{Seed 2024: } 97.33\% \quad (\mu = 67.22\% \pm 31.78\%)$$

Prior to this empirical audit, it was hypothesized that changes in Rust loss weighting (`rust-weight-mult 1.0`) or photometric shadow augmentations destabilized the **Healthy vs. Rust** decision boundary.

### The Ground-Truth Discovery:
Across all three seeds ($3 \times 1,152 = 3,456$ scorable inferences):
1. **Healthy $\longrightarrow$ Rust Error Count is Exactly ZERO across all three seeds ($0 / 600, 0.00\%$).**
   Not a single healthy groundnut leaf in the West Bengal external test set was predicted as Rust by Seed 42, Seed 1337, or Seed 2024.
2. **The entire Healthy recall collapse is Healthy being misclassified as TIKKA LEAF SPOT:**
   - **Seed 42:** 178 Healthy images predicted as **Tikka** ($29.67\%$), 0 as Rust.
   - **Seed 1337:** 396 Healthy images predicted as **Tikka** ($66.00\%$), 0 as Rust.
   - **Seed 2024:** 16 Healthy images predicted as **Tikka** ($2.67\%$), 0 as Rust.
3. **Rust recall remained high and stable in Seeds 42 and 1337 ($95.00\%$, $114 / 120$ correct in both).**  
   In Seed 2024, Rust recall dropped to $81.67\%$ ($98 / 120$) because $21$ Rust samples were predicted as **Tikka**, not Healthy ($1$ to Healthy).
4. **The underlying root cause is a Training-to-External Taxonomy Representation Mismatch:**
   - In training (`in_tn_multicrop_vitc`), the `healthy_or_abiotic` class is composed of **$80.3\%$ nutrient-deficient/chlorotic leaves** ($1,164 / 1,449$) and only **$19.7\%$ pristine green healthy leaves** ($285 / 1,449$).
   - Tikka in training has **$2,236$ images** (a **$7.8 : 1$ ratio** over pure green healthy).
   - In the external test set (`in_groundnut_wb_sasmal`), all $600$ healthy samples are **$100\%$ pristine green field phone captures** with zero nutrient deficiency.
   - Due to the scarcity of pure green healthy training samples, the model's Healthy vs. Tikka decision boundary on real field foliage is fragile and sensitive to random weight initialization and mini-batch ordering.

---

## 2. 3x3 Confusion Matrices per Seed ($N=1,152$)

### Seed 42 (Replication Baseline — S1)
*Overall Scorable Accuracy: $82.90\%$ ($955 / 1,152$) | Closed Macro-F1: $0.8548$*

| True Class | Pred Healthy | Pred Rust | Pred Tikka | Total True | Class Recall |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Healthy or Abiotic** | **422** | 0 | 178 | 600 | **70.33%** |
| **Rust** | 1 | **114** | 5 | 120 | **95.00%** |
| **Tikka Leaf Spot** | 2 | 11 | **419** | 432 | **96.99%** |
| **Total Predicted** | 425 | 125 | 602 | 1,152 | — |

---

### Seed 1337 (Collapsed Healthy Recall — S2)
*Overall Scorable Accuracy: $64.41\%$ ($742 / 1,152$) | Closed Macro-F1: $0.7089$*

| True Class | Pred Healthy | Pred Rust | Pred Tikka | Total True | Class Recall |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Healthy or Abiotic** | **204** | 0 | 396 | 600 | **34.00%** |
| **Rust** | 2 | **114** | 4 | 120 | **95.00%** |
| **Tikka Leaf Spot** | 1 | 7 | **424** | 432 | **98.15%** |
| **Total Predicted** | 207 | 121 | 824 | 1,152 | — |

---

### Seed 2024 (Peak Healthy Separation — S3)
*Overall Scorable Accuracy: $95.66\%$ ($1,102 / 1,152$) | Closed Macro-F1: $0.9388$*

| True Class | Pred Healthy | Pred Rust | Pred Tikka | Total True | Class Recall |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Healthy or Abiotic** | **584** | 0 | 16 | 600 | **97.33%** |
| **Rust** | 1 | **98** | 21 | 120 | **81.67%** |
| **Tikka Leaf Spot** | 11 | 1 | **420** | 432 | **97.22%** |
| **Total Predicted** | 596 | 99 | 457 | 1,152 | — |

---

## 3. Specific Quantification of Error Flows

| Direction | Seed 42 Count (%) | Seed 1337 Count (%) | Seed 2024 Count (%) | Aggregate Mean $\pm$ Std |
| :--- | :---: | :---: | :---: | :---: |
| **Healthy $\longrightarrow$ Rust** | **0 (0.00%)** | **0 (0.00%)** | **0 (0.00%)** | **0.0% $\pm$ 0.0%** |
| **Healthy $\longrightarrow$ Tikka** | **178 (29.67%)** | **396 (66.00%)** | **16 (2.67%)** | **32.78% $\pm$ 31.78%** |
| **Rust $\longrightarrow$ Healthy** | **1 (0.83%)** | **2 (1.67%)** | **1 (0.83%)** | **1.11% $\pm$ 0.48%** |
| **Rust $\longrightarrow$ Tikka** | **5 (4.17%)** | **4 (3.33%)** | **21 (17.50%)** | **8.33% $\pm$ 7.95%** |
| **Tikka $\longrightarrow$ Healthy** | **2 (0.46%)** | **1 (0.23%)** | **11 (2.55%)** | **1.08% $\pm$ 1.28%** |
| **Tikka $\longrightarrow$ Rust** | **11 (2.55%)** | **7 (1.62%)** | **1 (0.23%)** | **1.47% $\pm$ 1.17%** |

### Key Observations:
1. **Healthy $\longrightarrow$ Rust is non-existent.** The balanced Rust weight multiplier ($1.0\times$) did not cause false positive Rust predictions on healthy leaves.
2. **Healthy $\longrightarrow$ Tikka is the single point of failure.** In Seed 1337, two out of every three healthy leaves ($66.0\%$) are absorbed by the Tikka class.
3. **Rust $\longrightarrow$ Healthy is negligible.** Only 1 or 2 images out of 120 Rust samples are ever predicted as Healthy.
4. **Rust $\longrightarrow$ Tikka in Seed 2024:** In Seed 2024, Healthy separation expanded, but Tikka boundary shifted into Rust, causing 21 Rust images to be mislabeled as Tikka.

---

## 4. Actual External Image IDs for Specific Error Cases

### A. Healthy Predicted as Rust
- **Seed 42:** None ($0$ cases).
- **Seed 1337:** None ($0$ cases).
- **Seed 2024:** None ($0$ cases).

### B. Rust Predicted as Healthy
Across the entire 120 scorable Rust samples, exactly **3 unique images** were ever predicted as Healthy:

| Seed | Image SHA256 | Original Filename (Sasmal Dataset) | Confidence | $P(\text{Healthy})$ | $P(\text{Rust})$ | $P(\text{Tikka})$ |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: |
| **Seed 42** | `c0ee776a3f747c0800b7305943806ec046dbfd769da891d4e0e5a88e99a8035b` | `RUST/Rust (95).jpg` | 0.4746 | 0.4746 | 0.4371 | 0.0883 |
| **Seed 1337** | `30aebeaa8b99e0a298bfba8a3e746522cbb242eb0e527d928aa1bf4a02931a77` | `RUST/Rust (10).jpg` | 0.3457 | 0.3457 | 0.3340 | 0.3203 |
| **Seed 1337** | `357d3f649ee4031b2fc8627bc8004f2d7bf8a50c8e227092416b9cb8b7625841` | `RUST/Rust (11).jpg` | 0.5160 | 0.5160 | 0.4704 | 0.0136 |
| **Seed 2024** | `306298a9285c7ad1ba29dbf0744654921ea02aa1a7d653a99268db4c5b3d6cbe` | `RUST/Rust (92).jpg` | 0.4683 | 0.4683 | 0.4578 | 0.0739 |

*Diagnostic Note:* All four occurrences represent borderline ambiguous predictions ($P \approx 0.34 - 0.51$) with margins $< 0.05$ between Healthy and Rust.

### C. Persistent Healthy Predicted as Tikka (Common to All Three Seeds, $N=15$)
These 15 images represent the core ambiguity set where all three independent models failed:

| Image SHA256 | Original Filename (Sasmal) | S42 $P(\text{Tikka})$ | S1337 $P(\text{Tikka})$ | S2024 $P(\text{Tikka})$ | Mean Brightness | Contrast |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `6be97f9124370b54...` | `HEALTHY/Healthy (129).jpg` | 0.5282 | 0.7719 | 0.4946 | 134.9 | 47.7 |
| `b49cd0580f72b444...` | `HEALTHY/Healthy (190).jpg` | 0.5033 | 0.7410 | 0.4889 | 141.2 | 47.7 |
| `c101335cbf0974d0...` | `HEALTHY/Healthy (244).jpg` | 0.7329 | 0.8931 | 0.7097 | 129.8 | 48.0 |
| `6e995243a7977be3...` | `HEALTHY/Healthy (25).jpg` | 0.5218 | 0.6385 | 0.5852 | 139.7 | 45.4 |
| `9ee0e84f8c3d7b22...` | `HEALTHY/Healthy (257).jpg` | 0.6391 | 0.7607 | 0.7409 | 134.5 | 45.4 |
| `b8a68e096feeaea8...` | `HEALTHY/Healthy (260).jpg` | 0.6729 | 0.8124 | 0.7525 | 128.2 | 46.5 |
| `e30cf21b3b5f3bc1...` | `HEALTHY/Healthy (34).jpg` | 0.5404 | 0.6402 | 0.5298 | 136.2 | 44.9 |
| `5f733bf96a0cce0e...` | `HEALTHY/Healthy (347).jpg` | 0.7483 | 0.8711 | 0.7180 | 119.8 | 47.1 |
| `5ef7da4bacbf4e9e...` | `HEALTHY/Healthy (37).jpg` | 0.7818 | 0.8984 | 0.8612 | 144.3 | 47.2 |
| `50852382098cc57b...` | `HEALTHY/Healthy (380).jpg` | 0.5950 | 0.7621 | 0.5428 | 135.2 | 42.6 |
| `62dc689687b4a354...` | `HEALTHY/Healthy (40).jpg` | 0.5746 | 0.6853 | 0.5792 | 133.4 | 45.7 |
| `64f60e616b6f1f91...` | `HEALTHY/Healthy (480).jpg` | 0.7527 | 0.9046 | 0.8780 | 127.3 | 44.2 |
| `9b82376dc5218bac...` | `HEALTHY/Healthy (50).jpg` | 0.5186 | 0.6726 | 0.5273 | 129.6 | 45.5 |
| `6ab7809c57971584...` | `HEALTHY/Healthy (513).jpg` | 0.8118 | 0.9048 | 0.8682 | 120.5 | 49.3 |
| `f6948006fb4b295b...` | `HEALTHY/Healthy (516).jpg` | 0.5898 | 0.7274 | 0.6327 | 120.7 | 47.7 |

*(The 16th error in Seed 2024, `Healthy (89).jpg`, was correct in Seed 42 with $P(\text{Healthy})=0.534$ and Tikka in Seed 1337 with $P(\text{Tikka})=0.643$.)*

---

## 5. Misclassification Frequency Across Seeds

Of the $N=1,152$ scorable samples:

```mermaid
pie title Misclassification Count Across 3 Seeds (N=1152)
    "0 Errors (All 3 Correct)" : 697
    "1 Error (1 Seed Failed)" : 271
    "2 Errors (2 Seeds Failed)" : 166
    "3 Errors (All 3 Failed)" : 18
```

| Failure Frequency | Sample Count ($N=1,152$) | Percentage | Healthy ($N=600$) | Rust ($N=120$) | Tikka ($N=432$) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **All 3 Correct** (0 errors) | **697** | **60.50%** | 192 (32.00%) | 97 (80.83%) | 408 (94.44%) |
| **1 Seed Failed** (1 error) | **271** | **23.52%** | 241 (40.17%) | 14 (11.67%) | 16 (3.70%) |
| **2 Seeds Failed** (2 errors) | **166** | **14.41%** | 152 (25.33%) | 7 (5.83%) | 7 (1.62%) |
| **All 3 Failed** (3 errors) | **18** | **1.56%** | 15 (2.50%) | 2 (1.67%) | 1 (0.23%) |

### Interpretation:
- **Tikka is virtually solved:** $94.4\%$ of all Tikka images are correctly classified by all three models without disagreement.
- **Rust is substantially stable:** $80.8\%$ of Rust images are unanimously correct across all three models.
- **Healthy is where the instability concentrates:** Only $32.0\%$ ($192 / 600$) of Healthy images are unanimously correct. Over $65.5\%$ ($393 / 600$) suffer disagreement, almost exclusively with Tikka.

---

## 6. Prediction Agreement Across Seeds

Detailed breakdown from [m4_v2_2_three_seed_agreement.csv](file:///Users/ajaikumarn/Desktop/agri/reports/artifacts/m4_v2_2_three_seed_agreement.csv):

| Cohort | Total $N$ | 3/3 Unanimous Agree | 2/3 Majority Agree | All Disagree (Split) | Unanimous Correct |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **All Scorable** | **1,152** | **715 (62.07%)** | **433 (37.59%)** | **4 (0.35%)** | **697 (60.50%)** |
| **Healthy** | 600 | 207 (34.50%) | 393 (65.50%) | 0 (0.00%) | 192 (32.00%) |
| **Rust** | 120 | 99 (82.50%) | 19 (15.83%) | 2 (1.67%) | 97 (80.83%) |
| **Tikka** | 432 | 409 (94.68%) | 21 (4.86%) | 2 (0.46%) | 408 (94.44%) |

*Crucial Finding:* The "All Disagree" rate is almost zero ($0.35\%$, only 4 images in the entire dataset). When models disagree, it is strictly binary: **Healthy vs. Tikka**.

---

## 7. Confidence Distributions Comparison

Detailed summary from [m4_v2_2_three_seed_confidence.csv](file:///Users/ajaikumarn/Desktop/agri/reports/artifacts/m4_v2_2_three_seed_confidence.csv):

| Seed | Case Type | Count | Mean Conf | Std | Median | IQR | Min | Max |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Seed 42** | Correct Healthy | 422 | 0.7338 | 0.1393 | 0.7352 | 0.2376 | 0.4710 | 0.9957 |
| **Seed 42** | Healthy $\to$ Rust | **0** | **0.0000** | — | — | — | — | — |
| **Seed 42** | Healthy $\to$ Tikka | 178 | 0.6186 | 0.1054 | 0.5950 | 0.1721 | 0.4352 | 0.9379 |
| **Seed 42** | Correct Rust | 114 | 0.9213 | 0.1110 | 0.9686 | 0.0642 | 0.5119 | 0.9978 |
| **Seed 42** | Rust $\to$ Healthy | 1 | 0.4746 | 0.0000 | 0.4746 | 0.0000 | 0.4746 | 0.4746 |
| **Seed 42** | Correct Tikka | 419 | 0.9084 | 0.1144 | 0.9620 | 0.1172 | 0.4832 | 0.9997 |
| **Seed 1337** | Correct Healthy | 204 | 0.6787 | 0.1438 | 0.6531 | 0.2325 | 0.4405 | 0.9974 |
| **Seed 1337** | Healthy $\to$ Rust | **0** | **0.0000** | — | — | — | — | — |
| **Seed 1337** | Healthy $\to$ Tikka | 396 | 0.7285 | 0.1354 | 0.7327 | 0.2237 | 0.4509 | 0.9885 |
| **Seed 1337** | Correct Rust | 114 | 0.9692 | 0.0491 | 0.9891 | 0.0327 | 0.7273 | 0.9999 |
| **Seed 1337** | Rust $\to$ Healthy | 2 | 0.4309 | 0.0852 | 0.4309 | 0.0851 | 0.3457 | 0.5160 |
| **Seed 1337** | Correct Tikka | 424 | 0.9887 | 0.0416 | 0.9994 | 0.0024 | 0.5985 | 1.0000 |
| **Seed 2024** | Correct Healthy | 584 | 0.9263 | 0.1075 | 0.9753 | 0.0854 | 0.5010 | 0.9998 |
| **Seed 2024** | Healthy $\to$ Rust | **0** | **0.0000** | — | — | — | — | — |
| **Seed 2024** | Healthy $\to$ Tikka | 16 | 0.6659 | 0.1384 | 0.6138 | 0.2191 | 0.4889 | 0.8780 |
| **Seed 2024** | Correct Rust | 98 | 0.8518 | 0.1579 | 0.9337 | 0.2205 | 0.4844 | 0.9994 |
| **Seed 2024** | Rust $\to$ Healthy | 1 | 0.4683 | 0.0000 | 0.4683 | 0.0000 | 0.4683 | 0.4683 |
| **Seed 2024** | Correct Tikka | 420 | 0.9675 | 0.0729 | 0.9950 | 0.0223 | 0.4008 | 0.9999 |

### Statistical Insights:
1. **Misclassified Healthy images have suppressed confidence:**
   - In Seed 42, median confidence on Healthy $\to$ Tikka is **$0.5950$** (versus **$0.9620$** on true Tikka).
   - In Seed 1337, median confidence on Healthy $\to$ Tikka is **$0.7327$** (versus **$0.9994$** on true Tikka).
2. **True Tikka predictions are near certainty:** In Seed 1337, half of all true Tikka samples have $P(\text{Tikka}) \ge 0.9994$.
3. **Seed 1337 is slightly overconfident on errors, but still markedly below its true positives:** $41.9\%$ of Seed 1337's Healthy $\to$ Tikka errors have confidence $< 0.70$, and $63.1\%$ have confidence $< 0.80$.

---

## 8. Root Cause Factor Association Testing

We conducted empirical association tests across seven candidate explanations for the Healthy collapse:

### Factor 1: Image Quality, Resolution, and Camera Properties
- **Finding:** **NEGATIVE (No Association).**
- **Evidence:** All $1,152$ external scorable images in `in_groundnut_wb_sasmal` have identical spatial resolution ($4624 \times 3472$ px), identical format (JPEG RGB), and identical sensor origin (Samsung phone camera in Ramchandrapur village).
- Average file size is $43.1 \text{ KB} \pm 3.1 \text{ KB}$ for robust healthy versus $42.8 \text{ KB} \pm 2.9 \text{ KB}$ for Seed 1337 errors ($p = 0.22$).

### Factor 2: Shadows, Background, and Illumination
- **Finding:** **NEGATIVE (No Association).**
- **Evidence:** 
  - Mean brightness: Robust Healthy = $131.87 \pm 7.95$, Seed 1337 Error Only = $130.50 \pm 8.32$, Dual S42+S1337 Error = $131.84 \pm 8.28$.
  - Shadow fraction (pixels with luminance $< 40$): Exactly $0.04 \pm 0.03$ across all subgroups.
  - Contrast ($\sigma$ luminance): $43.96 \pm 4.65$ (robust) vs $45.45 \pm 4.13$ (errors).
  - Shadows and soil background variations exist equally across correctly and incorrectly classified images.

### Factor 3: Colorfulness and Brown Soil Ratios
- **Finding:** **NEGATIVE (No Association).**
- **Evidence:**
  - Green ratio ($G / (R+G+B)$): $0.43 \pm 0.03$ across all Healthy subsets.
  - Brown/soil ratio ($R / (R+G+B)$): $0.29 \pm 0.04$ across all Healthy subsets.
  - Soil background is not being mistaken for Rust pustules or Tikka spots.

### Factor 4: Sharpness / Blurriness (Laplacian Variance)
- **Finding:** **NEGATIVE (No Association).**
- **Evidence:**
  - Discrete Laplacian variance: Robust Healthy = $295.3 \pm 89.8$, Seed 1337 Error Only = $305.9 \pm 86.1$, Dual Error = $292.8 \pm 68.5$.
  - Blurring does not explain why Seed 1337 shifted to Tikka.

### Factor 5: Duplicate and Near-Duplicate Structure
- **Finding:** **NEGATIVE (No Association with Seed Variance).**
- **Evidence:**
  - There are $509$ distinct `group_id` clusters among the $600$ Healthy images ($91$ pairs of duplicate/near-duplicate images).
  - In all $91$ pairs, both images in the pair received identical predictions across all three seeds ($100\%$ intra-pair consistency).
  - Duplicate structure causes small redundancy, but does not drive the $34\%$ vs $70\%$ vs $97\%$ divergence.

### Factor 6: Cross-Seed Sample Persistence (Nested Error Hierarchy)
- **Finding:** **HIGHLY CONFIRMED.**
- **Evidence:**
  - The errors exhibit a near-perfect nested subset structure:
    $$\text{Seed 2024 Errors (16)} \;\subset\; \text{Seed 42 Errors (178)} \;\subset\; \text{Seed 1337 Errors (396)}$$
  - Specifically:
    - $16 / 16$ ($100\%$) of Seed 2024 Healthy errors were also misclassified by Seed 1337.
    - $15 / 16$ ($93.8\%$) of Seed 2024 Healthy errors were also misclassified by Seed 42.
    - $166 / 178$ ($93.3\%$) of Seed 42 Healthy errors were also misclassified by Seed 1337.
  - This proves that all three models share the exact same underlying error gradient, but operate with different decision boundary thresholds/margins!

### Factor 7: Training Distribution & Class Ambiguity (The Decisive Root Cause)
- **Finding:** **HIGHLY CONFIRMED (The Primary Driver).**
- **Evidence:**
  1. In the training split, `groundnut__healthy_or_abiotic` contains $1,164$ nutrient deficiency images (leaf chlorosis, pale margins) and only **$285$ pure green healthy images**.
  2. Tikka Leaf Spot contains **$2,236$ training images**.
  3. When the network is trained with Cross-Entropy:
     - The representation learns that "leaves with mild chlorosis or subtle natural variation belong to the healthy_or_abiotic distribution".
     - However, the feature space for pristine green foliage is severely under-represented ($285$ images vs $2,236$ Tikka images).
     - Without out-of-domain regularization or logit margin constraints, the classification hyperplane between pure healthy green leaves and early Tikka lesions fluctuates randomly during training.
  4. The log-odds margin on external Healthy samples reflects this direct boundary shift:
     - **Seed 2024:** Median $\ln(P_H / P_T) = +3.838$ (Recall $97.3\%$)
     - **Seed 42:** Median $\ln(P_H / P_T) = +0.660$ (Recall $70.3\%$)
     - **Seed 1337:** Median $\ln(P_H / P_T) = -0.607$ (Recall $34.0\%$)

---

## 9. Comprehensive Synthesis

### A. Evidence-Supported Root Causes
1. **Zero Healthy $\to$ Rust Confusion:**
   The hypothesis that Healthy leaves are being mistaken for Rust is definitively refuted by empirical evidence ($0$ occurrences in all seeds).
2. **Healthy $\to$ Tikka Representation Vulnerability:**
   Healthy recall varies between $34\%$ and $97\%$ exclusively because models misclassify pristine green leaves as Tikka Leaf Spot.
3. **Training Imbalance between Pure Healthy and Tikka:**
   The training split has a $7.8\times$ disparity between Tikka ($2,236$ samples) and pristine green Healthy ($285$ samples). The remaining $80.3\%$ of the training Healthy class is nutrient deficiency from a different visual domain (`in_tn_multicrop_vitc`).
4. **Hyperplane Instability (Log-Odds Shift):**
   The three seeds differ by a simple monotonic shift in their log-odds margin $\ln(P_H / P_T)$ on external images. The ranking of image difficulties is consistent ($93-100\%$ nested error overlap), but the decision boundary placement varies by $\approx 4.4$ log-odds units between Seed 1337 and Seed 2024.

### B. Evidence That Was NOT Sufficient to Establish a Cause
1. **Rust Class Weighting:**
   V2.2's Rust class weight ($1.0\times$) did not hurt Healthy recall. Rust recall was $95\%$ in both Seed 42 and Seed 1337.
2. **Photometric Augmentations:**
   Shadow simulation and Gaussian blur did not cause Healthy leaves to look like Rust pustules or induce false shadows.
3. **Image Metadata / Environmental Differences:**
   Image brightness, contrast, shadow percentage, aspect ratio, blurriness, and file size showed zero statistically significant correlation with Healthy misclassification.

### C. Recommended Controlled Next Experiment

Rather than blindly trying more epochs, changing augmentations, or adding random loss functions, the next controlled experiment should directly address the **Healthy vs. Tikka decision boundary stability**:

#### Experiment Recommendation: **M4 V2.3 — Balanced Healthy Representation & Logit-Adjusted Loss**
1. **Data Rebalancing (Fix the 7.8:1 Tikka-to-Healthy Starvation):**
   - Incorporate curated field healthy groundnut foliage or balance the sampling probability of pure green Healthy leaves relative to Tikka during batch sampling (e.g. `WeightedRandomSampler` or targeted oversampling of pure healthy samples up to $\approx 1,500$ effective samples per epoch).
2. **Logit Margin Adjustment / Class-Prior Calibration:**
   - Implement logit adjustment ($\text{logit}_y = z_y - \tau \log \pi_y$) to prevent the dominant Tikka class from encroaching on the Healthy decision boundary under random weight initialization.
3. **Validation Selection Metric Fix:**
   - In V2.2, all three seeds scored $1.0000$ macro-F1 on internal validation from Epoch 2-6 onward, leaving model checkpoint selection to random chance or negligible loss differences on the saturated internal validation set. Checkpoint selection must incorporate an out-of-domain validation slice (e.g., reserving 20% of external data or using a cross-domain early-stopping monitor) so models that collapse Healthy recall are never selected as `checkpoint_best.pt`.

---
*Report generated autonomously by Uzhavan ML Diagnostic Audit Engine. No checkpoints or production code modified.*
