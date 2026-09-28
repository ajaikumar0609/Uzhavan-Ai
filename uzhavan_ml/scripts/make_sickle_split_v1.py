"""SICKLE split_v1: freeze a plot-disjoint local TEST carved from the authors' TRAIN plots.
Authors' val kept as val. Authors' test (labels withheld) kept but flagged unusable. Raw CSV untouched.
NOTE: WACV checkpoints were trained on the train plots, so split_v1 test is only a valid hold-out for FUTURE retraining."""
import hashlib, json
import numpy as np, pandas as pd
from pathlib import Path
SRC = Path.home()/"Desktop/agri/sickle_dataset/sickle_dataset_tabular.csv"
OUT = Path.home()/"Desktop/agri/uzhavan_data/01_sickle/processed/splits"
SEED, TEST_FRAC = 20260925, 0.10
df = pd.read_csv(SRC)
lab = df[df.SPLIT == "train"].copy()
# one row per plot: stratify on majority river part x has-paddy-yield
p = lab.groupby("PLOT_ID").agg(river=("RIVER_PART", lambda s: s.mode().iat[0] if s.notna().any() else "NA"),
                               paddy_yield=("YIELD", lambda s: bool((s > 0).any())), n_rows=("UNIQUE_ID","size")).reset_index()
p["stratum"] = p.river.astype(str) + "|" + p.paddy_yield.astype(str)
rng = np.random.default_rng(SEED); test_plots = []
for _, g in p.groupby("stratum"):
    k = int(round(len(g) * TEST_FRAC)); test_plots += list(rng.choice(g.PLOT_ID.values, size=k, replace=False)) if k else []
test_plots = set(test_plots)
df["SPLIT_UZ_V1"] = df.SPLIT.map({"val": "val", "test": "author_test_unlabelled"})
df.loc[df.SPLIT == "train", "SPLIT_UZ_V1"] = np.where(df.loc[df.SPLIT == "train", "PLOT_ID"].isin(test_plots), "test", "train")
out = df[["UNIQUE_ID","PLOT_ID","YEAR","STANDARD_SEASON","RIVER_PART","CROP","YIELD","SPLIT","SPLIT_UZ_V1"]]
f = OUT/"sickle_split_v1.csv"; out.to_csv(f, index=False)
# checks
lab_all = out[out.SPLIT_UZ_V1.isin(["train","val","test"])]
cross = lab_all.groupby("PLOT_ID").SPLIT_UZ_V1.nunique().gt(1).sum()
summary = {"split_version": "sickle_split_v1", "seed": SEED, "test_frac_of_train_plots": TEST_FRAC,
  "source_csv_sha256": hashlib.sha256(SRC.read_bytes()).hexdigest(), "split_csv_sha256": hashlib.sha256(f.read_bytes()).hexdigest(),
  "plots_crossing_splits": int(cross),
  "rows": out.SPLIT_UZ_V1.value_counts().to_dict(),
  "plots": lab_all.groupby("SPLIT_UZ_V1").PLOT_ID.nunique().to_dict(),
  "paddy_yield_rows": lab_all[lab_all.YIELD > 0].SPLIT_UZ_V1.value_counts().to_dict(),
  "rows_by_year": pd.crosstab(lab_all.SPLIT_UZ_V1, lab_all.YEAR).to_dict("index"),
  "valid_use": {"test": "hold-out for FUTURE retrained/fine-tuned models only. WACV checkpoints trained on these plots",
                "val": "baseline evaluation of existing WACV checkpoints (checkpoint_last primary)",
                "author_test_unlabelled": "never used (labels withheld)"}}
json.dump(summary, open(OUT/"sickle_split_v1.json","w"), indent=2, default=str); print(json.dumps(summary, indent=1, default=str))
