# Uzhavan M4 V2.3 Evaluation Protocol & Scientific Benchmark Standard
**Document Type:** Formal Scientific Evaluation Protocol  
**Date:** 2026-09-28  
**Scope:** Model Selection, Development Holdout Partitioning, and Final External Benchmarking for M4 V2.3  
**Status:** **APPROVED & LOCKED**  

---

## 1. Scientific Objective & Rationale

In the M4 V2.2 three-seed replication audit, an unexpected evaluation flaw was identified:
- **Internal Validation Saturation:** On the internal validation split (`in_tn_multicrop_vitc`), all three seeds reached a perfect Macro-F1 of **$1.0000$** from Epoch 2–6 onward.
- **Blind Checkpoint Selection:** Because the internal validation set was fully saturated, the training engine's `checkpoint_best.pt` selection became stochastic or driven by minor float differences in cross-entropy loss, entirely blind to whether the model was maintaining Healthy separation or collapsing into Tikka on field foliage.
- **Tuning Contamination Risk:** Tuning hyperparameters or selecting thresholds directly against the entire $N=1,152$ external test set compromises the scientific integrity of the final benchmark.

To solve this, V2.3 establishes a **strict two-tier external evaluation protocol** prior to training:
```
West Bengal External Field Dataset (in_groundnut_wb_sasmal, N=1,695)
│
├── 1. Development Holdout (20% Group-Stratified, N=335 total / 224 scorable)
│      ├── Used for epoch-by-epoch model selection (checkpoint_best.pt)
│      └── Used for operational threshold calibration (tau = 0.60 to 0.80)
│
└── 2. Final External Test (80% Group-Stratified, N=1,360 total / 928 scorable)
       └── STRICTLY UNTOUCHED until final model freeze and evaluation
```

---

## 2. Partition Specifications & Zero-Leakage Guarantee

To prevent information leakage between the Development Holdout and the Final External Test, partitioning is conducted with **Group-Aware Stratification** based on the perceptual hash cluster ID (`group_id`). All duplicate and near-duplicate images within a cluster are constrained to the same split.

The partitioning is deterministically generated using Seed 42 and preserved in:
`uzhavan_ml/m4_v2_3/external_split_mapping.csv`

### Exact Class Distribution Across External Splits

| Canonical Class | Total External ($N=1,695$) | Development Holdout (20%) | Final Untouched Test (80%) |
| :--- | :---: | :---: | :---: |
| **Healthy or Abiotic** (`groundnut__healthy_or_abiotic`) | 600 | **117** (19.5%) | **483** (80.5%) |
| **Rust** (`groundnut__rust`) | 120 | **21** (17.5%) | **99** (82.5%) |
| **Tikka Leaf Spot** (`groundnut__tikka_leaf_spot`) | 432 | **86** (19.9%) | **346** (80.1%) |
| **Scorable In-Taxonomy Subtotal** | **1,152** | **224 (19.4%)** | **928 (80.6%)** |
| *Alternaria Leaf Spot* (OOD Non-Target) | 448 | **92** (20.5%) | **356** (79.5%) |
| *Rosette Virus* (OOD Non-Target) | 95 | **19** (20.0%) | **76** (80.0%) |
| **Total External Universe** | **1,695** | **335 (19.8%)** | **1,360 (80.2%)** |

### Zero-Leakage Proof:
1. **Source Disjointness:** No sample from `in_groundnut_wb_sasmal` appears in the training or internal validation splits.
2. **Cluster Exclusivity:** For all $509$ unique `group_id`s in the external dataset, $100\%$ of samples within any group are assigned exclusively to either the Development Holdout or the Final Test.
3. **Immutability:** The file mappings are recorded with SHA256 hashes in `external_split_mapping.csv`.

---

## 3. Checkpoint Selection & Operational Calibration

### A. Epoch Checkpoint Selection
During V2.3 training:
- At the end of each epoch, the model is evaluated on both the internal validation split and the **External Development Holdout** ($N=224$ scorable).
- The official checkpoint (`checkpoint_best.pt`) is saved when the model achieves the highest **Closed Macro-F1 on the Development Holdout**.
- This ensures models that collapse Healthy recall on real-world field leaves are immediately detected and discarded.

### B. Threshold Calibration ($\tau$)
- All operational threshold sweeps ($\tau \in [0.50, 0.90]$, quantile policies `val_q01`, `val_q05`) are calibrated **strictly on the Development Holdout**.
- The selected operational threshold $\tau^*$ is then locked.

---

## 4. Final Benchmark Reporting Standard

To preserve continuity with the V2.2 baseline while guaranteeing scientific rigor, V2.3 evaluation scripts will generate two standardized reporting tables:

### 1. Primary Scientific Benchmark: Final Untouched Test ($N=928$ scorable / $N=1,360$ total)
- Evaluated only once after `checkpoint_best.pt` and threshold $\tau^*$ are locked.
- Represents the true, unbiased generalization estimate for academic and production publication.

### 2. Historical Replication Benchmark: Full Canonical External Set ($N=1,152$ scorable / $N=1,695$ total)
- Evaluated over the exact same 1,152 scorable samples used in V2.0, V2.1, and V2.2.
- Enables direct, apples-to-apples comparison against V2.2's 3-seed baseline:
  - Macro-F1: $0.8342 \pm 0.1163$
  - Healthy Recall: $67.2\% \pm 31.8\%$
  - Rust Recall: $90.6\% \pm 7.7\%$
  - Tikka Recall: $97.5\% \pm 0.6\%$

---

## 5. Metric Definitions & Production Gates (Identical to V2.2)

1. **Closed-Set Macro-F1 (Primary Gate $\ge 0.85$):**
   Unweighted mean of class F1 scores across the three target classes:
   $$\text{Macro-F1} = \frac{1}{3} \left( \text{F1}_{\text{healthy}} + \text{F1}_{\text{rust}} + \text{F1}_{\text{tikka}} \right)$$

2. **Selective Efficiency at $\tau=0.70$ (Operational Gate):**
   - **Coverage $\ge 85\%$:** Percentage of scorable samples where $\max_c P(c) \ge 0.70$.
   - **Accepted Accuracy $\ge 90\%$:** Classification accuracy on accepted samples.

3. **Open-Set Macro-F1 (Discrimination Gate $\ge 0.85$):**
   Evaluated over all external samples (including Alternaria and Rosette). Samples below threshold are categorized as `UNSURE`. True target samples falling below threshold are counted as False Negatives; out-of-domain samples above threshold are counted as False Positives.

---
*Protocol locked and approved for Uzhavan M4 V2.3.*
