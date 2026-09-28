"""Per-plot errors + paired bootstrap CIs for the PRE-SPECIFIED calendar runs (training_specification.md §3 M2),
vs the no-imagery per-season-median baseline. Eval set: authors' VAL rows with YIELD>0 (37 rows). No training."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd, torch
sys.argv = ["x", "--exp_dir", "/tmp/unused"]
sys.path.insert(0, str(Path(__file__).parent))
import eval_sickle_baseline as E
from utils import utae_utils

PRESPEC = {"sowing_date": "[S2,L8,S1]_unet3d", "transplanting_date": "[S2,L8,S1]_convlstm", "harvesting_date": "[L8]_unet3d"}
OUT = Path.home() / "Desktop/agri/uzhavan_ml/experiments/UZ-SICKLE-BASELINE-v1.0-20260925-7ec31eda/calendar_ci.json"
df = pd.read_csv(E.DATA_DIR / "sickle_dataset_tabular.csv")
tr = df[(df.SPLIT == "train") & (df.YIELD > 0)]; va = df[(df.SPLIT == "val") & (df.YIELD > 0)].reset_index(drop=True)
rng = np.random.default_rng(0); res = {}
for task, run in PRESPEC.items():
    rd = E.RUNS / task / run; cfg = E.load_cfg(rd); ti = E.CAL_TASKS.index(task) + 2
    ds = E.SICKLE_Dataset(df=va, data_dir=str(E.DATA_DIR), satellites=cfg.satellites, ignore_index=E.IGNORE, actual_season=False)
    # train medians per season (same masking)
    h = E.SICKLE_Dataset(df=tr, data_dir=str(E.DATA_DIR), satellites=cfg.satellites)
    tv = []
    for _, r in tr.iterrows():
        m = h._read_masks(int(r.UNIQUE_ID)).transpose(1, 2, 0); m = h.resize(image=m)["image"].transpose(2, 0, 1)
        for pid in np.unique(m[0]):
            sel = (m[0] == pid) & (m[ti] != E.IGNORE)
            if pid != E.IGNORE and pid in set(tr.PLOT_ID) and sel.any(): tv.append((r.STANDARD_SEASON, float(m[ti][sel].mean())))
    tv = pd.DataFrame(tv, columns=["s", "d"]); med = tv.groupby("s").d.median().to_dict(); allm = tv.d.median()
    rows = []
    models = {ck: E.build_model(cfg, rd / f"{ck}.pth.tar")[0] for ck in ("checkpoint_last", "checkpoint_best")}
    with torch.no_grad():
        for i in range(len(ds)):
            data, masks = utae_utils.pad_collate([ds[i]], pad_value=cfg.pad_value)
            pm, t = masks["plot_mask"][0], masks[task][0].float()
            preds = {ck: m(data)[0, 0] for ck, m in models.items()}
            for pid in torch.unique(pm):
                sel = (pm == pid) & (t != E.IGNORE)
                if pid == E.IGNORE or sel.sum() == 0: continue
                truth = float(t[sel].mean())
                rows.append({"uid": int(va.UNIQUE_ID[i]), "plot": int(pid), "truth": truth,
                             "baseline": med.get(va.STANDARD_SEASON[i], allm),
                             **{ck: float(p[sel].mean()) for ck, p in preds.items()}})
    d = pd.DataFrame(rows)
    for c in ("checkpoint_last", "checkpoint_best", "baseline"): d[f"ae_{c}"] = (d[c] - d.truth).abs()
    plots = d["plot"].unique(); B = []
    for _ in range(5000):                                 # cluster bootstrap over plots
        s = \
            pd.concat([d[d["plot"] == p] for p in rng.choice(plots, len(plots), replace=True)])
        B.append([s.ae_checkpoint_last.mean(), s.ae_checkpoint_best.mean(), s.ae_baseline.mean(), (s.ae_checkpoint_last - s.ae_baseline).mean()])
    B = np.array(B); ci = lambda k: [float(np.percentile(B[:, k], 2.5)), float(np.percentile(B[:, k], 97.5))]
    res[task] = {"run": run, "n_instances": len(d), "n_plots": int(len(plots)),
                 "mae_last": float(d.ae_checkpoint_last.mean()), "ci95_last": ci(0),
                 "mae_best": float(d.ae_checkpoint_best.mean()), "ci95_best": ci(1),
                 "mae_baseline": float(d.ae_baseline.mean()), "ci95_baseline": ci(2),
                 "diff_last_minus_baseline": float((d.ae_checkpoint_last - d.ae_baseline).mean()), "ci95_diff": ci(3),
                 "gate_mae_days": E.GATES[task], "within7_last": float((d.ae_checkpoint_last <= 7).mean())}
    d.to_csv(OUT.with_name(f"calendar_instances_{task}.csv"), index=False)
    print(task, json.dumps(res[task]), flush=True)
json.dump(res, open(OUT, "w"), indent=1)
