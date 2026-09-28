# UZHAVAN model registry

Generated 2026-09-25T10:56:19 from `uzhavan_ml/registry.json` (append-only).

Status legend: **BASELINE** = pre-existing model evaluated, not trained by us · **TRAINED** = trained by us, not independently evaluated · **VALIDATED** = independently evaluated · **PRODUCTION-ELIGIBLE** = passed its fixed gate · **RESEARCH-ONLY** = failed or cannot meet its gate · **BLOCKED** = missing data/access · **PLANNED** = not started.

## Model status (decisions)

| Model | Candidate | Status | Evidence | Why |
|---|---|---|---|---|
| M1 paddy/non-paddy map | [S2,L8,S1]_unet3d checkpoint_last | **RESEARCH-ONLY** | val F1 0.833, paddy IoU 0.612 (227 rows); best-ckpt 0.874 is val-selected | SICKLE farmer-facing gate (licence, scope, protocol) not satisfied; Cauvery Delta only; binary paddy only |
| M1 UTAE variants | [S2]/[L8]/[S2,L8,S1]_utae | **RESEARCH-ONLY (excluded)** | paddy F1 = 0.000: collapsed | degenerate |
| M2 sowing date | [S2,L8,S1]_unet3d checkpoint_last | **RESEARCH-ONLY** | plot MAE 3.00 d (95% CI 1.9–4.3), gate ≤4 met on point estimate; beats no-imagery baseline by 1.2 d (CI −2.4 to −0.2); n=14 plots | SICKLE farmer-facing gate unmet; CI upper bound exceeds the gate |
| M2 transplanting date | [S2,L8,S1]_convlstm checkpoint_last | **RESEARCH-ONLY** | plot MAE 4.70 d (CI 2.9–7.3), gate ≤6 met on point estimate; NOT distinguishable from no-imagery baseline (diff −0.7, CI −2.3 to +0.5); n=14 plots | SICKLE gate unmet; no demonstrated value over the seasonal median |
| M2 harvest date | [L8]_unet3d checkpoint_last | **RESEARCH-ONLY** | plot MAE 8.12 d (CI 5.7–11.0) > gate 7; beats baseline by 4.0 d | fails the fixed gate (best-ckpt 7.77 also fails) |
| M3 plot yield | [S2,L8,S1]_utae_season checkpoint_last | **RESEARCH-ONLY** | MAPE 34%, pixel-sum MAE 565 (units unconfirmed); 37 rows | spec: research-only; yield units unverified |
| M4 leaf disease (6 crops) | EfficientNetV2-S, m4_v1 | **PLANNED (ready for Colab)** | data + splits + package + scripts smoke-tested | awaiting user-run Colab 3-seed training. Only groundnut CAN reach PRODUCTION-ELIGIBLE (only crop with a cross-source test); the other 5 are research-only by design |
| M5 rice disease | - | **BLOCKED** | Paddy Doctor not obtained (0 images) | needs a legitimate IEEE/Kaggle login |
| M6 mandi price forecast | LightGBM quantile (planned) | **PLANNED** | 16 eligible market×commodity pairs (paddy 12, groundnut 3, maize 1); 7 coconut on hold; 2,010 current-price-only | step 9 runs after M4 independent evaluation |
| M7 district yield benchmark | - | **PLANNED** | - | after M6 |
| R1 RAG / W1 weather / S1 soil / V1 speech | - | **PLANNED (evaluation-only)** | - | not trained by design; evaluations pending (speech blocked on consented eval set) |

## Experiments (append-only)

| Experiment ID | Model | Status | Dataset / split | Seed | Hardware | Duration | Key metric | Data-use / licence | Notes |
|---|---|---|---|---|---|---|---|---|---|
| `UZ-SICKLE-BASELINE-v1.0-20260925-7ec31eda` | M1/M2/M3 (SICKLE WACV-2024 checkpoints) authors' WACV-2024 (not trained by us) | **BASELINE** | SICKLE local copy (csv sha256 6f414d88…) / authors' val (227 rows crop_type; 37 rows / 14 plots calendar+yield) | n/a (inference) | Apple M4, 16 GiB | – | crop_type F1 0.833 (last); sowing 3.00 d, transplanting 4.70 d, harvest 8.12 d p | SICKLE data + checkpoints: licence UNVERIFIED; SICKLE code has no licence file (local rese | 72 runs x {last,best} evaluated on authors' val; the only labelled plots unseen in training. checkpoint_best is val-sele |
| `UZ-M4-BENCH-v1.0-20260925` | M4 v1.0 (benchmark) | **benchmark** | m4_v1 / n/a | n/a | Apple M4 (10-core GPU), 16 GiB | – | 24.0 img/s bs32; ~20.0 h for 3 seeds x 30 epochs on M4 | no weights saved; torchvision ImageNet weights downloaded | Throughput only (synthetic batches), run while SICKLE eval used CPU. Confirms cloud GPU for the 3-seed run. WB groundnut |
