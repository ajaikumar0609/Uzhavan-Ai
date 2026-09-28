# M4 V2 Groundnut Training Specification

## 1. Overview & Objectives
This document specifies the exact dataset, model architecture, training hyper-parameters, loss formulations, and reproducibility guarantees for the **M4 V2 Groundnut Disease Classification Model** in UZHAVAN AI.

The V2 model resolves the biological and visual confusions identified in the M4 V1 pre-training audit:
- Merges co-occurring early & late leaf spots into `groundnut__tikka_leaf_spot`.
- Merges healthy foliage and abiotic yellowing into `groundnut__healthy_or_abiotic`.
- Preserves distinct fungal pustule pathogen `groundnut__rust`.

---

## 2. Dataset & Taxonomy Specifications

### 2.1 Taxonomy Definition
| V2 Canonical Class | Source / V1 Biological Classes | Clinical Description |
|---|---|---|
| `groundnut__tikka_leaf_spot` | `early_leaf_spot` (Cercospora arachidicola) + `late_leaf_spot` (Phaeoisariopsis personata) | Indistinguishable necrotic brown/black circular lesions with yellow halos. |
| `groundnut__rust` | `rust` (Puccinia arachidis) | Raised orange-brown pustules on lower leaf surfaces. |
| `groundnut__healthy_or_abiotic` | `healthy` + `nutrient_deficiency` | Asymptomatic clean foliage or diffuse non-pathogenic chlorosis. |

### 2.2 Verified Training Split Image Counts
- Source manifest: `uzhavan_ml/packages/m4_v1/manifest.csv`
- V2 Groundnut manifest: `uzhavan_ml/m4_v2/manifests/groundnut_v2.csv`
- Manifest SHA256: `6768c740a0bc32ec45be08237c564e0be153a610caab9909196c1a0c123a4cfe`

| Canonical Class | Training Count | Validation Count | Internal Test Count |
|---|---|---|---|
| `groundnut__tikka_leaf_spot` | **2,236** | 478 | 483 |
| `groundnut__rust` | **2,235** | 478 | 481 |
| `groundnut__healthy_or_abiotic` | **1,449** | 311 | 312 |
| **Total** | **5,920** | **1,267** | **1,276** |

**External Test Split (West Bengal Sasmal)**:
- Total: 1,695 images (`healthy_or_abiotic`: 600, `tikka_leaf_spot`: 432, `rust`: 120, OOD `alternaria_leaf_spot`: 448, OOD `rosette_virus`: 95).
- **CRITICAL DATA SPLIT RULE**: Zero West Bengal external images are included in training or validation splits. The training split exclusively draws from source `in_tn_multicrop_vitc`.

---

## 3. Preprocessing & Input Augmentations

Inference and validation transformations must strictly match across all evaluation pipelines:
- **Aspect-Preserving Resize**: `Resize(256)`
- **Center Crop**: `CenterCrop(224)`
- **Tensor Conversion & Normalization**:
  - `ToTensor()`
  - `Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])`

Training augmentations (light, agronomic):
- `RandomResizedCrop(224, scale=(0.8, 1.0))`
- `RandomHorizontalFlip(p=0.5)`
- `RandomVerticalFlip(p=0.5)`
- `ColorJitter(brightness=0.1, contrast=0.1)`
- `ToTensor()`
- `Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])`

---

## 4. Model Architecture

- **Backbone**: `torchvision.models.efficientnet_v2_s(weights="DEFAULT")`
- **Classifier Head**:
  - Dropout: `p=0.2` (default EfficientNetV2 classifier dropout)
  - Linear layer: `in_features=1280`, `out_features=3`
  - Output classes: `[healthy_or_abiotic, rust, tikka_leaf_spot]`

---

## 5. Loss Formulations & Experimental Matrix

Two core loss formulations will be trained across 3 random seeds:

### 5.1 Weighted Cross-Entropy (WCE)
Weights inverse to class frequencies:
$$w_c = \frac{N}{K \cdot N_c}$$
Where $N = 5920$, $K = 3$:
- $w_{\text{healthy}} = 5920 / (3 \times 1449) \approx 1.3619$
- $w_{\text{rust}} = 5920 / (3 \times 2235) \approx 0.8829$
- $w_{\text{tikka}} = 5920 / (3 \times 2236) \approx 0.8825$

Normalized to mean 1.0: `[1.3619, 0.8829, 0.8825]`

### 5.2 Focal Loss ($\gamma = 2.0$)
Addresses hard examples and calibration:
$$\text{FL}(p_t) = -\alpha_t (1 - p_t)^\gamma \log(p_t)$$
Where $\gamma = 2.0$, and $\alpha_t$ matches the normalized inverse class weights.

---

## 6. Experimental Matrix (6 Planned Runs)

| Run ID | Experiment Directory | Loss Function | Seed | Epochs | Target Machine |
|---|---|---|---|---|---|
| Run 1 | `runs_m4_v2/UZ-M4-v2-groundnut-s1-wce/` | Weighted CE | Seed 1 (42) | 15 | Acer RTX 4050 |
| Run 2 | `runs_m4_v2/UZ-M4-v2-groundnut-s1-focal/` | Focal ($\gamma=2.0$) | Seed 1 (42) | 15 | Acer RTX 4050 |
| Run 3 | `runs_m4_v2/UZ-M4-v2-groundnut-s2-wce/` | Weighted CE | Seed 2 (1337) | 15 | Acer RTX 4050 |
| Run 4 | `runs_m4_v2/UZ-M4-v2-groundnut-s2-focal/` | Focal ($\gamma=2.0$) | Seed 2 (1337) | 15 | Acer RTX 4050 |
| Run 5 | `runs_m4_v2/UZ-M4-v2-groundnut-s3-wce/` | Weighted CE | Seed 3 (2024) | 15 | Acer RTX 4050 |
| Run 6 | `runs_m4_v2/UZ-M4-v2-groundnut-s3-focal/` | Focal ($\gamma=2.0$) | Seed 3 (2024) | 15 | Acer RTX 4050 |

---

## 7. Hyperparameters & Optimization Schedule

- **Optimizer**: AdamW (`lr=1e-4`, `weight_decay=1e-2`)
- **LR Scheduler**: `CosineAnnealingLR(optimizer, T_max=15, eta_min=1e-6)`
- **Batch Size**: 32 (optimized for 6 GB VRAM on RTX 4050)
- **DataLoader Workers**: 4
- **Precision**: AMP (`torch.cuda.amp.autocast(dtype=torch.float16)`) with `GradScaler`
- **Checkpointing**:
  - `checkpoint_best.pt`: Highest validation Macro-F1
  - `checkpoint_last.pt`: State dict after epoch 15
  - `history.csv`: Per-epoch train loss, val loss, val accuracy, val macro-F1
  - `experiment.json`: Complete hyperparameters, git commit, GPU info, dataset checksum
- **Resume Support**: Restores model, optimizer, scheduler, scaler, epoch, and best metric from `checkpoint_last.pt`.
- **Collision Protection**: Script halts with an error if target run directory already exists and contains a checkpoint, unless `--resume` is explicitly passed.

---

## 8. Hardware & Execution Guardrails

- **Target Hardware**: NVIDIA GeForce RTX 4050 Laptop GPU (6 GB VRAM), CUDA 12.x.
- **CUDA Strict Stop**: The training script will inspect CUDA availability. If CUDA is not detected, it stops immediately. CPU training is prevented to avoid unmetered multi-hour execution, unless `--smoke-test` or `--allow-cpu` is explicitly provided.
- **Controlled Execution Order**:
  1. Transfer package to Acer RTX 4050 via SSH.
  2. Run CUDA Smoke Test (`--smoke-test --epochs 1 --batch-size 4`).
  3. Run Seed 1 WCE.
  4. Run Seed 1 Focal.
  5. Validate results before scaling to remaining seeds.
