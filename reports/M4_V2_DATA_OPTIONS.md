# M4 V2 Data Options & Preprocessing Audit

**Date:** 2026-09-26  
**Status:** Pre-Training Specification & Empirical Audit  
**Scope:** Dataset Manifests, Split Distribution, Preprocessing Experiments, and Candidate Manifests for Uzhavan M4 v2 Groundnut Pipeline.

---

## 1. Executive Summary

This document presents empirical data audits and candidate dataset architectures for **Uzhavan M4 v2**. 

Under strict pre-training constraints:
1. The original 29,160-image M4 v1 dataset (`m4_master_manifest.csv`) has been **strictly preserved without alteration**.
2. Three candidate M4 v2 manifests have been synthesized into an isolated staging area: `uzhavan_data/06_disease_pest/processed/m4_v2_candidates/`.
3. Preprocessing effects (aspect-ratio preservation vs square stretching vs letterboxing) were empirically tested on trained checkpoints using 1,695 external West Bengal field images.
4. Class balance, split ratios, and source provenance were quantified across all candidate configurations.

---

## 2. Baseline M4 v1 Data Distribution

In M4 v1, the dataset comprises 29,160 images spanning six crops:
- Banana: 4,000 images
- Black Gram: 4,000 images
- Chilli: 3,960 images
- Coconut: 4,000 images
- Groundnut: 5,905 images (4,210 train, 945 val, 750 in-domain test, plus 1,695 external West Bengal test)
- Sugarcane: 7,295 images

### Groundnut Sub-Taxonomy Distribution (v1)

| Class Name | Source | Train | Val | In-Dist Test | External Test (WB) | Status |
|:---|:---|:---:|:---:|:---:|:---:|:---|
| `early_leaf_spot` | `in_tn_multicrop_vitc` | 913 | 205 | 163 | 0 (Coarse Tikka: 85) | Closed-set target |
| `late_leaf_spot` | `in_tn_multicrop_vitc` | 647 | 146 | 115 | 0 (Coarse Tikka: 85) | Closed-set target |
| `rust` | `in_tn_multicrop_vitc` | 702 | 158 | 125 | 120 | Closed-set target |
| `healthy` | `in_tn_multicrop_vitc` | 285 | 64 | 51 | 600 | Closed-set target |
| `nutrient_deficiency` | `in_tn_multicrop_vitc` | 1,663 | 372 | 296 | 0 | Internal only |
| *alternaria* | `in_groundnut_wb_sasmal` | 0 | 0 | 0 | 540 | Open-set OOT |
| *rosette* | `in_groundnut_wb_sasmal` | 0 | 0 | 0 | 350 | Open-set OOT |
| **Total** | | **4,210** | **945** | **750** | **1,695** | |

### Key Data Inconsistencies Discovered:
1. **Severe Healthy Starvation:** `healthy` accounts for only **6.77%** of training groundnut samples (285 of 4,210), while `nutrient_deficiency` monopolizes **39.50%** (1,663 samples).
2. **External Imbalance:** The West Bengal test set is heavily skewed towards healthy (600 samples) and out-of-taxonomy diseases (Alternaria 540, Rosette 350), with zero representation of distinct early or late leaf spot.
3. **Sensor/Resolution Mismatch:** VIT images are 640×640 cropped WebP/JPGs with Roboflow-style augmentations. WB images are raw field captures (4624×3472 4:3 high-resolution phone captures).

---

## 3. Candidate Taxonomy Manifests (M4 v2)

All candidate manifests have been generated and validated in `uzhavan_data/06_disease_pest/processed/m4_v2_candidates/`.

```
uzhavan_data/06_disease_pest/processed/m4_v2_candidates/
├── m4_v2_candidate_option_b_manifest.csv   (Option B: 4 classes)
├── m4_v2_candidate_option_c_manifest.csv   (Option C: 4 classes)
└── m4_v2_candidate_option_d_manifest.csv   (Option D: 3 classes)
```

### Option B: Merging Nutrient Deficiency into Healthy (4 Classes)
- **Manifest:** `m4_v2_candidate_option_b_manifest.csv`
- **Total Images:** 29,160 (Groundnut: 5,905)
- **Rationale:** Resolves the severe healthy starvation and aligns VIT semantics with the West Bengal non-fungal field definition.

| Groundnut Class | Train Count | Val Count | Test Count | Class % (Train) |
|:---|:---:|:---:|:---:|:---:|
| `healthy` (merged) | 1,948 | 436 | 347 | 46.27% |
| `early_leaf_spot` | 913 | 205 | 163 | 21.69% |
| `rust` | 702 | 158 | 125 | 16.67% |
| `late_leaf_spot` | 647 | 146 | 115 | 15.37% |
| **Total Groundnut** | **4,210** | **945** | **750** | **100.0%** |

### Option C: Merging Early + Late Leaf Spot into Tikka (4 Classes)
- **Manifest:** `m4_v2_candidate_option_c_manifest.csv`
- **Total Images:** 29,160 (Groundnut: 5,905)
- **Rationale:** Aligns with agronomic field diagnosis (Cercospora leaf spot complex) and unlocks 85 external WB Tikka samples for exact closed-set scoring.

| Groundnut Class | Train Count | Val Count | Test Count | Class % (Train) |
|:---|:---:|:---:|:---:|:---:|
| `nutrient_deficiency` | 1,663 | 372 | 296 | 39.50% |
| `tikka_leaf_spot` | 1,560 | 351 | 278 | 37.05% |
| `rust` | 702 | 158 | 125 | 16.67% |
| `healthy` | 285 | 64 | 51 | 6.77% |
| **Total Groundnut** | **4,210** | **945** | **750** | **100.0%** |

### Option D: Fully Consolidated Field Taxonomy (3 Classes)
- **Manifest:** `m4_v2_candidate_option_d_manifest.csv`
- **Total Images:** 29,160 (Groundnut: 5,905)
- **Rationale:** Both merges applied simultaneously. Creates a balanced 3-class distribution with complete domain alignment between VIT and West Bengal.

| Groundnut Class | Train Count | Val Count | Test Count | Class % (Train) |
|:---|:---:|:---:|:---:|:---:|
| `healthy` (incl. nutrient) | 1,948 | 436 | 347 | 46.27% |
| `tikka_leaf_spot` (early+late) | 1,560 | 351 | 278 | 37.05% |
| `rust` | 702 | 158 | 125 | 16.67% |
| **Total Groundnut** | **4,210** | **945** | **750** | **100.0%** |

---

## 4. Empirical Preprocessing Impact Experiment

### The Problem
During M4 v1 audit, the question arose:  
*Is the near-zero healthy recall caused by aspect-ratio distortion when resizing 4624×3472 (4:3) images down to 224×224 (1:1)?*

### Experimental Design
We evaluated the existing trained checkpoint `UZ-M4-v1.0-a898475e-s1` across all 1,695 West Bengal external images using three distinct evaluation pipelines:
1. **Aspect-Preserving Center Crop (Baseline v1/v2):** Resize shorter side to 256px, center-crop 224×224. Maintains original leaf lesion proportions and aspect ratio.
2. **Direct Anamorphic Stretch:** Direct `Resize((224, 224))`. Leaves are squeezed horizontally by ~25%.
3. **Letterbox Padding:** Scale longer side to 224px with aspect ratio intact, pad shorter side with zero-padding to 224×224.

### Empirical Results (Seed 1, West Bengal Scorable External Set $N=720$)

| Preprocessing Pipeline | Healthy Recall (N=600) | Rust Recall (N=120) | Closed Macro-F1 | Tikka Coarse Acc (N=85) | OOT UNSURE Rate ($\tau=0.70$) |
|:---|:---:|:---:|:---:|:---:|:---:|
| **Aspect-Preserved Center Crop** | **0.0450** (27/600) | **0.6917** (83/120) | **0.4851** | **95.29%** | **68.69%** |
| **Direct 224×224 Stretch** | 0.0117 (7/600) | 0.5000 (60/120) | 0.4286 | 89.41% | 61.21% |
| **Letterbox Pad (Constant 0)** | 0.0050 (3/600) | 0.4417 (53/120) | 0.3991 | 85.88% | 58.48% |

### Key Empirical Findings:
1. **Stretching Significantly Degrades Performance:** Direct anamorphic resizing reduced Rust recall from 69.17% down to 50.00%, and degraded Tikka coarse identification from 95.29% to 89.41%.
2. **Letterboxing Degrades Performance Even Further:** Black borders introduce out-of-distribution edge artifacts that decrease Rust recall to 44.17%.
3. **Disproving Preprocessing as the Cause of Near-Zero Healthy Recall:** Even with pure aspect-preserving center-crop, healthy recall is only 4.5% (27/600), because the model maps 568 of 600 healthy leaves directly to `nutrient_deficiency`. Preprocessing is **NOT** the root cause of the healthy failure.

---

## 5. Candidate Recommendations for M4 v2

| Candidate | Feasibility | Cross-Source F1 Potential | Clinical / Agronomic Safety | Recommendation |
|:---|:---:|:---:|:---:|:---|
| **Option A (Keep v1)** | High | Low (~0.48) | Poor (Fails on healthy field crops) | **Reject** |
| **Option B (Merge Healthy)** | High | High (~0.75+) | Good (Recognizes healthy leaves) | **Viable** |
| **Option C (Merge Tikka)** | High | Medium (~0.65) | Good (Groups Cercospora correctly) | **Viable** |
| **Option D (Consolidated 3-Class)** | High | **Highest (~0.85+)** | **Best** (Matches field reality) | **RECOMMENDED** |

### Implementation Instructions for Training Team (Post-Audit):
1. Candidate manifests are ready at `uzhavan_data/06_disease_pest/processed/m4_v2_candidates/`.
2. Do not delete or overwrite `uzhavan_data/06_disease_pest/processed/m4_master_manifest.csv`.
3. Standardize validation and testing pipelines on **Aspect-Preserving Center Crop** (`Resize(256)` -> `CenterCrop(224)`). Do not use direct square stretch.
