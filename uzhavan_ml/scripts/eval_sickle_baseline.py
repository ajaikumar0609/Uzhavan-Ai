"""BASELINE evaluation of the existing WACV-2024 SICKLE checkpoints. No training.

Protocol (training_specification.md §7.1):
  * evaluation set = authors' VAL plots (the only labelled plots the checkpoints never trained on)
  * checkpoint_last = primary (end of a fixed 100-epoch schedule); checkpoint_best = secondary (selected on val, so optimistic)
  * metrics = SICKLE's own get_metrics (pixel level) + plot-instance level MAE in days for the calendar tasks
  * reference baseline for calendar tasks = per-season median of TRAIN labels (no imagery)
Uses the official SICKLE code (external/SICKLE, commit c496cee; no licence file, local research use only).
"""
import argparse, json, os, sys, time, glob, re, platform, warnings
from pathlib import Path
from types import SimpleNamespace
import numpy as np, pandas as pd, torch, torch.nn as nn

warnings.filterwarnings("ignore")
AGRI = Path.home() / "Desktop/agri"
SICKLE_CODE = AGRI / "external/SICKLE"
sys.path.insert(0, str(SICKLE_CODE))
from utils.dataset import SICKLE_Dataset          # noqa: E402  (official code, unmodified)
from utils import utae_utils, model_utils         # noqa: E402
from utils.metric import get_metrics              # noqa: E402

DATA_DIR = AGRI / "sickle_dataset"
RUNS = AGRI / "runs/wacv_2024"
CAL_TASKS = ["sowing_date", "transplanting_date", "harvesting_date"]
GATES = {"sowing_date": 4.0, "transplanting_date": 6.0, "harvesting_date": 7.0}   # MAE days, fixed before results
IGNORE = -999


def load_cfg(run_dir):
    c = json.load(open(run_dir / "conf.json"))
    cfg = SimpleNamespace(**c)
    cfg.device = "cpu"
    for k in ["encoder_widths", "decoder_widths", "out_conv"]:
        v = getattr(cfg, k)
        if isinstance(v, str):
            setattr(cfg, k, [int(x) for x in re.sub(r"[\[\]\s]", "", v).split(",")])
    cfg.satellites = {s: {**m, "img_size": tuple(m["img_size"])} for s, m in cfg.satellites.items()}
    cfg.img_size = tuple(cfg.img_size)
    return cfg


def build_model(cfg, ckpt_path):
    m = model_utils.Fusion_model(cfg)
    state = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    m.load_state_dict(state["model"])
    m.eval()
    return m, {k: state.get(k) for k in ("epoch",) if k in state}


def plot_instances(pred, true, pmask):
    """Mean prediction per (chip, plot-index) region with a valid label. pred/true/pmask: B x H x W."""
    out = []
    for b in range(true.shape[0]):
        for pid in torch.unique(pmask[b]):
            if pid == IGNORE:
                continue
            sel = (pmask[b] == pid) & (true[b] != IGNORE)
            if sel.sum() == 0:
                continue
            out.append((float(pred[b][sel].mean()), float(true[b][sel].float().mean())))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exp_dir", required=True)
    ap.add_argument("--limit", type=int, default=0, help="debug: only first N val rows")
    args = ap.parse_args()
    exp = Path(args.exp_dir); exp.mkdir(parents=True, exist_ok=True)
    df_all = pd.read_csv(DATA_DIR / "sickle_dataset_tabular.csv")

    # group runs by (task family, satellites, actual_season) so each dataset is read once
    runs = [Path(p).parent for p in sorted(glob.glob(str(RUNS / "*/*/conf.json"))) if "debug" not in p]
    groups = {}
    for rd in runs:
        cfg = load_cfg(rd)
        fam = "crop_type" if cfg.task == "crop_type" else "regression"
        key = (fam, tuple(cfg.satellites), bool(getattr(cfg, "actual_season", False)))
        groups.setdefault(key, []).append((rd, cfg))

    # train-label medians per season for the no-imagery calendar baseline (mask space, read masks only)
    tr = df_all[(df_all.SPLIT == "train") & (df_all.YIELD > 0)]
    helper = SICKLE_Dataset(df=tr, data_dir=str(DATA_DIR), satellites={"S2": {"bands": ["B2"], "mask_res": 10, "img_size": (32, 32)}})
    tr_vals = {t: [] for t in CAL_TASKS}
    for _, r in tr.iterrows():
        m = helper._read_masks(int(r.UNIQUE_ID)).transpose(1, 2, 0)
        m = helper.resize(image=m)["image"].transpose(2, 0, 1)
        own = m[0]; plot_ids = set(tr.PLOT_ID)
        for i, t in enumerate(CAL_TASKS, start=2):
            v = m[i][(own != IGNORE) & (m[i] != IGNORE) & np.isin(own, list(plot_ids))]
            if v.size: tr_vals[t].append((r.STANDARD_SEASON, float(np.median(v))))
    med = {t: {**pd.DataFrame(v, columns=["s", "d"]).groupby("s").d.median().to_dict(),
               "_all": float(np.median([d for _, d in v]))} for t, v in tr_vals.items()}

    results = []
    for (fam, sats, act), members in sorted(groups.items()):
        val = df_all[df_all.SPLIT == "val"]
        if fam == "regression":
            val = val[val.YIELD > 0]
        val = val.reset_index(drop=True)
        if args.limit: val = val.head(args.limit)
        cfg0 = members[0][1]
        ds = SICKLE_Dataset(df=val, data_dir=str(DATA_DIR), satellites=cfg0.satellites, ignore_index=IGNORE, actual_season=act)
        loader = torch.utils.data.DataLoader(ds, batch_size=16, shuffle=False, num_workers=0,
                                             collate_fn=lambda x: utae_utils.pad_collate(x, pad_value=cfg0.pad_value))
        models = []
        for rd, cfg in members:
            for ck in ("checkpoint_last", "checkpoint_best"):
                m, meta = build_model(cfg, rd / f"{ck}.pth.tar")
                models.append({"run": rd.name, "task": cfg.task, "ckpt": ck, "model": m, "arch": cfg.model, "meta": meta,
                               "preds": [], "targets": [], "pmasks": [], "inst": []})
        t0 = time.time()
        with torch.no_grad():
            for data, masks in loader:
                for mm in models:
                    y = mm["model"](data)
                    tgt = masks[mm["task"]]
                    if mm["task"] == "crop_type":
                        y = nn.Softmax(dim=1)(y); tgt = tgt.long()
                    else:
                        tgt = tgt.float()
                        if mm["task"] in CAL_TASKS:
                            mm["inst"] += plot_instances(y[:, 0], tgt, masks["plot_mask"])
                    mm["preds"].append(y); mm["targets"].append(tgt); mm["pmasks"].append(masks["plot_mask"])
        for mm in models:
            P, T, PM = torch.cat(mm["preds"]), torch.cat(mm["targets"]), torch.cat(mm["pmasks"])
            met = get_metrics(P, T, PM, ignore_index=IGNORE, task=mm["task"])
            if mm["task"] == "crop_type":
                names = ["f1_macro", "acc", "iou", "f1_paddy", "f1_non_paddy", "acc_paddy", "acc_non_paddy", "iou_paddy", "iou_non_paddy"]
                r = {n: float(v) for n, v in zip(names, met[:9])}
            else:
                rmse, mae, mape = met
                r = {"pixel_rmse": float(rmse), "pixel_mae": float(mae), "sickle_mape": float(mape)}
                if mm["task"] in CAL_TASKS and mm["inst"]:
                    e = np.array([abs(p - t) for p, t in mm["inst"]])
                    r.update(plot_mae_days=float(e.mean()), plot_median_ae_days=float(np.median(e)),
                             plot_within_7d=float((e <= 7).mean()), n_plot_instances=int(len(e)),
                             gate_mae_days=GATES[mm["task"]], passes_gate=bool(e.mean() <= GATES[mm["task"]]))
            results.append({"task": mm["task"], "run": mm["run"], "arch": mm["arch"], "satellites": list(sats),
                            "actual_season": act, "checkpoint": mm["ckpt"], "n_val_rows": len(val), **r})
        print(f"group {fam} {sats} season={act}: {len(models)} models, {len(val)} rows, {time.time()-t0:.0f}s", flush=True)
        json.dump(results, open(exp / "results_partial.json", "w"), indent=1)

    # calendar no-imagery baseline on the same val plot instances (use one model's targets: identical across runs)
    base = {}
    for t in CAL_TASKS:
        val = df_all[(df_all.SPLIT == "val") & (df_all.YIELD > 0)]
        errs = []
        for _, r in val.iterrows():
            m = helper._read_masks(int(r.UNIQUE_ID)).transpose(1, 2, 0)
            m = helper.resize(image=m)["image"].transpose(2, 0, 1)
            i = CAL_TASKS.index(t) + 2
            pm, tv = m[0], m[i]
            pred = med[t].get(r.STANDARD_SEASON, med[t]["_all"])
            valid_plots = set(val.PLOT_ID)            # same masking as SICKLE_Dataset: plots outside the eval set are ignored
            for pid in np.unique(pm):
                sel = (pm == pid) & (tv != IGNORE) & (pm != IGNORE)
                if pid != IGNORE and pid in valid_plots and sel.any(): errs.append(abs(pred - float(tv[sel].mean())))
        e = np.array(errs)
        base[t] = {"plot_mae_days": float(e.mean()), "plot_within_7d": float((e <= 7).mean()), "n_plot_instances": int(len(e)),
                   "method": "per-season median of TRAIN plot labels (no imagery)"}
    env = {"python": sys.version.split()[0], "torch": torch.__version__, "device": "cpu",
           "machine": platform.machine(), "platform": platform.platform(), "sickle_code_commit": "c496cee8aadc5b6b61312f5ddb9b060f09555539"}
    json.dump({"results": results, "calendar_no_imagery_baseline": base, "env": env,
               "split_version": "authors_val (see sickle_split_v1.json)", "protocol": "training_specification.md §7.1"},
              open(exp / "results.json", "w"), indent=1)
    print("done", len(results))


if __name__ == "__main__":
    main()
