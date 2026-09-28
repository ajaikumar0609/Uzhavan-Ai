# UZHAVAN evaluation report (2026-09-25)

Scope: steps 1–2 of the approved order (the SICKLE independent split + baseline evaluation). No model was trained.
Experiment: `UZ-SICKLE-BASELINE-v1.0-20260925-7ec31eda` (`uzhavan_ml/experiments/…`). The script, raw results, per-plot errors and CIs are all in that folder.

## 1. Protocol (as corrected at sign-off, spec §7.1)
- The WACV checkpoints were trained on the SICKLE **train** plots. The only labelled plots they never trained on are the authors' **val** plots. So:
  - evaluation set = authors' val: 227 rows for crop type; **37 rows / 14 plots** for calendar and yield (SICKLE evaluates these tasks only on rows with yield > 0).
  - **primary = `checkpoint_last`** (end of the fixed 100-epoch schedule). `checkpoint_best` was chosen on these same val plots, so it is optimistic and shown for reference only.
  - Gate decisions use the runs **named in the spec before this evaluation** (not the best-looking run afterwards).
- `sickle_split_v1` (our plot-disjoint test: 31 plots / 201 rows, 0 plots crossing splits) is frozen for **future retraining only**.
- The 206 author-held-out test rows were not used (no labels).
- The calendar gate metric is **plot-level MAE in days**: the mean prediction over each plot's pixels vs the plot's label, computed with single-sample inference (production-like). No-imagery baseline = per-season median of the train labels. Uncertainty = 95% cluster-bootstrap over plots (5,000 resamples).
- Code: the official SICKLE repo (commit c496cee, **no licence file**, local research use only), unmodified. It was run on CPU.

## 2. Reproduction check
Our val numbers for `checkpoint_last` match the authors' trainlogs closely (e.g. fused UNet3D crop-type macro-F1 **0.833** here vs **0.839** logged). The checkpoints load and behave as published.

## 3. Results

### M1: paddy vs non-paddy (binary; not a 21-crop classifier)
| Run (checkpoint_last) | macro-F1 | paddy F1 | paddy IoU | paddy recall | non-paddy recall |
|---|---|---|---|---|---|
| **[S2,L8,S1]_unet3d** (pre-specified) | **0.833** | 0.759 | 0.612 | 0.901 | 0.853 |
| [S1]_unet3d (pre-specified alternative) | 0.820 | 0.746 | 0.595 | 0.925 | 0.827 |
| (ref.) [S2,L8,S1]_unet3d checkpoint_best | 0.874 | 0.803 | 0.671 | 0.739 | 0.968 |

UTAE: 3 of 4 runs are **collapsed** (paddy F1 = 0.000 in both checkpoints for S2, L8 and fused). They are excluded. The sign-off set no numeric gate for M1.

### M2: crop calendar (14 val plots, 41 plot instances)
| Task | Run (pre-specified) | MAE last (95% CI) | Gate | No-imagery baseline | Model − baseline (95% CI) | Within ±7 d | Point gate |
|---|---|---|---|---|---|---|---|
| Sowing | [S2,L8,S1]_unet3d | **3.00 d** (1.9–4.3) | ≤ 4 | 4.22 d | **−1.2** (−2.4 to −0.2) | 83% | met |
| Transplanting | [S2,L8,S1]_convlstm | **4.70 d** (2.9–7.3) | ≤ 6 | 5.41 d | −0.7 (−2.3 to +0.5) | 80% | met |
| Harvest | [L8]_unet3d | **8.12 d** (5.7–11.0) | ≤ 7 | 12.12 d | **−4.0** (−6.0 to −1.9) | 56% | **FAILED** |

(`checkpoint_best` for reference: sowing 2.81, transplanting 4.79, harvest 7.77, which also fails.)

### M3: plot yield
The pre-specified [S2,L8,S1]_utae_season (last): MAPE **34%**, plot-sum MAE 565 (units **unconfirmed**), 37 rows. Research-only by spec.

## 4. Decisions (thresholds were fixed before the results)
| Model | Status | Reason |
|---|---|---|
| M1 paddy map | **RESEARCH-ONLY** | SICKLE farmer-facing gate (licence, units, scope, protocol, uncertainty) not satisfied; Cauvery Delta only |
| M2 sowing | **RESEARCH-ONLY** | Meets the accuracy gate on its point estimate and beats the baseline, but the CI upper bound (4.3) exceeds the gate and the SICKLE gate is unmet |
| M2 transplanting | **RESEARCH-ONLY** | Meets the point gate but is **not demonstrably better than guessing the seasonal median**; the SICKLE gate is unmet |
| M2 harvest | **RESEARCH-ONLY** | **Fails** the ≤7 d gate |
| M3 yield | **RESEARCH-ONLY** | By spec; yield units unverified |

## 5. What this means for fine-tuning (the "only retrain if the baseline requires it" question)
- **The binding constraint is evaluation power, not the model.** 14 val plots cannot confirm a 4–7 day gate: every CI is 2–5 days wide. Retraining on `sickle_split_v1` would make a genuinely independent 31-plot test (28 paddy-yield rows) available, but that is still small.
- Harvest is the one task where fine-tuning could plausibly move a gate decision: it's 1.1 d over the gate with a clear signal (4 d better than the baseline).
- Recommendation **[DECIDE]**: (a) don't fine-tune now. Resolve the SICKLE licence/units gate first, because without it no SICKLE output can reach farmers regardless of accuracy. (b) If fine-tuning is approved, retrain the pre-specified architectures on `sickle_split_v1` train (3 seeds; the 6.2 M-param UNet3D is feasible on the Mac or Colab) and report on the split_v1 test **once**.

## 6. Reproducibility notes
- SICKLE predictions depend slightly on **batch composition** (time-series padding): sowing 2.92 d batched vs 3.00 d single-sample. The gate uses single-sample, which is how production would run. No decision changes.
- The first no-imagery baseline was computed on the wrong plot set (it included neighbouring plots that SICKLE masks out: 137 vs 41 instances). It was caught, fixed and recomputed. The invalid version is kept in `results.json` under `calendar_no_imagery_baseline_v0_INVALID` for audit.
