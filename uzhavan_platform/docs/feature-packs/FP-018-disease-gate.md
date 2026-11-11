# FP-018: Disease model integration gate

**Status:** `BLOCKED: model not yet evaluated` (gate review 2026-09-25) · **Decision: DISEASE SCAN = MODEL UNAVAILABLE**
**Owner:** Master Agent · **Depends on:** M4 3-seed Colab training (user-run) → independent evaluation on the Mac (`uzhavan_ml/scripts/eval_m4.py`)

## 1. Gate checks (training_specification.md §7, fixed before results)
| # | Requirement | Evidence found on 2026-09-25 | Result |
|---|---|---|---|
| G1 | 3 completed seeds (experiment.json status completed/experiment) | No `UZ-M4-v1.0-*-s1/2/3` directory and no `checkpoint_best.pt` anywhere under `~/Desktop/agri`, `~/Downloads` or `~/Desktop`. The Colab `runs/` folder hasn't been downloaded | ❌ not met |
| G2 | Independent evaluation (`eval_m4.py`) on the internal group-split test | not run (no checkpoints) | ❌ |
| G3 | Cross-source test: per-crop macro-F1 ≥ 0.85 | not run. By design only groundnut has a cross-source set, so banana, coconut, sugarcane, black gram and chilli are **research-only** regardless | ❌ |
| G4 | Per-disease recall ≥ 0.70 | not run | ❌ |
| G5 | UNSURE threshold calibrated on val (≥ 0.90 precision on accepted predictions) | implemented in `eval_m4.py`; not run | ❌ |
| G6 | No M4 v2 / root-cause work to review | none exists in the repository | n/a |

## 2. What the app does now (enforced in code, not by convention)
- Backend `POST /api/disease/scan` → **503 `model_unavailable`** while `DISEASE_MODEL_APPROVED=false` (the default). The model service is never called.
- Flutter Scan: crop picker, camera/gallery, own-photo preview and upload progress are all real. The result is the **"Validated disease model unavailable"** state. There's no diagnosis, confidence, class or dose.
- No M4 checkpoint (including a partially trained Seed 1) may be wired in. Promotion needs G1–G5 met **and** an entry in `uzhavan_ml/model_status.json` set to `PRODUCTION-ELIGIBLE` for that crop.

## 3. Unblocking steps (for the project owner)
1. Finish the Colab seeds (notebook v1.1 resumes automatically) and download `MyDrive/uzhavan_m4/runs/` to `~/Desktop/agri/uzhavan_ml/runs_m4/`.
2. The Master runs `eval_m4.py --exp <3 seed dirs>`, then records the per-crop decision in `model_status.json` and `evaluation_report.md`.
3. Only crops marked PRODUCTION-ELIGIBLE (at most groundnut in v1) get `DISEASE_MODEL_APPROVED=true` plus a crop allow-list. Other crops keep returning UNSURE/unavailable.
