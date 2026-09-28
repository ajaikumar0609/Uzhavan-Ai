"""Independent M4 evaluation on the Mac (run AFTER cloud training; never used for model selection).

Gates (training_specification.md §7, fixed before results):
  per crop: macro-F1 >= 0.85 on an INDEPENDENT CROSS-SOURCE test  AND  per-disease recall >= 0.70
  -> otherwise the crop is research-only. A crop with no cross-source test cannot pass (reported as 'no_cross_source_test').
UNSURE: per-crop confidence threshold chosen on VAL as the lowest threshold giving >= 0.90 precision on accepted predictions.
Cross-source groundnut test (VIT-trained -> West Bengal images): only classes that exist in training are scorable.
  healthy, rust: exact match. WB 'tikka' (early+late merged by the source): scored COARSELY as correct if the model predicts
  early_leaf_spot or late_leaf_spot (reported separately; no claim about etiology). WB alternaria/rosette: not in training
  taxonomy -> reported as out-of-taxonomy (should ideally be UNSURE), excluded from F1.
usage: python eval_m4.py --pkg PKG --exp EXP_DIR [EXP_DIR ...] --out report.json
"""
import argparse, json
from pathlib import Path
import numpy as np, pandas as pd, torch
from torch.utils.data import DataLoader
import importlib.util, sys

spec = importlib.util.spec_from_file_location("train_m4", Path(__file__).with_name("train_m4.py"))
tm = importlib.util.module_from_spec(spec); spec.loader.exec_module(tm)
F1_GATE, RECALL_GATE, UNSURE_PREC = 0.85, 0.70, 0.90
COARSE = {"groundnut__tikka_leaf_spot": {"groundnut__early_leaf_spot", "groundnut__late_leaf_spot"}}


@torch.no_grad()
def predict(model, df, pkg, classes, dev):
    ds = tm.DS(df.assign(canonical_id=df.canonical_id.where(df.canonical_id.isin(sum(classes.values(), [])), df.crop.map(lambda c: classes[c][0]))),
               pkg, classes, False)
    out = []
    for x, cr, _ in DataLoader(ds, batch_size=64, num_workers=0):
        out += [torch.softmax(l.float(), 0).cpu().numpy() for l in model(x.to(dev), cr)]
    return out


def macro(y, yh, labels):
    f1, rec = {}, {}
    for j in labels:
        tp = ((yh == j) & (y == j)).sum(); fp = ((yh == j) & (y != j)).sum(); fn = ((yh != j) & (y == j)).sum()
        if (y == j).sum():
            f1[j] = 2 * tp / max(2 * tp + fp + fn, 1); rec[j] = tp / (y == j).sum()
    return float(np.mean(list(f1.values()))) if f1 else None, {k: float(v) for k, v in rec.items()}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--pkg", required=True); ap.add_argument("--exp", nargs="+", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args(); pkg = Path(a.pkg); man = pd.read_csv(pkg / "manifest.csv")
    dev = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    per_seed = []
    for e in a.exp:
        e = Path(e); ck = torch.load(e / "checkpoint_best.pt", map_location="cpu", weights_only=False); classes = ck["classes"]
        model = tm.Model(classes); model.load_state_dict(ck["model"]); model.to(dev).eval()
        seed_res = {"experiment": e.name}
        for crop in tm.CROPS:
            cl = classes[crop]; r = {}
            va = man[(man.crop == crop) & (man.split == "val")]
            pv = predict(model, va, pkg, classes, dev); yv = np.array([cl.index(k) for k in va.canonical_id]); P = np.stack(pv)
            conf, yh = P.max(1), P.argmax(1)
            thr = 1.0
            for t in np.linspace(0, 0.99, 100):             # lowest threshold reaching the precision target on VAL
                acc = conf >= t
                if acc.sum() and (yh[acc] == yv[acc]).mean() >= UNSURE_PREC: thr = float(t); break
            r["unsure_threshold"] = thr
            te = man[(man.crop == crop) & (man.split == "test")]
            P = np.stack(predict(model, te, pkg, classes, dev)); y = np.array([cl.index(k) for k in te.canonical_id]); yh = P.argmax(1)
            f1, rec = macro(y, yh, range(len(cl)))
            r["internal_test"] = {"n": int(len(y)), "macro_f1": f1, "recall": {cl[k]: v for k, v in rec.items()},
                                  "coverage_at_threshold": float((P.max(1) >= thr).mean()),
                                  "accuracy_on_accepted": float((yh[P.max(1) >= thr] == y[P.max(1) >= thr]).mean()) if (P.max(1) >= thr).any() else None,
                                  "note": "same-source held-out groups (leakage-safe); NOT the production gate"}
            ex = man[(man.crop == crop) & (man.split == "external_test")]
            if len(ex):
                P = np.stack(predict(model, ex, pkg, classes, dev)); yh = P.argmax(1); pred = [cl[i] for i in yh]
                inx = ex.canonical_id.isin(cl).to_numpy()
                coarse = ex.canonical_id.isin(COARSE).to_numpy()
                y_in = np.array([cl.index(k) for k in ex.canonical_id[inx]])
                f1x, recx = macro(y_in, yh[inx], range(len(cl)))
                coarse_ok = [p in COARSE[t] for p, t in zip(np.array(pred)[coarse], ex.canonical_id[coarse])]
                ooT = ~inx & ~coarse
                r["cross_source_test"] = {"n_scorable_exact": int(inx.sum()), "macro_f1_exact_classes": f1x,
                    "recall": {cl[k]: v for k, v in recx.items()},
                    "tikka_coarse_accuracy": float(np.mean(coarse_ok)) if coarse.any() else None, "n_tikka": int(coarse.sum()),
                    "out_of_taxonomy_n": int(ooT.sum()), "out_of_taxonomy_unsure_rate": float((P.max(1)[ooT] < thr).mean()) if ooT.any() else None}
            seed_res[crop] = r
        per_seed.append(seed_res)
    # aggregate over seeds + gate decision
    report = {"seeds": per_seed, "gates": {"f1": F1_GATE, "per_disease_recall": RECALL_GATE, "unsure_precision_target": UNSURE_PREC}, "decision": {}}
    for crop in tm.CROPS:
        xs = [s[crop].get("cross_source_test") for s in per_seed]
        if not all(xs):
            report["decision"][crop] = {"status": "RESEARCH-ONLY", "reason": "no_cross_source_test (single source held)"}; continue
        f1s = [x["macro_f1_exact_classes"] for x in xs]; minrec = [min(x["recall"].values()) for x in xs]
        ok = np.mean(f1s) >= F1_GATE and min(minrec) >= RECALL_GATE
        report["decision"][crop] = {"status": "PRODUCTION-ELIGIBLE" if ok else "RESEARCH-ONLY",
            "cross_source_macro_f1_mean": float(np.mean(f1s)), "cross_source_macro_f1_sd": float(np.std(f1s)), "min_per_disease_recall": float(min(minrec))}
    json.dump(report, open(a.out, "w"), indent=1, default=float); print(json.dumps(report["decision"], indent=1))


if __name__ == "__main__":
    main()
