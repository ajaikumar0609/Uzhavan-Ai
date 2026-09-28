"""M4 V2.2 Comprehensive 3-Way Comparative Evaluation Script.

Compares:
1. V2 baseline: UZ-M4-v2-groundnut-s1-wce
2. V2.1: UZ-M4-v2.1-groundnut-s1-wce-rustrobust (1.25x Rust weight + Augmentation)
3. V2.2: UZ-M4-v2.2-groundnut-s1-wce-balanced-rust (1.0x Rust weight + Augmentation)

Evaluates:
- Thresholds: fixed_0.60, fixed_0.70, fixed_0.75, fixed_0.80, val_q01, val_q05
- A. Full-set exact metrics (denominator = all 1,152 scorable external samples)
- B. Accepted-only selective metrics (denominator = accepted subset only)
- C. Open-set metrics (denominator = all 1,695 external samples)
- D. Tikka auxiliary diagnostic metrics

Generates:
- reports/M4_V2_2_S1_ANALYSIS.md
- reports/artifacts/m4_v2_2_s1_comparison.csv
- reports/artifacts/m4_v2_2_s1_metrics.json
- reports/artifacts/m4_v2_2_full_set_metrics.csv
"""

import os, sys, json, csv, time
from pathlib import Path
import numpy as np, pandas as pd, torch
from torch.utils.data import DataLoader

sys.path.insert(0, "scripts")
import train_m4 as tm

POLICIES = ["fixed_0.60", "fixed_0.70", "fixed_0.75", "fixed_0.80", "val_q01", "val_q05"]

def calibrate_threshold(conf_val, yh_val, y_val, policy):
    correct_mask = (yh_val == y_val)
    conf_correct = conf_val[correct_mask] if correct_mask.any() else conf_val
    if policy.startswith("fixed_"):
        return float(policy.split("_")[1])
    elif policy == "val_q01":
        return float(np.percentile(conf_correct, 1))
    elif policy == "val_q05":
        return float(np.percentile(conf_correct, 5))
    else:
        return float(policy)

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

def evaluate_checkpoint(ck_path, exp_name, val_df, ext_df, gn_classes, classes, pkg, device):
    print(f"\n==========================================")
    print(f"Evaluating {exp_name} from {ck_path}")
    ck = torch.load(ck_path, map_location="cpu", weights_only=False)
    model = tm.Model(ck["classes"])
    model.load_state_dict(ck["model"])
    model.to(device).eval()

    def run_inference(df):
        ds = tm.DS(
            df.assign(canonical_id=df.canonical_id.where(
                df.canonical_id.isin(sum(classes.values(), [])),
                df.crop.map(lambda c: classes[c][0])
            )),
            pkg, classes, False
        )
        loader = DataLoader(ds, batch_size=64, shuffle=False, num_workers=4)
        probs = []
        with torch.no_grad():
            for x, cr, _ in loader:
                lg = model(x.to(device), cr)
                for l in lg:
                    probs.append(torch.softmax(l.float(), 0).cpu().numpy())
        return np.stack(probs)

    print("Running val inference...")
    P_val = run_inference(val_df)
    y_val = np.array([gn_classes.index(k) for k in val_df.canonical_id])
    conf_val, yh_val = P_val.max(1), P_val.argmax(1)

    print("Running external test inference (N=1695)...")
    P_ext = run_inference(ext_df)
    conf_ext, yh_ext = P_ext.max(1), P_ext.argmax(1)

    scorable_mask = ext_df.canonical_id.isin(gn_classes).to_numpy()
    total_scorable = int(scorable_mask.sum())
    assert total_scorable == 1152

    y_scorable = np.array([gn_classes.index(k) for k in ext_df.canonical_id[scorable_mask]])
    yh_scorable = yh_ext[scorable_mask]
    conf_scorable = conf_ext[scorable_mask]

    # Metrics on full unthresholded scorable set (Metric A)
    full_f1, full_mrec, full_mprec, full_recs, full_precs, full_f1s = macro_scores(y_scorable, yh_scorable, len(gn_classes))
    full_acc = float((yh_scorable == y_scorable).mean())

    oot_mask = ext_df.canonical_id.isin(["groundnut__alternaria_leaf_spot", "groundnut__rosette_virus"]).to_numpy()
    alt_mask = (ext_df.canonical_id == "groundnut__alternaria_leaf_spot").to_numpy()
    ros_mask = (ext_df.canonical_id == "groundnut__rosette_virus").to_numpy()
    tikka_mask = (ext_df.canonical_id == "groundnut__tikka_leaf_spot").to_numpy()

    policy_results = {}
    for policy in POLICIES:
        thr = calibrate_threshold(conf_val, yh_val, y_val, policy)

        # B. Accepted-only selective metrics
        accepted_mask = (conf_scorable >= thr)
        n_accepted = int(accepted_mask.sum())
        n_rejected = int((~accepted_mask).sum())
        coverage = float(n_accepted / total_scorable)

        # False rejection rate on scorable: correct predictions that were rejected
        correct_scorable = (yh_scorable == y_scorable)
        frr = float(((correct_scorable) & (~accepted_mask)).sum() / max(1, correct_scorable.sum()))

        if n_accepted > 0:
            acc_accuracy = float((yh_scorable[accepted_mask] == y_scorable[accepted_mask]).mean())
            acc_f1, acc_mrec, acc_mprec, acc_recs, acc_precs, acc_f1s = macro_scores(y_scorable[accepted_mask], yh_scorable[accepted_mask], len(gn_classes))
        else:
            acc_accuracy, acc_f1 = 0.0, 0.0
            acc_recs, acc_precs, acc_f1s = {0:0,1:0,2:0}, {0:0,1:0,2:0}, {0:0,1:0,2:0}

        # C. Open-set metrics (all 1695 samples)
        accepted_all_mask = (conf_ext >= thr)
        open_f1s, open_recs, open_precs = {}, {}, {}
        for k, cname in enumerate(gn_classes):
            n_true = int((ext_df.canonical_id == cname).sum())
            tp = int(((ext_df.canonical_id == cname) & (yh_ext == k) & accepted_all_mask).sum())
            fp_all = int(((ext_df.canonical_id != cname) & (yh_ext == k) & accepted_all_mask).sum())
            fn = int(((ext_df.canonical_id == cname) & ((yh_ext != k) | (~accepted_all_mask))).sum())
            open_recs[cname] = float(tp / n_true) if n_true > 0 else 0.0
            open_precs[cname] = float(tp / (tp + fp_all)) if (tp + fp_all) > 0 else 0.0
            denom = 2 * tp + fp_all + fn
            open_f1s[cname] = float(2 * tp / denom) if denom > 0 else 0.0
        open_macro_f1 = float(np.mean(list(open_f1s.values())))

        # Non-target false alarms
        alt_false_alarms = int((alt_mask & accepted_all_mask).sum())
        ros_false_alarms = int((ros_mask & accepted_all_mask).sum())
        oot_unsure_rate = float((conf_ext[oot_mask] < thr).mean())

        # D. Tikka auxiliary diagnostic (N=432)
        tikka_pred_tikka = (yh_ext[tikka_mask] == gn_classes.index("groundnut__tikka_leaf_spot"))
        tikka_acc_mask = (conf_ext[tikka_mask] >= thr)
        raw_tikka_recall = float(tikka_pred_tikka.mean())
        thresh_tikka_recall = float((tikka_pred_tikka & tikka_acc_mask).sum() / len(tikka_pred_tikka))
        tikka_coverage = float(tikka_acc_mask.mean())
        tikka_unsure_rate = float((~tikka_acc_mask).mean())
        tikka_accepted_accuracy = float(tikka_pred_tikka[tikka_acc_mask].mean()) if tikka_acc_mask.any() else 0.0

        policy_results[policy] = {
            "experiment": exp_name,
            "policy": policy,
            "threshold": round(thr, 4),
            # A. Full-set exact (denominator = 1152)
            "full_macro_f1": round(full_f1, 4),
            "full_macro_recall": round(full_mrec, 4),
            "full_macro_precision": round(full_mprec, 4),
            "full_accuracy": round(full_acc, 4),
            "full_recall_healthy": round(full_recs[0], 4),
            "full_recall_rust": round(full_recs[1], 4),
            "full_recall_tikka": round(full_recs[2], 4),
            "full_prec_healthy": round(full_precs[0], 4),
            "full_prec_rust": round(full_precs[1], 4),
            "full_prec_tikka": round(full_precs[2], 4),
            "full_f1_healthy": round(full_f1s[0], 4),
            "full_f1_rust": round(full_f1s[1], 4),
            "full_f1_tikka": round(full_f1s[2], 4),
            # B. Accepted-only selective
            "accepted_macro_f1": round(acc_f1, 4),
            "accepted_accuracy": round(acc_accuracy, 4),
            "coverage": round(coverage, 4),
            "accepted_count": n_accepted,
            "rejected_count": n_rejected,
            "false_rejection_rate": round(frr, 4),
            "acc_recall_healthy": round(acc_recs.get(0, 0), 4),
            "acc_recall_rust": round(acc_recs.get(1, 0), 4),
            "acc_recall_tikka": round(acc_recs.get(2, 0), 4),
            # C. Open-set (denominator = 1695)
            "open_macro_f1": round(open_macro_f1, 4),
            "open_prec_healthy": round(open_precs["groundnut__healthy_or_abiotic"], 4),
            "open_prec_rust": round(open_precs["groundnut__rust"], 4),
            "open_prec_tikka": round(open_precs["groundnut__tikka_leaf_spot"], 4),
            "alt_false_alarms": alt_false_alarms,
            "ros_false_alarms": ros_false_alarms,
            "oot_unsure_rate": round(oot_unsure_rate, 4),
            # D. Tikka auxiliary
            "raw_tikka_recall": round(raw_tikka_recall, 4),
            "thresh_tikka_recall": round(thresh_tikka_recall, 4),
            "tikka_coverage": round(tikka_coverage, 4),
            "tikka_unsure_rate": round(tikka_unsure_rate, 4),
            "tikka_accepted_accuracy": round(tikka_accepted_accuracy, 4),
        }
    return policy_results

def main():
    root = Path(".")
    reports_dir = root / "reports"
    artifacts_dir = reports_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    man_path = root / "m4_v2/manifests/groundnut_v2.csv"
    pkg = root / "m4_v1"
    classes_file = root / "m4_v2/classes.json"

    with open(classes_file) as f:
        classes = json.load(f)
    gn_classes = classes["groundnut"]

    man = pd.read_csv(man_path)
    gn_man = man[man.crop == "groundnut"].copy().reset_index(drop=True)
    val_df = gn_man[gn_man.split == "val"].copy().reset_index(drop=True)
    ext_df = gn_man[gn_man.split == "external_test"].copy().reset_index(drop=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device} ({torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'})")

    ck_v2 = root / "runs_m4_v2/UZ-M4-v2-groundnut-s1-wce/checkpoint_best.pt"
    ck_v2_1 = root / "runs_m4_v2_1/UZ-M4-v2.1-groundnut-s1-wce-rustrobust/checkpoint_best.pt"
    ck_v2_2 = root / "runs_m4_v2_2/UZ-M4-v2.2-groundnut-s1-wce-balanced-rust/checkpoint_best.pt"

    assert ck_v2.exists(), f"Missing V2 checkpoint: {ck_v2}"
    assert ck_v2_1.exists(), f"Missing V2.1 checkpoint: {ck_v2_1}"
    assert ck_v2_2.exists(), f"Missing V2.2 checkpoint: {ck_v2_2}"

    res_v2 = evaluate_checkpoint(ck_v2, "v2-baseline", val_df, ext_df, gn_classes, classes, pkg, device)
    res_v2_1 = evaluate_checkpoint(ck_v2_1, "v2.1-rustrobust", val_df, ext_df, gn_classes, classes, pkg, device)
    res_v2_2 = evaluate_checkpoint(ck_v2_2, "v2.2-balanced", val_df, ext_df, gn_classes, classes, pkg, device)

    # 1. Full-set metrics CSV (N=1,152 fixed universe)
    full_set_rows = []
    for pol in POLICIES:
        for name, res in [("V2_Baseline_S1", res_v2), ("V2.1_S1_RustRobust", res_v2_1), ("V2.2_S1_Balanced", res_v2_2)]:
            r = res[pol]
            full_set_rows.append({
                "model": name,
                "policy": pol,
                "threshold": r["threshold"],
                "full_macro_f1": r["full_macro_f1"],
                "full_accuracy": r["full_accuracy"],
                "full_recall_healthy": r["full_recall_healthy"],
                "full_recall_rust": r["full_recall_rust"],
                "full_recall_tikka": r["full_recall_tikka"],
                "full_prec_healthy": r["full_prec_healthy"],
                "full_prec_rust": r["full_prec_rust"],
                "full_prec_tikka": r["full_prec_tikka"],
                "full_f1_healthy": r["full_f1_healthy"],
                "full_f1_rust": r["full_f1_rust"],
                "full_f1_tikka": r["full_f1_tikka"],
            })
    df_full_set = pd.DataFrame(full_set_rows)
    csv_full_path = artifacts_dir / "m4_v2_2_full_set_metrics.csv"
    df_full_set.to_csv(csv_full_path, index=False)
    print(f"Saved: {csv_full_path}")

    # 2. Comparison CSV across policies
    comp_rows = []
    for pol in POLICIES:
        b = res_v2[pol]
        v1 = res_v2_1[pol]
        v2 = res_v2_2[pol]
        comp_rows.append({
            "policy": pol,
            "v2_base_thresh": b["threshold"],
            "v2_1_thresh": v1["threshold"],
            "v2_2_thresh": v2["threshold"],
            # Full set Macro-F1
            "v2_base_full_f1": b["full_macro_f1"],
            "v2_1_full_f1": v1["full_macro_f1"],
            "v2_2_full_f1": v2["full_macro_f1"],
            "delta_v2_2_minus_v2_base_full_f1": round(v2["full_macro_f1"] - b["full_macro_f1"], 4),
            "delta_v2_2_minus_v2_1_full_f1": round(v2["full_macro_f1"] - v1["full_macro_f1"], 4),
            # Recalls (Full Set)
            "v2_base_healthy_rec": b["full_recall_healthy"],
            "v2_1_healthy_rec": v1["full_recall_healthy"],
            "v2_2_healthy_rec": v2["full_recall_healthy"],
            "delta_healthy_rec_v2_2_minus_v2_1": round(v2["full_recall_healthy"] - v1["full_recall_healthy"], 4),
            "v2_base_rust_rec": b["full_recall_rust"],
            "v2_1_rust_rec": v1["full_recall_rust"],
            "v2_2_rust_rec": v2["full_recall_rust"],
            "delta_rust_rec_v2_2_minus_base": round(v2["full_recall_rust"] - b["full_recall_rust"], 4),
            "v2_base_tikka_rec": b["full_recall_tikka"],
            "v2_1_tikka_rec": v1["full_recall_tikka"],
            "v2_2_tikka_rec": v2["full_recall_tikka"],
            # Selective (tau)
            "v2_base_accepted_f1": b["accepted_macro_f1"],
            "v2_1_accepted_f1": v1["accepted_macro_f1"],
            "v2_2_accepted_f1": v2["accepted_macro_f1"],
            "v2_base_coverage": b["coverage"],
            "v2_1_coverage": v1["coverage"],
            "v2_2_coverage": v2["coverage"],
            "v2_base_accepted_acc": b["accepted_accuracy"],
            "v2_1_accepted_acc": v1["accepted_accuracy"],
            "v2_2_accepted_acc": v2["accepted_accuracy"],
            # Open set
            "v2_base_open_f1": b["open_macro_f1"],
            "v2_1_open_f1": v1["open_macro_f1"],
            "v2_2_open_f1": v2["open_macro_f1"],
            "v2_base_oot_unsure": b["oot_unsure_rate"],
            "v2_1_oot_unsure": v1["oot_unsure_rate"],
            "v2_2_oot_unsure": v2["oot_unsure_rate"],
        })
    df_comp = pd.DataFrame(comp_rows)
    csv_comp_path = artifacts_dir / "m4_v2_2_s1_comparison.csv"
    df_comp.to_csv(csv_comp_path, index=False)
    print(f"Saved: {csv_comp_path}")

    # 3. JSON metrics
    json_path = artifacts_dir / "m4_v2_2_s1_metrics.json"
    full_json = {
        "metadata": {
            "title": "M4 V2.2 Controlled Experiment 3-Way Comparison",
            "date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "models": {
                "v2_baseline": "runs_m4_v2/UZ-M4-v2-groundnut-s1-wce",
                "v2_1": "runs_m4_v2_1/UZ-M4-v2.1-groundnut-s1-wce-rustrobust",
                "v2_2": "runs_m4_v2_2/UZ-M4-v2.2-groundnut-s1-wce-balanced-rust",
            },
            "device": str(device)
        },
        "v2_baseline": res_v2,
        "v2_1": res_v2_1,
        "v2_2": res_v2_2,
        "comparison": comp_rows
    }
    with open(json_path, "w") as f:
        json.dump(full_json, f, indent=2)
    print(f"Saved: {json_path}")

    # 4. Markdown Report
    md_path = reports_dir / "M4_V2_2_S1_ANALYSIS.md"
    b70 = res_v2["fixed_0.70"]
    v1_70 = res_v2_1["fixed_0.70"]
    v2_70 = res_v2_2["fixed_0.70"]

    lines = [
        "# Uzhavan M4 V2.2 Controlled Training Experiment Analysis",
        "",
        f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}  ",
        "**Host:** Acer ALPHA (NVIDIA GeForce RTX 4050 Laptop GPU, 6GB VRAM, CUDA 12.6)  ",
        "**Experiment Target:** `UZ-M4-v2.2-groundnut-s1-wce-balanced-rust`  ",
        "**Comparison Set:**",
        "1. `V2 Baseline S1 WCE` (`runs_m4_v2/UZ-M4-v2-groundnut-s1-wce`)",
        "2. `V2.1 S1 WCE RustRobust` (`runs_m4_v2_1/UZ-M4-v2.1-groundnut-s1-wce-rustrobust`, Rust weight = 1.25x)",
        "3. `V2.2 S1 WCE Balanced` (`runs_m4_v2_2/UZ-M4-v2.2-groundnut-s1-wce-balanced-rust`, Rust weight = 1.0x)",
        "",
        "---",
        "",
        "## 1. Controlled Experiment Hypothesis & Variable Isolation",
        "",
        "| Factor | V2 Baseline S1 | V2.1 S1 RustRobust | V2.2 S1 Balanced | Status |",
        "|---|---|---|---|---|",
        "| **Architecture** | EfficientNetV2-S | EfficientNetV2-S | EfficientNetV2-S | Strictly identical |",
        "| **Field-Robust Augmentation** | None (standard crop/flip) | Full (shadow, blur, color jitter) | Full (shadow, blur, color jitter) | **Identical to V2.1** |",
        "| **Rust Loss Weight Multiplier** | 1.0x (standard) | 1.25x (boosted) | **1.0x (balanced standard)** | **Single variable changed** |",
        "| **Optimizer / LR / Epochs** | AdamW / 1e-4 / 15 eps | AdamW / 1e-4 / 15 eps | AdamW / 1e-4 / 15 eps | Strictly identical |",
        "| **Random Seed** | 42 | 42 | 42 | Strictly identical |",
        "",
        "> **Hypothesis:** Resetting Rust loss weight from 1.25x to 1.0x while retaining the field-robust augmentations will recover the Healthy recall loss of V2.1 while preserving the external Rust recall improvements.",
        "",
        "---",
        "",
        "## 2. Three-Way Metric Comparison at Operational tau=0.70",
        "",
        "| Metric | V2 Baseline S1 | V2.1 S1 (1.25x Rust) | V2.2 S1 (1.0x Rust) | Delta (V2.2 - V2.1) | Delta (V2.2 - Base) |",
        "|---|---|---|---|---|---|",
        f"| **Full-Set Exact Macro-F1** (N=1152) | **{b70['full_macro_f1']:.4f}** | **{v1_70['full_macro_f1']:.4f}** | **{v2_70['full_macro_f1']:.4f}** | {(v2_70['full_macro_f1'] - v1_70['full_macro_f1']):+.4f} | {(v2_70['full_macro_f1'] - b70['full_macro_f1']):+.4f} |",
        f"| **Healthy Recall (Full-Set)** | {b70['full_recall_healthy']*100:.1f}% | {v1_70['full_recall_healthy']*100:.1f}% | **{v2_70['full_recall_healthy']*100:.1f}%** | {(v2_70['full_recall_healthy'] - v1_70['full_recall_healthy'])*100:+.1f}% | {(v2_70['full_recall_healthy'] - b70['full_recall_healthy'])*100:+.1f}% |",
        f"| **Rust Recall (Full-Set)** | {b70['full_recall_rust']*100:.1f}% | {v1_70['full_recall_rust']*100:.1f}% | **{v2_70['full_recall_rust']*100:.1f}%** | {(v2_70['full_recall_rust'] - v1_70['full_recall_rust'])*100:+.1f}% | {(v2_70['full_recall_rust'] - b70['full_recall_rust'])*100:+.1f}% |",
        f"| **Tikka Recall (Full-Set)** | {b70['full_recall_tikka']*100:.1f}% | {v1_70['full_recall_tikka']*100:.1f}% | **{v2_70['full_recall_tikka']*100:.1f}%** | {(v2_70['full_recall_tikka'] - v1_70['full_recall_tikka'])*100:+.1f}% | {(v2_70['full_recall_tikka'] - b70['full_recall_tikka'])*100:+.1f}% |",
        f"| **Overall Accuracy (Full-Set)** | {b70['full_accuracy']*100:.1f}% | {v1_70['full_accuracy']*100:.1f}% | **{v2_70['full_accuracy']*100:.1f}%** | {(v2_70['full_accuracy'] - v1_70['full_accuracy'])*100:+.1f}% | {(v2_70['full_accuracy'] - b70['full_accuracy'])*100:+.1f}% |",
        f"| **Accepted Macro-F1** (tau=0.70) | {b70['accepted_macro_f1']:.4f} | {v1_70['accepted_macro_f1']:.4f} | **{v2_70['accepted_macro_f1']:.4f}** | {(v2_70['accepted_macro_f1'] - v1_70['accepted_macro_f1']):+.4f} | {(v2_70['accepted_macro_f1'] - b70['accepted_macro_f1']):+.4f} |",
        f"| **Accepted Accuracy** (tau=0.70) | {b70['accepted_accuracy']*100:.1f}% | {v1_70['accepted_accuracy']*100:.1f}% | **{v2_70['accepted_accuracy']*100:.1f}%** | {(v2_70['accepted_accuracy'] - v1_70['accepted_accuracy'])*100:+.1f}% | {(v2_70['accepted_accuracy'] - b70['accepted_accuracy'])*100:+.1f}% |",
        f"| **Scorable Coverage** (tau=0.70) | {b70['coverage']*100:.1f}% | {v1_70['coverage']*100:.1f}% | **{v2_70['coverage']*100:.1f}%** | {(v2_70['coverage'] - v1_70['coverage'])*100:+.1f}% | {(v2_70['coverage'] - b70['coverage'])*100:+.1f}% |",
        f"| **Open-Set Macro-F1** (N=1695) | {b70['open_macro_f1']:.4f} | {v1_70['open_macro_f1']:.4f} | **{v2_70['open_macro_f1']:.4f}** | {(v2_70['open_macro_f1'] - v1_70['open_macro_f1']):+.4f} | {(v2_70['open_macro_f1'] - b70['open_macro_f1']):+.4f} |",
        f"| **OOD UNSURE Rate** (tau=0.70) | {b70['oot_unsure_rate']*100:.1f}% | {v1_70['oot_unsure_rate']*100:.1f}% | **{v2_70['oot_unsure_rate']*100:.1f}%** | {(v2_70['oot_unsure_rate'] - v1_70['oot_unsure_rate'])*100:+.1f}% | {(v2_70['oot_unsure_rate'] - b70['oot_unsure_rate'])*100:+.1f}% |",
        "",
        "---",
        "",
        "## 3. Policy Sweep Breakdown across All Thresholds",
        "",
        "| Policy | Model | Full-Set Macro-F1 | Healthy Recall | Rust Recall | Tikka Recall | Coverage | Accepted Acc | Accepted F1 | Open-Set F1 |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]

    for pol in POLICIES:
        for name, res in [("V2_Base", res_v2), ("V2.1", res_v2_1), ("V2.2", res_v2_2)]:
            r = res[pol]
            lines.append(f"| `{pol}` | {name} | **{r['full_macro_f1']:.4f}** | {r['full_recall_healthy']*100:.1f}% | {r['full_recall_rust']*100:.1f}% | {r['full_recall_tikka']*100:.1f}% | {r['coverage']*100:.1f}% | {r['accepted_accuracy']*100:.1f}% | {r['accepted_macro_f1']:.4f} | {r['open_macro_f1']:.4f} |")

    lines.extend([
        "",
        "---",
        "",
        "## 4. Systematic Answers to Decision Criteria",
        "",
        f"1. **Did V2.2 recover Healthy recall relative to V2.1?**",
        f"   - V2.1 Healthy Recall: **{v1_70['full_recall_healthy']*100:.1f}%**",
        f"   - V2.2 Healthy Recall: **{v2_70['full_recall_healthy']*100:.1f}%** (Delta: {(v2_70['full_recall_healthy'] - v1_70['full_recall_healthy'])*100:+.1f}%)",
        "",
        f"2. **Did V2.2 retain the Rust recall improvement?**",
        f"   - Baseline Rust Recall: **{b70['full_recall_rust']*100:.1f}%**",
        f"   - V2.2 Rust Recall: **{v2_70['full_recall_rust']*100:.1f}%** (Delta vs Base: {(v2_70['full_recall_rust'] - b70['full_recall_rust'])*100:+.1f}%)",
        "",
        f"3. **Did V2.2 preserve Tikka performance?**",
        f"   - Tikka Recall: **{v2_70['full_recall_tikka']*100:.1f}%** (Auxiliary Accepted Acc: **{v2_70['tikka_accepted_accuracy']*100:.1f}%**)",
        "",
        f"4. **Did full-set Macro-F1 improve?**",
        f"   - Baseline Full-Set F1: **{b70['full_macro_f1']:.4f}**",
        f"   - V2.2 Full-Set F1: **{v2_70['full_macro_f1']:.4f}**",
        "",
        f"5. **Does V2.2 meet the tau=0.70 selective coverage/accuracy requirement (Coverage >= 85%, Accepted Acc >= 90%)?**",
        f"   - Coverage at tau=0.70: **{v2_70['coverage']*100:.1f}%** ({'PASS' if v2_70['coverage'] >= 0.85 else 'FAIL - Coverage under 85%'})",
        f"   - Accepted Accuracy at tau=0.70: **{v2_70['accepted_accuracy']*100:.1f}%** ({'PASS' if v2_70['accepted_accuracy'] >= 0.90 else 'FAIL'})",
        "",
        "---",
        "",
        "## 5. Decision on Seeds 2 and 3",
        "",
    ])

    healthy_recovered = (v2_70["full_recall_healthy"] > v1_70["full_recall_healthy"])
    rust_retained = (v2_70["full_recall_rust"] > b70["full_recall_rust"] - 0.03)
    full_f1_higher = (v2_70["full_macro_f1"] >= b70["full_macro_f1"])

    if healthy_recovered and rust_retained and full_f1_higher:
        decision_txt = "> **Verdict:** PROCEED with Seeds 2 and 3. V2.2 successfully balances Healthy recall while retaining augmentation-driven Rust robustness, establishing an improved Pareto frontier."
    else:
        decision_txt = "> **Verdict:** PAUSE on Seeds 2 and 3. The empirical trade-off requires further single-seed tuning before committing multi-seed GPU training hours."

    lines.append(decision_txt)
    lines.extend([
        "",
        "---",
        "*Report generated by Uzhavan ML V2.2 Evaluation Engine.*"
    ])

    with open(md_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Saved: {md_path}")

if __name__ == "__main__":
    main()
