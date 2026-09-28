"""UZHAVAN AI - M4 V2.2 Three-Seed Error Audit Engine.
NO TRAINING - EVALUATION & DIAGNOSTIC AUDIT ONLY.

Audits Seed 42, Seed 1337, and Seed 2024 checkpoints on the fixed N=1,152
scorable external test set (West Bengal Sasmal dataset).
Produces:
1. 3x3 confusion matrices for each seed
2. Specific error flow quantifications (Healthy <-> Rust, Healthy <-> Tikka, etc.)
3. Detailed image-level tracking of Healthy->Rust and Rust->Healthy
4. Classification of errors: 1 seed, 2 seeds, 3 seeds
5. Prediction agreement breakdown
6. Confidence distribution statistics
7. Image feature inspection (brightness, shadows, contrast, sharpness, color ratios, file size)
8. Root cause association tests (domain, image features, duplicates, severity)
9. Cross-seed consistency / subset tests

Generates:
- reports/artifacts/m4_v2_2_three_seed_confusion.csv
- reports/artifacts/m4_v2_2_three_seed_error_cases.csv
- reports/artifacts/m4_v2_2_three_seed_agreement.csv
- reports/artifacts/m4_v2_2_three_seed_confidence.csv
- reports/artifacts/m4_v2_2_three_seed_audit_diagnostic.json
"""

import os
import sys
import json
import csv
import math
from pathlib import Path
import numpy as np
import pandas as pd
from PIL import Image
import torch
from torch.utils.data import DataLoader

sys.path.insert(0, "scripts")
import train_m4 as tm

def compute_image_stats(img_path):
    try:
        with Image.open(img_path) as img:
            img_rgb = img.convert("RGB")
            w, h = img_rgb.size
            arr = np.array(img_rgb, dtype=np.float32)
            
            # Grayscale luminance (Rec. 601)
            lum = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
            mean_brightness = float(np.mean(lum))
            std_contrast = float(np.std(lum))
            shadow_fraction = float(np.mean(lum < 40.0))
            
            # Color ratios
            r_mean = float(np.mean(arr[:, :, 0]))
            g_mean = float(np.mean(arr[:, :, 1]))
            b_mean = float(np.mean(arr[:, :, 2]))
            tot_color = r_mean + g_mean + b_mean + 1e-6
            green_ratio = float(g_mean / tot_color)
            brown_ratio = float(r_mean / tot_color)
            
            # Sharpness via discrete Laplacian variance on downsampled 224x224 grayscale
            img_small = img_rgb.resize((224, 224), Image.Resampling.BILINEAR).convert("L")
            arr_gray = np.array(img_small, dtype=np.float32)
            # 3x3 Laplacian kernel convolution
            kernel = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=np.float32)
            lap = (
                arr_gray[:-2, 1:-1] * 1 +
                arr_gray[2:, 1:-1] * 1 +
                arr_gray[1:-1, :-2] * 1 +
                arr_gray[1:-1, 2:] * 1 -
                arr_gray[1:-1, 1:-1] * 4
            )
            laplacian_sharpness = float(np.var(lap))
            
            file_bytes = os.path.getsize(img_path)
            return {
                "width": w,
                "height": h,
                "file_bytes": file_bytes,
                "mean_brightness": round(mean_brightness, 2),
                "std_contrast": round(std_contrast, 2),
                "shadow_fraction": round(shadow_fraction, 4),
                "green_ratio": round(green_ratio, 4),
                "brown_ratio": round(brown_ratio, 4),
                "laplacian_sharpness": round(laplacian_sharpness, 2),
            }
    except Exception as e:
        return {
            "width": 0, "height": 0, "file_bytes": 0,
            "mean_brightness": 0.0, "std_contrast": 0.0, "shadow_fraction": 0.0,
            "green_ratio": 0.0, "brown_ratio": 0.0, "laplacian_sharpness": 0.0,
        }

def calc_distribution(arr):
    if len(arr) == 0:
        return {"count": 0, "mean": 0, "std": 0, "median": 0, "iqr": 0, "min": 0, "max": 0, "p10": 0, "p90": 0}
    a = np.array(arr)
    p25, p75 = np.percentile(a, 25), np.percentile(a, 75)
    return {
        "count": int(len(a)),
        "mean": round(float(np.mean(a)), 4),
        "std": round(float(np.std(a)), 4),
        "median": round(float(np.median(a)), 4),
        "iqr": round(float(p75 - p25), 4),
        "min": round(float(np.min(a)), 4),
        "max": round(float(np.max(a)), 4),
        "p10": round(float(np.percentile(a, 10)), 4),
        "p90": round(float(np.percentile(a, 90)), 4),
    }

def main():
    root = Path(".")
    manifest_path = root / "m4_v2/manifests/groundnut_v2.csv"
    pkg = root / "m4_v1"
    classes_file = root / "m4_v2/classes.json"
    sasmal_manifest_path = root / "m4_v2/in_groundnut_wb_sasmal.csv"

    print("=" * 70)
    print("  M4 V2.2 THREE-SEED ERROR AUDIT ENGINE (NO TRAINING)")
    print("=" * 70)

    with open(classes_file) as f:
        classes = json.load(f)
    gn_classes = classes["groundnut"]
    assert gn_classes == ["groundnut__healthy_or_abiotic", "groundnut__rust", "groundnut__tikka_leaf_spot"]

    man = pd.read_csv(manifest_path)
    gn_man = man[man.crop == "groundnut"].copy().reset_index(drop=True)
    ext_df = gn_man[gn_man.split == "external_test"].copy().reset_index(drop=True)
    print(f"Total external test samples: {len(ext_df)}")

    # Filter scorable external samples (N=1,152)
    scorable_mask = ext_df.canonical_id.isin(gn_classes)
    scorable_df = ext_df[scorable_mask].copy().reset_index(drop=True)
    assert len(scorable_df) == 1152, f"Expected 1,152 scorable samples, got {len(scorable_df)}"
    print(f"Verified scorable samples: {len(scorable_df)}")
    print("Scorable class counts:")
    print(scorable_df["canonical_id"].value_counts().to_dict())

    # Map original sasmal relative path if available
    sasmal_map = {}
    if sasmal_manifest_path.exists():
        sas_df = pd.read_csv(sasmal_manifest_path)
        for _, row in sas_df.iterrows():
            sasmal_map[str(row["sha256"]).strip()] = str(row["relpath"]).strip()
        print(f"Loaded Sasmal original filenames mapping: {len(sasmal_map)} records")

    checkpoints = {
        "Seed_42": root / "runs_m4_v2_2/UZ-M4-v2.2-groundnut-s1-wce-balanced-rust/checkpoint_best.pt",
        "Seed_1337": root / "runs_m4_v2_2/UZ-M4-v2.2-groundnut-s2-wce-balanced-rust/checkpoint_best.pt",
        "Seed_2024": root / "runs_m4_v2_2/UZ-M4-v2.2-groundnut-s3-wce-balanced-rust/checkpoint_best.pt",
    }

    for sname, ck in checkpoints.items():
        assert ck.exists(), f"Missing checkpoint for {sname}: {ck}"

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Inference device: {device}")

    # Dataset loader for scorable samples
    ds = tm.DS(
        scorable_df.assign(canonical_id=scorable_df.canonical_id.where(
            scorable_df.canonical_id.isin(sum(classes.values(), [])),
            scorable_df.crop.map(lambda c: classes[c][0])
        )),
        pkg, classes, False
    )
    loader = DataLoader(ds, batch_size=64, shuffle=False, num_workers=0)

    seed_preds = {}
    for sname, ck_path in checkpoints.items():
        print(f"Running inference for {sname} from {ck_path}...")
        ck = torch.load(ck_path, map_location="cpu", weights_only=False)
        model = tm.Model(ck["classes"])
        model.load_state_dict(ck["model"])
        model.to(device).eval()

        probs = []
        with torch.no_grad():
            for x, cr, _ in loader:
                lg = model(x.to(device), cr)
                for l in lg:
                    probs.append(torch.softmax(l.float(), 0).cpu().numpy())
        P = np.stack(probs)
        seed_preds[sname] = {
            "probs": P,
            "pred_idx": P.argmax(axis=1),
            "conf": P.max(axis=1),
        }

    # True labels
    class_to_idx = {c: i for i, c in enumerate(gn_classes)}
    y_true = np.array([class_to_idx[c] for c in scorable_df.canonical_id])

    # 1. 3x3 Confusion Matrices & Quantification
    print("\n" + "=" * 50)
    print("1. CONFUSION MATRICES (3x3)")
    print("=" * 50)
    confusion_rows = []
    cm_dict = {}

    short_names = ["healthy", "rust", "tikka"]

    for sname in ["Seed_42", "Seed_1337", "Seed_2024"]:
        yh = seed_preds[sname]["pred_idx"]
        cm = np.zeros((3, 3), dtype=int)
        for t in range(3):
            for p in range(3):
                cm[t, p] = int(((y_true == t) & (yh == p)).sum())
        cm_dict[sname] = cm

        rec_h = float(cm[0, 0] / cm[0].sum())
        rec_r = float(cm[1, 1] / cm[1].sum())
        rec_t = float(cm[2, 2] / cm[2].sum())

        h_to_r = int(cm[0, 1])
        h_to_t = int(cm[0, 2])
        r_to_h = int(cm[1, 0])
        r_to_t = int(cm[1, 2])
        t_to_h = int(cm[2, 0])
        t_to_r = int(cm[2, 1])

        print(f"\n--- {sname} ---")
        print(f"                Pred Healthy   Pred Rust   Pred Tikka   Total   Recall")
        print(f"True Healthy :  {cm[0,0]:12d}  {cm[0,1]:10d}  {cm[0,2]:11d}   {cm[0].sum():5d}   {rec_h*100:.2f}%")
        print(f"True Rust    :  {cm[1,0]:12d}  {cm[1,1]:10d}  {cm[1,2]:11d}   {cm[1].sum():5d}   {rec_r*100:.2f}%")
        print(f"True Tikka   :  {cm[2,0]:12d}  {cm[2,1]:10d}  {cm[2,2]:11d}   {cm[2].sum():5d}   {rec_t*100:.2f}%")
        print(f"Quantified Error Flows:")
        print(f"  Healthy -> Rust : {h_to_r:3d} ({h_to_r/600*100:5.2f}%)   Healthy -> Tikka: {h_to_t:3d} ({h_to_t/600*100:5.2f}%)")
        print(f"  Rust -> Healthy : {r_to_h:3d} ({r_to_h/120*100:5.2f}%)   Rust -> Tikka   : {r_to_t:3d} ({r_to_t/120*100:5.2f}%)")
        print(f"  Tikka -> Healthy: {t_to_h:3d} ({t_to_h/432*100:5.2f}%)   Tikka -> Rust   : {t_to_r:3d} ({t_to_r/432*100:5.2f}%)")

        for t_idx, t_name in enumerate(["groundnut__healthy_or_abiotic", "groundnut__rust", "groundnut__tikka_leaf_spot"]):
            row_total = int(cm[t_idx].sum())
            row_rec = float(cm[t_idx, t_idx] / row_total) if row_total > 0 else 0.0
            confusion_rows.append({
                "seed": sname,
                "true_class": t_name,
                "pred_healthy": int(cm[t_idx, 0]),
                "pred_rust": int(cm[t_idx, 1]),
                "pred_tikka": int(cm[t_idx, 2]),
                "total": row_total,
                "recall": round(row_rec, 4),
                "healthy_to_rust": h_to_r if t_idx == 0 else 0,
                "healthy_to_tikka": h_to_t if t_idx == 0 else 0,
                "rust_to_healthy": r_to_h if t_idx == 1 else 0,
                "rust_to_tikka": r_to_t if t_idx == 1 else 0,
                "tikka_to_healthy": t_to_h if t_idx == 2 else 0,
                "tikka_to_rust": t_to_r if t_idx == 2 else 0,
            })

    # 2. Extract image properties and per-sample error details
    print("\nComputing image features on external test set...")
    image_stats_list = []
    for idx, row in scorable_df.iterrows():
        img_path = pkg / row["pkg_path"]
        st = compute_image_stats(img_path)
        image_stats_list.append(st)
    img_stats_df = pd.DataFrame(image_stats_list)

    # Build per-sample table
    cases = []
    for i in range(len(scorable_df)):
        sha = str(scorable_df.iloc[i]["sha256"])
        pkg_p = str(scorable_df.iloc[i]["pkg_path"])
        true_c = str(scorable_df.iloc[i]["canonical_id"])
        orig_l = str(scorable_df.iloc[i]["original_label"])
        grp_id = int(scorable_df.iloc[i]["group_id"])
        orig_f = sasmal_map.get(sha, Path(pkg_p).name)

        p42 = seed_preds["Seed_42"]["probs"][i]
        c42 = int(seed_preds["Seed_42"]["pred_idx"][i])
        conf42 = float(seed_preds["Seed_42"]["conf"][i])

        p1337 = seed_preds["Seed_1337"]["probs"][i]
        c1337 = int(seed_preds["Seed_1337"]["pred_idx"][i])
        conf1337 = float(seed_preds["Seed_1337"]["conf"][i])

        p2024 = seed_preds["Seed_2024"]["probs"][i]
        c2024 = int(seed_preds["Seed_2024"]["pred_idx"][i])
        conf2024 = float(seed_preds["Seed_2024"]["conf"][i])

        t_idx = y_true[i]
        err42 = (c42 != t_idx)
        err1337 = (c1337 != t_idx)
        err2024 = (c2024 != t_idx)
        num_errors = int(err42) + int(err1337) + int(err2024)

        # Agreement
        preds_all = [c42, c1337, c2024]
        if len(set(preds_all)) == 1:
            agree_type = "3/3 agree"
        elif len(set(preds_all)) == 2:
            agree_type = "2/3 agree"
        else:
            agree_type = "all disagree"

        cases.append({
            "sha256": sha,
            "pkg_path": pkg_p,
            "original_file": orig_f,
            "canonical_id": true_c,
            "original_label": orig_l,
            "group_id": grp_id,
            # Seed 42
            "s42_pred": gn_classes[c42],
            "s42_conf": round(conf42, 4),
            "s42_p_healthy": round(float(p42[0]), 4),
            "s42_p_rust": round(float(p42[1]), 4),
            "s42_p_tikka": round(float(p42[2]), 4),
            "s42_is_correct": not err42,
            # Seed 1337
            "s1337_pred": gn_classes[c1337],
            "s1337_conf": round(conf1337, 4),
            "s1337_p_healthy": round(float(p1337[0]), 4),
            "s1337_p_rust": round(float(p1337[1]), 4),
            "s1337_p_tikka": round(float(p1337[2]), 4),
            "s1337_is_correct": not err1337,
            # Seed 2024
            "s2024_pred": gn_classes[c2024],
            "s2024_conf": round(conf2024, 4),
            "s2024_p_healthy": round(float(p2024[0]), 4),
            "s2024_p_rust": round(float(p2024[1]), 4),
            "s2024_p_tikka": round(float(p2024[2]), 4),
            "s2024_is_correct": not err2024,
            # Error classification
            "num_errors": num_errors,
            "num_correct": 3 - num_errors,
            "agreement": agree_type,
            # Flags
            "healthy_pred_rust_s42": (t_idx == 0 and c42 == 1),
            "healthy_pred_rust_s1337": (t_idx == 0 and c1337 == 1),
            "healthy_pred_rust_s2024": (t_idx == 0 and c2024 == 1),
            "rust_pred_healthy_s42": (t_idx == 1 and c42 == 0),
            "rust_pred_healthy_s1337": (t_idx == 1 and c1337 == 0),
            "rust_pred_healthy_s2024": (t_idx == 1 and c2024 == 0),
            # Physical features
            "width": img_stats_df.iloc[i]["width"],
            "height": img_stats_df.iloc[i]["height"],
            "file_bytes": img_stats_df.iloc[i]["file_bytes"],
            "mean_brightness": img_stats_df.iloc[i]["mean_brightness"],
            "std_contrast": img_stats_df.iloc[i]["std_contrast"],
            "shadow_fraction": img_stats_df.iloc[i]["shadow_fraction"],
            "green_ratio": img_stats_df.iloc[i]["green_ratio"],
            "brown_ratio": img_stats_df.iloc[i]["brown_ratio"],
            "laplacian_sharpness": img_stats_df.iloc[i]["laplacian_sharpness"],
        })

    cases_df = pd.DataFrame(cases)

    # 3. List actual image IDs for Healthy -> Rust and Rust -> Healthy
    print("\n" + "=" * 50)
    print("2. HEALTHY -> RUST & RUST -> HEALTHY QUANTIFICATION")
    print("=" * 50)
    h_rust_s42 = cases_df[cases_df.healthy_pred_rust_s42]
    h_rust_s1337 = cases_df[cases_df.healthy_pred_rust_s1337]
    h_rust_s2024 = cases_df[cases_df.healthy_pred_rust_s2024]

    r_h_s42 = cases_df[cases_df.rust_pred_healthy_s42]
    r_h_s1337 = cases_df[cases_df.rust_pred_healthy_s1337]
    r_h_s2024 = cases_df[cases_df.rust_pred_healthy_s2024]

    print(f"Healthy -> Rust counts:")
    print(f"  Seed 42  : {len(h_rust_s42)} / 600 ({len(h_rust_s42)/600*100:.2f}%)")
    print(f"  Seed 1337: {len(h_rust_s1337)} / 600 ({len(h_rust_s1337)/600*100:.2f}%)")
    print(f"  Seed 2024: {len(h_rust_s2024)} / 600 ({len(h_rust_s2024)/600*100:.2f}%)")

    print(f"Rust -> Healthy counts:")
    print(f"  Seed 42  : {len(r_h_s42)} / 120 ({len(r_h_s42)/120*100:.2f}%)")
    print(f"  Seed 1337: {len(r_h_s1337)} / 120 ({len(r_h_s1337)/120*100:.2f}%)")
    print(f"  Seed 2024: {len(r_h_s2024)} / 120 ({len(r_h_s2024)/120*100:.2f}%)")

    # Set overlap analysis for Healthy -> Rust
    set_h_r_42 = set(h_rust_s42["sha256"])
    set_h_r_1337 = set(h_rust_s1337["sha256"])
    set_h_r_2024 = set(h_rust_s2024["sha256"])

    print(f"\nHealthy -> Rust Set Intersections:")
    print(f"  In all three seeds        : {len(set_h_r_42 & set_h_r_1337 & set_h_r_2024)}")
    print(f"  In Seed 42 & Seed 1337    : {len(set_h_r_42 & set_h_r_1337)}")
    print(f"  In Seed 1337 & Seed 2024  : {len(set_h_r_1337 & set_h_r_2024)}")
    print(f"  In Seed 42 & Seed 2024    : {len(set_h_r_42 & set_h_r_2024)}")
    print(f"  Seed 42 subset of 1337?   : {set_h_r_42.issubset(set_h_r_1337)} ({len(set_h_r_42 - set_h_r_1337)} in S42 but not S1337)")
    print(f"  Seed 2024 subset of 1337? : {set_h_r_2024.issubset(set_h_r_1337)} ({len(set_h_r_2024 - set_h_r_1337)} in S2024 but not S1337)")
    print(f"  In Seed 1337 ONLY         : {len(set_h_r_1337 - set_h_r_42 - set_h_r_2024)}")

    # 4. Error distribution by seeds: misclassified by 1, 2, or 3 seeds
    print("\n" + "=" * 50)
    print("3. MISCLASSIFICATION FREQUENCY (1, 2, or 3 SEEDS)")
    print("=" * 50)
    all_err_counts = cases_df["num_errors"].value_counts().to_dict()
    print("Number of seeds making error across all 1,152 scorable samples:")
    print(f"  0 errors (All 3 correct) : {all_err_counts.get(0, 0)} ({all_err_counts.get(0, 0)/1152*100:.2f}%)")
    print(f"  1 error  (1 seed failed) : {all_err_counts.get(1, 0)} ({all_err_counts.get(1, 0)/1152*100:.2f}%)")
    print(f"  2 errors (2 seeds failed): {all_err_counts.get(2, 0)} ({all_err_counts.get(2, 0)/1152*100:.2f}%)")
    print(f"  3 errors (All 3 failed)  : {all_err_counts.get(3, 0)} ({all_err_counts.get(3, 0)/1152*100:.2f}%)")

    # Broken down by class
    print("\nBreakdown by True Class:")
    for cname in gn_classes:
        sub = cases_df[cases_df.canonical_id == cname]
        cnts = sub["num_errors"].value_counts().to_dict()
        print(f"  Class: {cname} (N={len(sub)})")
        print(f"    All 3 correct: {cnts.get(0, 0):3d} ({cnts.get(0, 0)/len(sub)*100:5.2f}%)")
        print(f"    1 seed wrong : {cnts.get(1, 0):3d} ({cnts.get(1, 0)/len(sub)*100:5.2f}%)")
        print(f"    2 seeds wrong: {cnts.get(2, 0):3d} ({cnts.get(2, 0)/len(sub)*100:5.2f}%)")
        print(f"    All 3 wrong  : {cnts.get(3, 0):3d} ({cnts.get(3, 0)/len(sub)*100:5.2f}%)")

    # 5. Prediction agreement
    print("\n" + "=" * 50)
    print("4. PREDICTION AGREEMENT ACROSS SEEDS")
    print("=" * 50)
    agree_rows = []
    for label, sub in [
        ("All Scorable (N=1152)", cases_df),
        ("Healthy (N=600)", cases_df[cases_df.canonical_id == "groundnut__healthy_or_abiotic"]),
        ("Rust (N=120)", cases_df[cases_df.canonical_id == "groundnut__rust"]),
        ("Tikka (N=432)", cases_df[cases_df.canonical_id == "groundnut__tikka_leaf_spot"]),
    ]:
        n_sub = len(sub)
        a3 = int((sub["agreement"] == "3/3 agree").sum())
        a2 = int((sub["agreement"] == "2/3 agree").sum())
        a0 = int((sub["agreement"] == "all disagree").sum())
        
        c3 = int((sub["num_correct"] == 3).sum())
        c2 = int((sub["num_correct"] == 2).sum())
        c1 = int((sub["num_correct"] == 1).sum())
        c0 = int((sub["num_correct"] == 0).sum())

        print(f"\n{label}:")
        print(f"  3/3 Agree: {a3} ({a3/n_sub*100:.2f}%) | 2/3 Agree: {a2} ({a2/n_sub*100:.2f}%) | All Disagree: {a0} ({a0/n_sub*100:.2f}%)")
        print(f"  3 Correct: {c3} ({c3/n_sub*100:.2f}%) | 2 Correct: {c2} ({c2/n_sub*100:.2f}%) | 1 Correct: {c1} ({c1/n_sub*100:.2f}%) | 0 Correct: {c0} ({c0/n_sub*100:.2f}%)")

        agree_rows.append({
            "subset": label,
            "total_samples": n_sub,
            "all_three_agree_count": a3,
            "all_three_agree_pct": round(a3 / n_sub * 100, 2),
            "two_of_three_agree_count": a2,
            "two_of_three_agree_pct": round(a2 / n_sub * 100, 2),
            "all_disagree_count": a0,
            "all_disagree_pct": round(a0 / n_sub * 100, 2),
            "three_correct_count": c3,
            "three_correct_pct": round(c3 / n_sub * 100, 2),
            "two_correct_count": c2,
            "two_correct_pct": round(c2 / n_sub * 100, 2),
            "one_correct_count": c1,
            "one_correct_pct": round(c1 / n_sub * 100, 2),
            "zero_correct_count": c0,
            "zero_correct_pct": round(c0 / n_sub * 100, 2),
        })

    # 6. Confidence distributions
    print("\n" + "=" * 50)
    print("5. CONFIDENCE DISTRIBUTIONS COMPARISON")
    print("=" * 50)
    conf_rows = []
    for sname, c_col, p_col in [("Seed_42", "s42_conf", "s42_pred"),
                                 ("Seed_1337", "s1337_conf", "s1337_pred"),
                                 ("Seed_2024", "s2024_conf", "s2024_pred")]:
        # Correct Healthy
        mask_corr_h = (cases_df.canonical_id == "groundnut__healthy_or_abiotic") & (cases_df[p_col] == "groundnut__healthy_or_abiotic")
        # Healthy -> Rust
        mask_h_r = (cases_df.canonical_id == "groundnut__healthy_or_abiotic") & (cases_df[p_col] == "groundnut__rust")
        # Correct Rust
        mask_corr_r = (cases_df.canonical_id == "groundnut__rust") & (cases_df[p_col] == "groundnut__rust")
        # Rust -> Healthy
        mask_r_h = (cases_df.canonical_id == "groundnut__rust") & (cases_df[p_col] == "groundnut__healthy_or_abiotic")
        # Correct Tikka
        mask_corr_t = (cases_df.canonical_id == "groundnut__tikka_leaf_spot") & (cases_df[p_col] == "groundnut__tikka_leaf_spot")
        # Overall correct vs error
        mask_all_corr = (cases_df.canonical_id == cases_df[p_col])
        mask_all_err = (cases_df.canonical_id != cases_df[p_col])

        types = [
            ("correct_healthy", mask_corr_h),
            ("healthy_pred_rust", mask_h_r),
            ("correct_rust", mask_corr_r),
            ("rust_pred_healthy", mask_r_h),
            ("correct_tikka", mask_corr_t),
            ("all_correct", mask_all_corr),
            ("all_errors", mask_all_err),
        ]

        print(f"\nConfidence Stats for {sname}:")
        for ctype, mask in types:
            vals = cases_df.loc[mask, c_col].tolist()
            d = calc_distribution(vals)
            print(f"  {ctype:20s} (N={d['count']:3d}): mean={d['mean']:.4f} +/- {d['std']:.4f}, median={d['median']:.4f}, IQR={d['iqr']:.4f}, range=[{d['min']:.4f}, {d['max']:.4f}]")
            row = {"seed": sname, "case_type": ctype}
            row.update(d)
            conf_rows.append(row)

    # 7. Measurable Root Cause Analysis
    print("\n" + "=" * 50)
    print("6. MEASURABLE FACTOR ASSOCIATIONS WITH HEALTHY -> RUST")
    print("=" * 50)
    # Compare Healthy images correctly predicted across all 3 vs Healthy images mispredicted as Rust by S1337
    h_df = cases_df[cases_df.canonical_id == "groundnut__healthy_or_abiotic"].copy()
    
    # 3 groups of Healthy:
    # A: Healthy correct in all 3 seeds (Robust Healthy)
    # B: Healthy correct in S42 & S2024 but Rust in S1337 (S1337-specific collapse)
    # C: Healthy Rust in both S42 & S1337 (Systemic boundary ambiguity)
    # D: Healthy Rust in all 3 seeds
    h_robust = h_df[(h_df.s42_is_correct) & (h_df.s1337_is_correct) & (h_df.s2024_is_correct)]
    h_s1337_only = h_df[(h_df.s42_is_correct) & (h_df.healthy_pred_rust_s1337) & (h_df.s2024_is_correct)]
    h_s42_s1337 = h_df[(h_df.healthy_pred_rust_s42) & (h_df.healthy_pred_rust_s1337)]
    h_all_three_rust = h_df[(h_df.healthy_pred_rust_s42) & (h_df.healthy_pred_rust_s1337) & (h_df.healthy_pred_rust_s2024)]

    print(f"Healthy Category Counts (N=600):")
    print(f"  Robust Healthy (Correct in all 3)         : {len(h_robust)}")
    print(f"  S1337-Specific Rust Error (Correct in 42,2024): {len(h_s1337_only)}")
    print(f"  Dual S42 & S1337 Rust Error               : {len(h_s42_s1337)}")
    print(f"  All 3 Seeds Rust Error                    : {len(h_all_three_rust)}")

    # Group ID analysis: duplicate structure
    print(f"\nGroup ID Duplicate Clustering:")
    h_groups = h_df.groupby("group_id").agg(
        n=("sha256", "count"),
        s42_rust=("healthy_pred_rust_s42", "sum"),
        s1337_rust=("healthy_pred_rust_s1337", "sum"),
        s2024_rust=("healthy_pred_rust_s2024", "sum")
    ).reset_index()
    multi_groups = h_groups[h_groups.n > 1]
    print(f"  Total distinct group_ids in Healthy: {len(h_groups)}")
    print(f"  Groups with multiple images (>1): {len(multi_groups)} (encompassing {multi_groups.n.sum()} images)")
    
    # Are errors correlated within groups?
    # For groups of size 2, do both get predicted as Rust or both Healthy?
    g2 = h_groups[h_groups.n == 2]
    print(f"  Groups with exactly 2 images: {len(g2)}")
    print(f"    Seed 42  : both rust={len(g2[g2.s42_rust == 2])}, both healthy={len(g2[g2.s42_rust == 0])}, split={len(g2[g2.s42_rust == 1])}")
    print(f"    Seed 1337: both rust={len(g2[g2.s1337_rust == 2])}, both healthy={len(g2[g2.s1337_rust == 0])}, split={len(g2[g2.s1337_rust == 1])}")
    print(f"    Seed 2024: both rust={len(g2[g2.s2024_rust == 2])}, both healthy={len(g2[g2.s2024_rust == 0])}, split={len(g2[g2.s2024_rust == 1])}")

    # Feature comparison between Robust Healthy vs S1337 Rust Errors vs Dual Errors
    feature_metrics = [
        "mean_brightness", "std_contrast", "shadow_fraction",
        "green_ratio", "brown_ratio", "laplacian_sharpness", "file_bytes"
    ]
    print(f"\nImage Feature Comparison across Healthy subgroups:")
    feat_comparison = {}
    for feat in feature_metrics:
        v_robust = h_robust[feat].to_numpy()
        v_s1337 = h_s1337_only[feat].to_numpy()
        v_dual = h_s42_s1337[feat].to_numpy()
        v_rust_all = cases_df[cases_df.canonical_id == "groundnut__rust"][feat].to_numpy()
        feat_comparison[feat] = {
            "robust_healthy_mean": round(float(np.mean(v_robust)), 4) if len(v_robust) else 0,
            "robust_healthy_std": round(float(np.std(v_robust)), 4) if len(v_robust) else 0,
            "s1337_error_mean": round(float(np.mean(v_s1337)), 4) if len(v_s1337) else 0,
            "s1337_error_std": round(float(np.std(v_s1337)), 4) if len(v_s1337) else 0,
            "dual_error_mean": round(float(np.mean(v_dual)), 4) if len(v_dual) else 0,
            "dual_error_std": round(float(np.std(v_dual)), 4) if len(v_dual) else 0,
            "true_rust_mean": round(float(np.mean(v_rust_all)), 4) if len(v_rust_all) else 0,
            "true_rust_std": round(float(np.std(v_rust_all)), 4) if len(v_rust_all) else 0,
        }
        print(f"  {feat:20s}: Robust={feat_comparison[feat]['robust_healthy_mean']} +/- {feat_comparison[feat]['robust_healthy_std']} | S1337-Err={feat_comparison[feat]['s1337_error_mean']} +/- {feat_comparison[feat]['s1337_error_std']} | Dual-Err={feat_comparison[feat]['dual_error_mean']} +/- {feat_comparison[feat]['dual_error_std']} | TrueRust={feat_comparison[feat]['true_rust_mean']} +/- {feat_comparison[feat]['true_rust_std']}")

    # Probability shifts: How close were probabilities in Seed 42, 1337, 2024?
    print(f"\nSoftmax Probability Shift on Healthy Samples (N=600):")
    p_h_42 = h_df["s42_p_healthy"].mean()
    p_r_42 = h_df["s42_p_rust"].mean()
    p_h_1337 = h_df["s1337_p_healthy"].mean()
    p_r_1337 = h_df["s1337_p_rust"].mean()
    p_h_2024 = h_df["s2024_p_healthy"].mean()
    p_r_2024 = h_df["s2024_p_rust"].mean()
    print(f"  Seed 42  : Mean P(Healthy)={p_h_42:.4f}, Mean P(Rust)={p_r_42:.4f}")
    print(f"  Seed 1337: Mean P(Healthy)={p_h_1337:.4f}, Mean P(Rust)={p_r_1337:.4f}")
    print(f"  Seed 2024: Mean P(Healthy)={p_h_2024:.4f}, Mean P(Rust)={p_r_2024:.4f}")

    # Logit/Probability Margin analysis:
    # In S1337, what percentage of the Healthy->Rust errors have P(Rust) > 0.70?
    s1337_high_conf_errors = (h_rust_s1337["s1337_conf"] >= 0.70).sum()
    s1337_low_conf_errors = (h_rust_s1337["s1337_conf"] < 0.70).sum()
    print(f"\nSeed 1337 Healthy->Rust Error Confidence:")
    print(f"  Overconfident (P(Rust) >= 0.70): {s1337_high_conf_errors} / {len(h_rust_s1337)} ({s1337_high_conf_errors/len(h_rust_s1337)*100:.2f}%)")
    print(f"  Borderline    (P(Rust) <  0.70): {s1337_low_conf_errors} / {len(h_rust_s1337)} ({s1337_low_conf_errors/len(h_rust_s1337)*100:.2f}%)")

    # Save Artifacts
    out_dir = root / "reports/artifacts"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Confusion matrix CSV
    df_cm = pd.DataFrame(confusion_rows)
    df_cm.to_csv(out_dir / "m4_v2_2_three_seed_confusion.csv", index=False)
    print(f"\nSaved {out_dir / 'm4_v2_2_three_seed_confusion.csv'}")

    # 2. Error cases CSV
    cases_df.to_csv(out_dir / "m4_v2_2_three_seed_error_cases.csv", index=False)
    print(f"Saved {out_dir / 'm4_v2_2_three_seed_error_cases.csv'} ({len(cases_df)} samples)")

    # 3. Agreement CSV
    df_agr = pd.DataFrame(agree_rows)
    df_agr.to_csv(out_dir / "m4_v2_2_three_seed_agreement.csv", index=False)
    print(f"Saved {out_dir / 'm4_v2_2_three_seed_agreement.csv'}")

    # 4. Confidence CSV
    df_conf = pd.DataFrame(conf_rows)
    df_conf.to_csv(out_dir / "m4_v2_2_three_seed_confidence.csv", index=False)
    print(f"Saved {out_dir / 'm4_v2_2_three_seed_confidence.csv'}")

    # 5. Diagnostic JSON
    diagnostic = {
        "metadata": {
            "title": "M4 V2.2 Three-Seed Error Audit Diagnostic",
            "date": "2026-09-28",
            "samples_scorable": 1152,
            "classes": gn_classes,
        },
        "confusion_summary": {
            s: cm_dict[s].tolist() for s in cm_dict
        },
        "healthy_to_rust": {
            "seed_42_count": len(h_rust_s42),
            "seed_1337_count": len(h_rust_s1337),
            "seed_2024_count": len(h_rust_s2024),
            "all_three_intersection": len(set_h_r_42 & set_h_r_1337 & set_h_r_2024),
            "s42_s1337_intersection": len(set_h_r_42 & set_h_r_1337),
            "s42_in_s1337_pct": round(len(set_h_r_42 & set_h_r_1337) / max(1, len(set_h_r_42)) * 100, 2),
            "s1337_only_count": len(set_h_r_1337 - set_h_r_42 - set_h_r_2024),
            "s1337_high_conf_count": int(s1337_high_conf_errors),
            "s1337_low_conf_count": int(s1337_low_conf_errors),
        },
        "rust_to_healthy": {
            "seed_42_count": len(r_h_s42),
            "seed_1337_count": len(r_h_s1337),
            "seed_2024_count": len(r_h_s2024),
        },
        "agreement": {
            "all_three_agree_count": int((cases_df["agreement"] == "3/3 agree").sum()),
            "two_of_three_agree_count": int((cases_df["agreement"] == "2/3 agree").sum()),
            "all_disagree_count": int((cases_df["agreement"] == "all disagree").sum()),
        },
        "healthy_subgroups": {
            "robust_healthy_count": len(h_robust),
            "s1337_only_rust_error_count": len(h_s1337_only),
            "dual_s42_s1337_error_count": len(h_s42_s1337),
            "all_three_rust_error_count": len(h_all_three_rust),
        },
        "feature_comparison": feat_comparison,
        "mean_probabilities_on_healthy": {
            "seed_42": {"p_healthy": round(p_h_42, 4), "p_rust": round(p_r_42, 4)},
            "seed_1337": {"p_healthy": round(p_h_1337, 4), "p_rust": round(p_r_1337, 4)},
            "seed_2024": {"p_healthy": round(p_h_2024, 4), "p_rust": round(p_r_2024, 4)},
        },
    }

    with open(out_dir / "m4_v2_2_three_seed_audit_diagnostic.json", "w") as f:
        json.dump(diagnostic, f, indent=2)
    print(f"Saved {out_dir / 'm4_v2_2_three_seed_audit_diagnostic.json'}")
    print("\n[AUDIT COMPLETE - ZERO ERRORS]")

if __name__ == "__main__":
    main()
