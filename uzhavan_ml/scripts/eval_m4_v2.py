"""M4 v2 Independent evaluation script.

Implements M4 v2 evaluation protocol fixes:
1. Closed-set exact-match metrics on scorable cross-source classes (e.g. Groundnut Healthy + Rust, N=720).
2. Open-set precision and F1 accounting for false positives from ALL external samples (N=1,695),
   ensuring false alarms on out-of-taxonomy (Alternaria, Rosette) or coarse classes (Tikka) penalize precision.
3. Coarse Tikka diagnostic reported strictly as an auxiliary complex metric (N=432), never counted as exact early/late ground truth.
4. Out-of-taxonomy rejection metrics on non-target classes (N=543).
5. Fixed UNSURE calibration: eliminates the broken ascending loop starting at 0.0. Supports:
   - 'val_q05': 5th percentile of confidence on correct in-distribution validation predictions.
   - 'val_q01': 1st percentile of confidence on correct in-distribution validation predictions.
   - 'fixed_0.70' / 'fixed_0.75': fixed confidence thresholds.
   - 'v1_zero': legacy 0.0 threshold for backwards compatibility auditing.

usage: python eval_m4_v2.py --pkg PKG --exp EXP_DIR [EXP_DIR ...] --out report_v2.json [--policy val_q05|val_q01|fixed_0.70|fixed_0.75|v1_zero]
"""
import argparse, json
from pathlib import Path
import numpy as np, pandas as pd, torch
from torch.utils.data import DataLoader
import importlib.util, sys

spec = importlib.util.spec_from_file_location("train_m4", Path(__file__).with_name("train_m4.py"))
tm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tm)

F1_GATE, RECALL_GATE, UNSURE_PREC = 0.85, 0.70, 0.90
COARSE = {"groundnut__tikka_leaf_spot": {"groundnut__early_leaf_spot", "groundnut__late_leaf_spot"}}


@torch.no_grad()
def predict(model, df, pkg, classes, dev):
    ds = tm.DS(df.assign(canonical_id=df.canonical_id.where(df.canonical_id.isin(sum(classes.values(), [])), df.crop.map(lambda c: classes[c][0]))),
               pkg, classes, False)
    out = []
    for x, cr, _ in DataLoader(ds, batch_size=64, num_workers=0):
        for l in model(x.to(dev), cr):
            out.append(torch.softmax(l.float(), 0).cpu().numpy())
    return out


def macro_scores(y_true, y_pred, labels):
    """Computes per-class recall, precision, and macro-F1 over specified labels present in y_true."""
    f1, rec, prec = {}, {}, {}
    for j in labels:
        tp = int(((y_pred == j) & (y_true == j)).sum())
        fp = int(((y_pred == j) & (y_true != j)).sum())
        fn = int(((y_pred != j) & (y_true == j)).sum())
        n_pos = int((y_true == j).sum())
        if n_pos > 0:
            rec[j] = float(tp / n_pos)
            prec[j] = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
            denom = 2 * tp + fp + fn
            f1[j] = float(2 * tp / denom) if denom > 0 else 0.0
    mean_f1 = float(np.mean(list(f1.values()))) if f1 else None
    return mean_f1, rec, prec


def calibrate_threshold(conf_val, yh_val, y_val, policy):
    """Calibrate UNSURE threshold on in-distribution validation data strictly."""
    correct_mask = (yh_val == y_val)
    conf_correct = conf_val[correct_mask] if correct_mask.any() else conf_val

    if policy == "val_q05":
        return float(np.percentile(conf_correct, 5))
    elif policy == "val_q01":
        return float(np.percentile(conf_correct, 1))
    elif policy == "fixed_0.70":
        return 0.70
    elif policy == "fixed_0.75":
        return 0.75
    elif policy == "fixed_0.80":
        return 0.80
    elif policy == "v1_zero":
        return 0.0
    else:
        try:
            return float(policy)
        except ValueError:
            raise ValueError(f"Unknown threshold policy: {policy}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pkg", required=True)
    ap.add_argument("--exp", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--policy", default="val_q05", choices=["val_q05", "val_q01", "fixed_0.70", "fixed_0.75", "fixed_0.80", "v1_zero"])
    a = ap.parse_args()

    pkg = Path(a.pkg)
    man = pd.read_csv(pkg / "manifest.csv")
    dev = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    per_seed = []

    for e in a.exp:
        e = Path(e)
        ck = torch.load(e / "checkpoint_best.pt", map_location="cpu", weights_only=False)
        classes = ck["classes"]
        model = tm.Model(classes)
        model.load_state_dict(ck["model"])
        model.to(dev).eval()
        seed_res = {"experiment": e.name}

        for crop in tm.CROPS:
            cl = classes[crop]
            r = {}
            va = man[(man.crop == crop) & (man.split == "val")]
            P_va = np.stack(predict(model, va, pkg, classes, dev))
            y_va = np.array([cl.index(k) for k in va.canonical_id])
            conf_va, yh_va = P_va.max(1), P_va.argmax(1)

            # Calibrate threshold on VAL
            thr = calibrate_threshold(conf_va, yh_va, y_va, a.policy)
            r["unsure_threshold"] = thr
            r["threshold_policy"] = a.policy
            r["val_diagnostics"] = {
                "n": int(len(y_va)),
                "raw_accuracy": float((yh_va == y_va).mean()),
                "coverage_at_threshold": float((conf_va >= thr).mean()),
                "accepted_accuracy": float((yh_va[conf_va >= thr] == y_va[conf_va >= thr]).mean()) if (conf_va >= thr).any() else None,
                "false_rejection_rate": float(((yh_va == y_va) & (conf_va < thr)).sum() / max(1, (yh_va == y_va).sum()))
            }

            # Internal same-source held-out test
            te = man[(man.crop == crop) & (man.split == "test")]
            P_te = np.stack(predict(model, te, pkg, classes, dev))
            y_te = np.array([cl.index(k) for k in te.canonical_id])
            conf_te, yh_te = P_te.max(1), P_te.argmax(1)

            f1_te, rec_te, prec_te = macro_scores(y_te, yh_te, range(len(cl)))
            acc_te_mask = conf_te >= thr
            r["internal_test"] = {
                "n": int(len(y_te)),
                "macro_f1": f1_te,
                "recall": {cl[k]: v for k, v in rec_te.items()},
                "precision": {cl[k]: v for k, v in prec_te.items()},
                "coverage_at_threshold": float(acc_te_mask.mean()),
                "accepted_accuracy": float((yh_te[acc_te_mask] == y_te[acc_te_mask]).mean()) if acc_te_mask.any() else None,
                "false_rejection_rate": float(((yh_te == y_te) & (~acc_te_mask)).sum() / max(1, (yh_te == y_te).sum())),
                "note": "same-source held-out groups (leakage-safe); NOT the production gate"
            }

            # External Cross-Source Test
            ex = man[(man.crop == crop) & (man.split == "external_test")].copy()
            if len(ex):
                P_ex = np.stack(predict(model, ex, pkg, classes, dev))
                yh_ex = P_ex.argmax(1)
                conf_ex = P_ex.max(1)
                pred_labels = [cl[i] for i in yh_ex]

                # Identify sample subsets
                inx_scorable = ex.canonical_id.isin(cl).to_numpy()
                coarse_mask = ex.canonical_id.isin(COARSE).to_numpy()
                oot_mask = ~inx_scorable & ~coarse_mask

                # 1. Closed-set exact-match evaluation on scorable (N=720 for groundnut)
                y_scorable = np.array([cl.index(k) for k in ex.canonical_id[inx_scorable]])
                yh_scorable = yh_ex[inx_scorable]
                conf_scorable = conf_ex[inx_scorable]

                f1_closed, rec_closed, prec_closed = macro_scores(y_scorable, yh_scorable, range(len(cl)))

                # 2. Open-set precision and F1 accounting for false alarms from ALL 1,695 external samples
                open_rec = {}
                open_prec = {}
                open_f1 = {}
                for k in range(len(cl)):
                    cname = cl[k]
                    n_true = int((ex.canonical_id == cname).sum())
                    if n_true > 0:
                        tp = int(((ex.canonical_id == cname) & (yh_ex == k)).sum())
                        fp_all = int(((ex.canonical_id != cname) & (yh_ex == k)).sum())
                        fn = int(((ex.canonical_id == cname) & (yh_ex != k)).sum())
                        open_rec[cname] = float(tp / n_true)
                        open_prec[cname] = float(tp / (tp + fp_all)) if (tp + fp_all) > 0 else 0.0
                        denom = 2 * tp + fp_all + fn
                        open_f1[cname] = float(2 * tp / denom) if denom > 0 else 0.0

                open_macro_f1 = float(np.mean(list(open_f1.values()))) if open_f1 else None

                # 3. Coarse Tikka diagnostic (separate from exact metrics)
                coarse_ok = [p in COARSE[t] for p, t in zip(np.array(pred_labels)[coarse_mask], ex.canonical_id[coarse_mask])]
                tikka_acc_mask = conf_ex[coarse_mask] >= thr
                tikka_accepted_acc = float(np.mean(np.array(coarse_ok)[tikka_acc_mask])) if tikka_acc_mask.any() else None

                # 4. Out-of-taxonomy UNSURE rejection (N=543)
                oot_unsure_rate = float((conf_ex[oot_mask] < thr).mean()) if oot_mask.any() else None

                # 5. Full external confusion matrix across all 1,695 samples
                cm_all = pd.crosstab(ex.canonical_id, pd.Series(pred_labels, name="predicted"), dropna=False).reindex(columns=cl, fill_value=0)

                r["cross_source_test"] = {
                    "n_total_external": int(len(ex)),
                    "n_scorable_exact": int(inx_scorable.sum()),
                    "closed_set_exact": {
                        "macro_f1": f1_closed,
                        "recall": {cl[k]: v for k, v in rec_closed.items()},
                        "precision": {cl[k]: v for k, v in prec_closed.items()},
                        "coverage_at_threshold": float((conf_scorable >= thr).mean()),
                        "accuracy_on_accepted": float((yh_scorable[conf_scorable >= thr] == y_scorable[conf_scorable >= thr]).mean()) if (conf_scorable >= thr).any() else None
                    },
                    "open_set_exact_accounting_all_samples": {
                        "open_macro_f1": open_macro_f1,
                        "recall": open_rec,
                        "open_precision": open_prec,
                        "open_f1": open_f1
                    },
                    "coarse_tikka_diagnostic": {
                        "n_tikka": int(coarse_mask.sum()),
                        "raw_coarse_accuracy": float(np.mean(coarse_ok)) if coarse_mask.any() else None,
                        "accepted_coarse_accuracy": tikka_accepted_acc,
                        "unsure_rate": float((~tikka_acc_mask).mean()) if coarse_mask.any() else None,
                        "note": "Reported separately as an auxiliary complex metric. Never counted as exact early/late ground truth."
                    },
                    "out_of_taxonomy_evaluation": {
                        "n_out_of_taxonomy": int(oot_mask.sum()),
                        "unsure_rate": oot_unsure_rate,
                        "coverage_accepted": float((conf_ex[oot_mask] >= thr).mean()) if oot_mask.any() else None,
                        "classes_present": ex.canonical_id[oot_mask].value_counts().to_dict()
                    },
                    "confusion_matrix_all_1695": cm_all.to_dict("index")
                }
            seed_res[crop] = r
        per_seed.append(seed_res)

    report = {
        "evaluation_version": "m4_v2",
        "threshold_policy": a.policy,
        "gates": {"f1": F1_GATE, "per_disease_recall": RECALL_GATE, "unsure_precision_target": UNSURE_PREC},
        "seeds": per_seed,
        "decision": {}
    }

    for crop in tm.CROPS:
        xs = [s[crop].get("cross_source_test") for s in per_seed]
        if not all(xs):
            report["decision"][crop] = {"status": "RESEARCH-ONLY", "reason": "no_cross_source_test (single source held)"}
            continue
        closed_f1s = [x["closed_set_exact"]["macro_f1"] for x in xs]
        open_f1s = [x["open_set_exact_accounting_all_samples"]["open_macro_f1"] for x in xs]
        min_recs = [min(x["closed_set_exact"]["recall"].values()) for x in xs]

        closed_ok = (np.mean(closed_f1s) >= F1_GATE) and (min(min_recs) >= RECALL_GATE)
        open_ok = (np.mean(open_f1s) >= F1_GATE) and (min(min_recs) >= RECALL_GATE)

        report["decision"][crop] = {
            "status": "PRODUCTION-ELIGIBLE" if (closed_ok and open_ok) else "RESEARCH-ONLY",
            "closed_set_macro_f1_mean": float(np.mean(closed_f1s)),
            "closed_set_macro_f1_sd": float(np.std(closed_f1s)),
            "open_set_macro_f1_mean": float(np.mean(open_f1s)),
            "open_set_macro_f1_sd": float(np.std(open_f1s)),
            "min_per_disease_recall": float(min(min_recs)),
            "coarse_tikka_mean_accuracy": float(np.mean([x["coarse_tikka_diagnostic"]["raw_coarse_accuracy"] for x in xs])),
            "oot_mean_unsure_rate": float(np.mean([x["out_of_taxonomy_evaluation"]["unsure_rate"] for x in xs]))
        }

    with open(a.out, "w") as f:
        json.dump(report, f, indent=1, default=float)
    print(json.dumps(report["decision"], indent=1))


if __name__ == "__main__":
    main()
