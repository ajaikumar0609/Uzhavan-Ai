# UZHAVAN training results (2026-09-25)

**Models trained by us so far: 0.** Everything below is BASELINE (evaluated, not trained), READY (prepared and smoke-tested) or BLOCKED.
Registry: `model_registry.md`. SICKLE evaluation details: `evaluation_report.md`.

## Status by approved step
| # | Step | Status | Output |
|---|---|---|---|
| 1 | SICKLE independent split | ✅ done | `uzhavan_data/01_sickle/processed/splits/sickle_split_v1.{csv,json}`: train 284 / val 36 / test 31 plots; 0 plots cross splits; seed 20260925 |
| 2 | Evaluate existing SICKLE checkpoints | ✅ done | `UZ-SICKLE-BASELINE-v1.0-20260925-7ec31eda` (144 evaluations) |
| 3 | Baseline report | ✅ done | `evaluation_report.md`: all SICKLE models RESEARCH-ONLY |
| 4 | Disease processed dataset | ✅ done | `uzhavan_data/06_disease_pest/processed/m4_v1/`: 29,160 kept / 381 quarantined |
| 5 | M4 splits | ✅ done | group-aware 70/15/15 + groundnut cross-source test (West Bengal, 1,695 images) |
| 6 | EfficientNetV2-S benchmark | ✅ done | `UZ-M4-BENCH-v1.0-20260925`: 24 img/s on M4 (bs32, 6.8 GB) → ~20 h for 3 seeds locally |
| 7 | 3-seed training (Colab GPU) | ⏳ **waiting on you** | `packages/m4_v1_colab.zip` + `UZHAVAN_M4_train_colab.ipynb` (smoke-tested locally) |
| 8 | Independent M4 evaluation | ⏳ after 7 | `scripts/eval_m4.py` (smoke-tested) |
| 9 | M6 market | eligibility done; training after 8 | `uzhavan_data/08_market/processed/m6_eligibility_v1.csv`: 16 eligible pairs |
| 10 | Calendar models | ✅ evaluated (step 2) | harvest fails the gate; fine-tuning decision pending (evaluation_report §5) |
| 11 | RAG / weather / soil / speech | evaluation-only, not started | – |

## M4 data (dataset_version `m4_v1`, split_version `m4_v1_split_seed20260925`)
Pipeline: raw → exact duplicates (sha256) → near-duplicate groups (pHash ≤ 6 bits, union-find per crop across sources) → conflicting-label groups quarantined → group-aware stratified split → processed manifest. Raw files are untouched.

| Crop | Source (primary) | train | val | test | cross-source test | Classes |
|---|---|---|---|---|---|---|
| banana | VIT Chennai (TN) | 6,261 | 1,342 | 1,346 | **none** | 8 |
| coconut | Pune (MH) | 3,993 | 872 | 866 | **none** | 5 (no healthy class) |
| groundnut | VIT Chennai (TN) | 5,920 | 1,267 | 1,276 | **West Bengal, 1,695** | 5 |
| sugarcane | Maharashtra | 1,615 | 346 | 350 | **none** | 5 |
| black gram | Andhra Pradesh | 702 | 151 | 152 | **none** | 5 |
| chilli | VIT Chennai (TN) | 701 | 150 | 155 | **none** | 6 |

Quarantined (381): 240 exact duplicates, 72 images in 34 conflicting-label groups, 69 VIT multi-label or no-box images. 6,775 near-duplicate pairs are kept inside single splits (verified: 0 groups cross splits).
Groundnut cross-source scoring: healthy and rust are scored exactly (720 images). The WB "tikka" label (the source's merged early+late leaf spot) is normalised to `groundnut_tikka_leaf_spot` and scored **coarsely** (432 images; no etiology claim). WB alternaria and rosette are **not in the training taxonomy** (543 images) and are reported as out-of-taxonomy; they should come back UNSURE.

## Bugs caught before any GPU time was spent
1. `train_m4.py` built each crop's classes from the whole manifest, so external-test-only classes got output heads. **Fixed:** the taxonomy now comes from the train split only (34 classes).
2. Class imbalance was corrected twice (sampler + loss weights). **Fixed:** sampler only.
3. The package's image paths pointed at `raw/` instead of `raw/extracted/`. **Fixed:** the build now asserts that all 29,541 paths exist.
4. The SICKLE no-imagery baseline was scored on the wrong plot set. **Fixed** and recomputed (evaluation_report §6).

## Critical finding for the M4 production gate
The approved gate needs an **independent cross-source test per crop**. Only groundnut has two sources. **Banana, coconut, sugarcane, black gram and chilli are therefore RESEARCH-ONLY regardless of their scores.** The gate has not been changed. They will still be trained and reported on their same-source held-out test for research. Getting them to production needs one additional independent, licence-compatible dataset per crop.

## Training code v1.1: epoch-level resume (2026-09-25)
- The protocol is unchanged (byte-identical data/model/loss/eval code and hyperparameters; same config hash). Only checkpointing and resume changed.
- Seed 1 runs on **v1.0** (the legacy script is archived at `scripts/archive/train_m4_v1.0_seed1_legacy.py`, identical to the script inside `m4_v1_colab.zip`). v1.1 is used from Seed 2 onward. Because the protocol is identical, all 3 seeds remain comparable. The code version is recorded per experiment.
- Local resume tests: **21/21 pass** (`experiments/resume_tests_train_m4_v1.1.json`), including an exact match between an interrupted+resumed run and an uninterrupted one.
- New files: `packages/m4_v1_code_v1.1.zip` (train_m4.py, test_m4_resume.py, the v1.1 notebook, README_RESUME.md) and `packages/UZHAVAN_M4_train_colab_v1.1.ipynb`.
