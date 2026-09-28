"""UZHAVAN AI - M4 V2.3.1 Standalone Evaluator.
NO TRAINING - EVALUATION ONLY.

Evaluates M4 V2.3.1 checkpoint (UZ-M4-v2.3.1-groundnut-s1-triclass-balance) against:
1. Primary Benchmark: Untouched Final External Test (N=928 scorable / N=1,360 total)
2. Historical Replication Benchmark: Full Canonical External Test (N=1,152 scorable / N=1,695 total)

Generates:
- reports/artifacts/m4_v2_3_1_s1_metrics.json
- reports/artifacts/m4_v2_3_1_s1_confusion.csv
- reports/artifacts/m4_v2_3_1_s1_comparison.csv
- reports/artifacts/m4_v2_3_1_s1_error_cases.csv
"""

import argparse
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader

import sys
sys.path.insert(0, "scripts")
import train_m4 as tm

POLICIES = ["fixed_0.60", "fixed_0.70", "fixed_0.75", "fixed_0.80", "val_q01", "val_q05"]


def macro_scores(y_true, y_pred, n_classes):
    rec, prec, f1 = {}, {}, {}
    for j in range(n_classes):
        tp = int(((y_pred == j) & (y_true == j)).sum())
        fp = int(((y_pred == j) & (y_true != j)).sum())
        fn = int(((y_pred != j) & (y_true == j)).sum())
        n_pos = int((y_true == j).sum())
        rec[j] = float(tp / n_pos) if n_pos > 0 else 0.0
        prec[j] = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
        denom = 2 * tp + fp + fn
        f1[j] = float(2 * tp / denom) if denom > 0 else 0.0
    valid_f1s = [f1[j] for j in range(n_classes) if (y_true == j).sum() > 0]
    mean_f1 = float(np.mean(valid_f1s)) if valid_f1s else 0.0
    mean_rec = float(np.mean(list(rec.values()))) if rec else 0.0
    mean_prec = float(np.mean(list(prec.values()))) if prec else 0.0
    return mean_f1, mean_rec, mean_prec, rec, prec, f1


def evaluate_cohort(P_ext, ext_df, gn_classes, conf_val, yh_val, y_val, cohort_mask, cohort_name):
    cohort_df = ext_df[cohort_mask].copy().reset_index(drop=True)
    P_cohort = P_ext[cohort_mask]
    conf_cohort = P_cohort.max(axis=1)
    yh_cohort = P_cohort.argmax(axis=1)

    scorable_mask = cohort_df.canonical_id.isin(gn_classes).to_numpy()
    total_scorable = int(scorable_mask.sum())

    y_scorable = np.array([gn_classes.index(k) for k in cohort_df.canonical_id[scorable_mask]])
    yh_scorable = yh_cohort[scorable_mask]
    conf_scorable = conf_cohort[scorable_mask]

    full_f1, full_mrec, full_mprec, full_recs, full_precs, full_f1s = macro_scores(y_scorable, yh_scorable, len(gn_classes))
    full_acc = float((yh_scorable == y_scorable).mean())

    # Directional errors
    h_idx = gn_classes.index("groundnut__healthy_or_abiotic")
    r_idx = gn_classes.index("groundnut__rust")
    t_idx = gn_classes.index("groundnut__tikka_leaf_spot")

    err_h_to_t = int(((y_scorable == h_idx) & (yh_scorable == t_idx)).sum())
    err_h_to_r = int(((y_scorable == h_idx) & (yh_scorable == r_idx)).sum())
    err_r_to_t = int(((y_scorable == r_idx) & (yh_scorable == t_idx)).sum())
    err_r_to_h = int(((y_scorable == r_idx) & (yh_scorable == h_idx)).sum())
    err_t_to_h = int(((y_scorable == t_idx) & (yh_scorable == h_idx)).sum())
    err_t_to_r = int(((y_scorable == t_idx) & (yh_scorable == r_idx)).sum())

    policy_results = {}
    for policy in POLICIES:
        if policy.startswith("fixed_"):
            thr = float(policy.split("_")[1])
        elif policy == "val_q01":
            correct_mask = (yh_val == y_val)
            thr = float(np.percentile(conf_val[correct_mask], 1))
        elif policy == "val_q05":
            correct_mask = (yh_val == y_val)
            thr = float(np.percentile(conf_val[correct_mask], 5))
        else:
            thr = float(policy)

        accepted_mask = (conf_scorable >= thr)
        n_accepted = int(accepted_mask.sum())
        coverage = float(n_accepted / max(1, total_scorable))

        if n_accepted > 0:
            acc_acc = float((yh_scorable[accepted_mask] == y_scorable[accepted_mask]).mean())
            acc_f1, _, _, _, _, _ = macro_scores(y_scorable[accepted_mask], yh_scorable[accepted_mask], len(gn_classes))
        else:
            acc_acc, acc_f1 = 0.0, 0.0

        # Open-set
        accepted_all_mask = (conf_cohort >= thr)
        open_f1s = {}
        for k, cname in enumerate(gn_classes):
            tp = int(((cohort_df.canonical_id == cname) & (yh_cohort == k) & accepted_all_mask).sum())
            fp_all = int(((cohort_df.canonical_id != cname) & (yh_cohort == k) & accepted_all_mask).sum())
            fn = int(((cohort_df.canonical_id == cname) & ((yh_cohort != k) | (~accepted_all_mask))).sum())
            denom = 2 * tp + fp_all + fn
            open_f1s[cname] = float(2 * tp / denom) if denom > 0 else 0.0
        open_macro_f1 = float(np.mean(list(open_f1s.values())))

        policy_results[policy] = {
            "cohort": cohort_name,
            "policy": policy,
            "threshold": round(thr, 4),
            "full_macro_f1": round(full_f1, 4),
            "full_accuracy": round(full_acc, 4),
            "full_recall_healthy": round(full_recs[0], 4),
            "full_recall_rust": round(full_recs[1], 4),
            "full_recall_tikka": round(full_recs[2], 4),
            "full_prec_healthy": round(full_precs[0], 4),
            "full_prec_rust": round(full_precs[1], 4),
            "full_prec_tikka": round(full_precs[2], 4),
            "coverage": round(coverage, 4),
            "accepted_accuracy": round(acc_acc, 4),
            "accepted_macro_f1": round(acc_f1, 4),
            "open_macro_f1": round(open_macro_f1, 4),
            "error_healthy_to_tikka": err_h_to_t,
            "error_healthy_to_rust": err_h_to_r,
            "error_rust_to_tikka": err_r_to_t,
            "error_rust_to_healthy": err_r_to_h,
            "error_tikka_to_healthy": err_t_to_h,
            "error_tikka_to_rust": err_t_to_r,
            "n_scorable": total_scorable,
            "n_total": len(cohort_df),
        }

    return policy_results, y_scorable, yh_scorable, conf_scorable, cohort_df[scorable_mask].copy()


def main():
    parser = argparse.ArgumentParser(description="M4 V2.3.1 Standalone Evaluator")
    parser.add_argument("--ckpt", type=str, default="runs_m4_v2_3_1/UZ-M4-v2.3.1-groundnut-s1-triclass-balance/checkpoint_best.pt", help="Path to checkpoint")
    parser.add_argument("--manifest", type=str, default="m4_v2/manifests/groundnut_v2.csv", help="Path to manifest")
    parser.add_argument("--split-map", type=str, default="m4_v2_3/external_split_mapping.csv", help="Path to split mapping")
    parser.add_argument("--pkg", type=str, default="m4_v1", help="Path to images")
    parser.add_argument("--classes", type=str, default="m4_v2/classes.json", help="Path to classes JSON")
    args = parser.parse_args()

    ckpt_path = Path(args.ckpt)
    assert ckpt_path.exists(), f"Checkpoint missing: {ckpt_path}"

    with open(args.classes) as f:
        classes = json.load(f)
    gn_classes = classes["groundnut"]

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Evaluating {ckpt_path} on {device}...")

    ck = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    model = tm.Model(ck["classes"])
    model.load_state_dict(ck["model"])
    model.to(device).eval()

    pkg = Path(args.pkg)
    man = pd.read_csv(args.manifest)
    gn_man = man[man.crop == "groundnut"].copy().reset_index(drop=True)
    val_df = gn_man[gn_man.split == "val"].copy().reset_index(drop=True)
    ext_df = gn_man[gn_man.split == "external_test"].copy().reset_index(drop=True)

    # Attach split mapping if present
    split_map_path = Path(args.split_map)
    if split_map_path.exists():
        smap = pd.read_csv(split_map_path)
        sha_to_split = dict(zip(smap.sha256, smap.v2_3_external_split))
        ext_df["v2_3_split"] = ext_df.sha256.map(sha_to_split)
    else:
        ext_df["v2_3_split"] = "ext_final_test"

    def run_inference(df):
        ds = tm.DS(df.assign(canonical_id=df.canonical_id.where(
            df.canonical_id.isin(sum(classes.values(), [])),
            df.crop.map(lambda c: classes[c][0])
        )), pkg, classes, False)
        loader = DataLoader(ds, batch_size=64, shuffle=False, num_workers=0)
        probs = []
        with torch.no_grad():
            for x, cr, _ in loader:
                lg = model(x.to(device), cr)
                for l in lg:
                    probs.append(torch.softmax(l.float(), 0).cpu().numpy())
        return np.stack(probs)

    print("Running internal validation inference...")
    P_val = run_inference(val_df)
    y_val = np.array([gn_classes.index(k) for k in val_df.canonical_id])
    conf_val, yh_val = P_val.max(1), P_val.argmax(1)

    print("Running external test inference (N=1695)...")
    P_ext = run_inference(ext_df)

    # 1. Historical Benchmark (Canonical N=1152 scorable)
    mask_canonical = np.ones(len(ext_df), dtype=bool)
    res_canonical, y_can, yh_can, conf_can, df_can = evaluate_cohort(
        P_ext, ext_df, gn_classes, conf_val, yh_val, y_val, mask_canonical, "canonical_full_1152"
    )

    # 2. Untouched Final External Test (N=928 scorable)
    mask_untouched = (ext_df["v2_3_split"] == "ext_final_test").to_numpy()
    res_untouched, y_unt, yh_unt, conf_unt, df_unt = evaluate_cohort(
        P_ext, ext_df, gn_classes, conf_val, yh_val, y_val, mask_untouched, "untouched_final_test_928"
    )

    # 3. Development Holdout (N=224 scorable)
    mask_dev = (ext_df["v2_3_split"] == "ext_dev_holdout").to_numpy()
    res_dev, _, _, _, _ = evaluate_cohort(
        P_ext, ext_df, gn_classes, conf_val, yh_val, y_val, mask_dev, "dev_holdout_224"
    )

    print("\n" + "=" * 70)
    print("M4 V2.3.1 EVALUATION RESULTS SUMMARY (tau = 0.70)")
    print("=" * 70)
    for name, r in [("Untouched Final Test (N=928)", res_untouched["fixed_0.70"]),
                    ("Canonical Full Set (N=1152)", res_canonical["fixed_0.70"])]:
        print(f"\n--- {name} ---")
        print(f"  Full-Set Exact Macro-F1: {r['full_macro_f1']}")
        print(f"  Healthy Recall          : {r['full_recall_healthy']*100:.2f}%")
        print(f"  Rust Recall             : {r['full_recall_rust']*100:.2f}%")
        print(f"  Tikka Recall            : {r['full_recall_tikka']*100:.2f}%")
        print(f"  Accuracy                : {r['full_accuracy']*100:.2f}%")
        print(f"  Coverage (tau=0.70)     : {r['coverage']*100:.2f}%")
        print(f"  Accepted Accuracy       : {r['accepted_accuracy']*100:.2f}%")
        print(f"  Open-Set Macro-F1       : {r['open_macro_f1']}")
        print(f"  Healthy -> Tikka Errors : {r['error_healthy_to_tikka']}")
        print(f"  Rust -> Tikka Errors    : {r['error_rust_to_tikka']}")
        print(f"  Rust -> Healthy Errors  : {r['error_rust_to_healthy']}")

    out_dir = Path("reports/artifacts")
    out_dir.mkdir(parents=True, exist_ok=True)
    all_res = {
        "canonical_full": res_canonical,
        "untouched_final": res_untouched,
        "dev_holdout": res_dev,
    }
    with open(out_dir / "m4_v2_3_1_s1_metrics.json", "w") as f:
        json.dump(all_res, f, indent=2)
    print(f"\nSaved {out_dir / 'm4_v2_3_1_s1_metrics.json'}")

    # Build Sample Error Cases CSV
    df_can["v2_3_1_pred"] = [gn_classes[i] for i in yh_can]
    df_can["v2_3_1_conf"] = conf_can
    df_can["v2_3_1_is_correct"] = (y_can == yh_can)
    df_can.to_csv(out_dir / "m4_v2_3_1_s1_error_cases.csv", index=False)
    print(f"Saved {out_dir / 'm4_v2_3_1_s1_error_cases.csv'}")

    # Build 3-Way Comparative Benchmark Table (V2.2 S42 vs V2.3 S42 vs V2.3.1 S42)
    can_r = res_canonical["fixed_0.70"]
    comp_data = [
        {"Metric": "Healthy recall", "V2.2 S42": "70.33%", "V2.3 S42": "84.67%", "V2.3.1 S42": f"{can_r['full_recall_healthy']*100:.2f}%"},
        {"Metric": "Rust recall", "V2.2 S42": "95.00%", "V2.3 S42": "60.00%", "V2.3.1 S42": f"{can_r['full_recall_rust']*100:.2f}%"},
        {"Metric": "Tikka recall", "V2.2 S42": "96.99%", "V2.3 S42": "99.07%", "V2.3.1 S42": f"{can_r['full_recall_tikka']*100:.2f}%"},
        {"Metric": "Macro-F1", "V2.2 S42": "0.8548", "V2.3 S42": "0.8399", "V2.3.1 S42": f"{can_r['full_macro_f1']:.4f}"},
        {"Metric": "Accuracy", "V2.2 S42": "82.90%", "V2.3 S42": "87.50%", "V2.3.1 S42": f"{can_r['full_accuracy']*100:.2f}%"},
        {"Metric": "τ=.70 coverage", "V2.2 S42": "68.40%", "V2.3 S42": "80.47%", "V2.3.1 S42": f"{can_r['coverage']*100:.2f}%"},
        {"Metric": "τ=.70 accepted accuracy", "V2.2 S42": "93.27%", "V2.3 S42": "92.66%", "V2.3.1 S42": f"{can_r['accepted_accuracy']*100:.2f}%"},
        {"Metric": "Open-set F1", "V2.2 S42": "0.6964", "V2.3 S42": "0.6651", "V2.3.1 S42": f"{can_r['open_macro_f1']:.4f}"},
        {"Metric": "Healthy → Tikka", "V2.2 S42": "178", "V2.3 S42": "92", "V2.3.1 S42": str(can_r['error_healthy_to_tikka'])},
        {"Metric": "Rust → Tikka", "V2.2 S42": "5", "V2.3 S42": "47", "V2.3.1 S42": str(can_r['error_rust_to_tikka'])},
        {"Metric": "Rust → Healthy", "V2.2 S42": "1", "V2.3 S42": "1", "V2.3.1 S42": str(can_r['error_rust_to_healthy'])},
    ]
    df_comp = pd.DataFrame(comp_data)
    df_comp.to_csv(out_dir / "m4_v2_3_1_s1_comparison.csv", index=False)
    print(f"Saved {out_dir / 'm4_v2_3_1_s1_comparison.csv'}")

    print("\n" + "=" * 70)
    print("M4 THREE-WAY CONTROLLED COMPARISON MATRIX (Canonical N=1,152)")
    print("=" * 70)
    header = f"{'Metric':<26} | {'V2.2 S42':<12} | {'V2.3 S42':<12} | {'V2.3.1 S42':<12}"
    print(header)
    print("-" * len(header))
    for row in comp_data:
        print(f"{row['Metric']:<26} | {row['V2.2 S42']:<12} | {row['V2.3 S42']:<12} | {row['V2.3.1 S42']:<12}")
    print("=" * 70)


if __name__ == "__main__":
    main()
