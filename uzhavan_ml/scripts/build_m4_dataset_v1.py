"""M4 v1 processed disease dataset: exact dups -> near-dup groups -> conflicting-label quarantine -> leakage-safe splits.
Raw images are never copied or modified; the output is a manifest referencing raw paths.
Crops (sign-off 2026-09-25): banana, coconut, groundnut, sugarcane, black_gram, chilli. Rice excluded (Paddy Doctor not obtained).
"""
import json, hashlib
from pathlib import Path
import numpy as np, pandas as pd

D = Path.home() / "Desktop/agri/uzhavan_data/06_disease_pest"
OUT = D / "processed/m4_v1"; OUT.mkdir(parents=True, exist_ok=True)
CROPS = ["banana", "coconut", "groundnut", "sugarcane", "black_gram", "chilli"]
SOURCES = {"in_tn_multicrop_vitc": D / "icar/in_tn_multicrop_vitc/raw", "in_coconut_tree_disease": D / "icar/in_coconut_tree_disease/raw",
           "in_sugarcane_leaf_disease_mh": D / "icar/in_sugarcane_leaf_disease_mh/raw", "in_groundnut_wb_sasmal": D / "icar/in_groundnut_wb_sasmal/raw",
           "in_blackgram_bpld_ap": D / "icar/in_blackgram_bpld_ap/raw"}
PHASH_MAX_DIST = 6          # near-duplicate threshold (bits of 64)
SEED = 20260925
SPLIT = (0.70, 0.15, 0.15)
# sign-off: normalise the WB source's merged early+late label to tikka; never claim separate etiology
RENAME = {"groundnut__tikka_leaf_spot": "groundnut__tikka_leaf_spot"}

cm = pd.DataFrame(json.load(open(D / "metadata/class_mapping.json"))["classes"])
rows = []
for src, root in SOURCES.items():
    m = pd.read_csv(D / f"metadata/manifests/{src}.csv")
    m["source"] = src
    m = m.merge(cm[cm.source == src][["original_label", "crop", "canonical_id"]], left_on="labels", right_on="original_label", how="left")
    rows.append(m)
df = pd.concat(rows, ignore_index=True)
df["quarantine"] = ""
df.loc[df.ok != 1, "quarantine"] = "unreadable"
df.loc[df.canonical_id.isna() & (df.quarantine == ""), "quarantine"] = "unmapped_or_multilabel"
df = df[df.crop.isin(CROPS) | (df.quarantine != "")].copy()
df.loc[df.crop.isna(), "crop"] = df.loc[df.crop.isna(), "labels"].astype(str).str.split("_").str[0]
df = df[df.crop.isin(CROPS)].copy()
df["canonical_id"] = df.canonical_id.replace(RENAME)
df["abs_path"] = [str(SOURCES[s] / "extracted" / r) for s, r in zip(df.source, df.relpath)]
missing = [p for p in df.abs_path if not Path(p).is_file()]
assert not missing, f"{len(missing)} image paths missing, e.g. {missing[:2]}"

# ---- union-find over exact (sha256) and near (phash) duplicates, per crop, across sources
parent = {}
def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]; x = parent[x]
    return x
def union(a, b):
    ra, rb = find(a), find(b)
    if ra != rb: parent[rb] = ra
idx = df.index.to_list()
for i in idx: parent[i] = i
for _, g in df.groupby("sha256"):
    ii = g.index.to_list()
    for j in ii[1:]: union(ii[0], j)
POP = np.array([bin(i).count("1") for i in range(256)], dtype=np.uint8)
def popcount64(x):
    b = x.view(np.uint8).reshape(*x.shape, 8)
    return POP[b].sum(-1)
near_pairs = 0
for crop, g in df.groupby("crop"):
    ok = g[g.phash.notna()]
    h = np.array([int(p, 16) for p in ok.phash], dtype=np.uint64); ii = ok.index.to_numpy()
    for s in range(0, len(h), 512):
        d = popcount64(np.bitwise_xor(h[s:s + 512, None], h[None, :]))
        a, b = np.nonzero(d <= PHASH_MAX_DIST)
        for x, y in zip(a + s, b):
            if x < y: union(ii[x], ii[y]); near_pairs += 1
df["group_id"] = [find(i) for i in df.index]
gsize = df.groupby("group_id").size(); df["group_size"] = df.group_id.map(gsize)

# ---- conflicting-label groups -> quarantine whole group
nlab = df[df.quarantine == ""].groupby("group_id").canonical_id.nunique()
conflict = set(nlab[nlab > 1].index)
df.loc[df.group_id.isin(conflict) & (df.quarantine == ""), "quarantine"] = "conflicting_label_group"
# exact duplicates: keep one representative per sha256 inside the dataset (others quarantined as duplicate)
dup = df[df.quarantine == ""].duplicated("sha256", keep="first")
df.loc[dup[dup].index, "quarantine"] = "exact_duplicate_removed"

# ---- splits. Primary source per crop = largest; other sources for that crop = EXTERNAL cross-source test.
use = df[df.quarantine == ""]
primary = use.groupby(["crop", "source"]).size().reset_index().sort_values(0).groupby("crop").tail(1).set_index("crop").source.to_dict()
df["role"] = np.where(df.source == df.crop.map(primary), "primary", "external_test")
# groups spanning primary + external sources: keep in primary train, drop from external test (external must be disjoint)
span = df[df.quarantine == ""].groupby("group_id").role.nunique()
span_groups = set(span[span > 1].index)
df.loc[df.group_id.isin(span_groups) & (df.role == "external_test") & (df.quarantine == ""), "quarantine"] = "external_overlaps_primary_group"
rng = np.random.default_rng(SEED)
df["split"] = ""
for (crop, cls), g in df[(df.quarantine == "") & (df.role == "primary")].groupby(["crop", "canonical_id"]):
    groups = g.group_id.unique(); rng.shuffle(groups)
    sizes = g.groupby("group_id").size().reindex(groups).to_numpy(); cum = np.cumsum(sizes) / sizes.sum()
    lab = np.where(cum <= SPLIT[0], "train", np.where(cum <= SPLIT[0] + SPLIT[1], "val", "test"))
    if "test" not in lab and len(lab) >= 3: lab[-1] = "test"
    if "val" not in lab and len(lab) >= 3: lab[-2] = "val"
    df.loc[g.index, "split"] = g.group_id.map(dict(zip(groups, lab)))
# a group must not be split across classes' split assignment (can't: conflicts quarantined) -> verify
chk = df[df.split != ""].groupby("group_id").split.nunique()
assert (chk <= 1).all(), "group crosses splits"
df.loc[(df.role == "external_test") & (df.quarantine == ""), "split"] = "external_test"

cols = ["abs_path", "source", "crop", "canonical_id", "labels", "role", "split", "group_id", "group_size", "sha256", "phash", "width", "height", "quarantine"]
out = df[cols].rename(columns={"labels": "original_label"}).sort_values(["crop", "canonical_id", "split"])
f = OUT / "m4_v1_manifest.csv"; out.to_csv(f, index=False)
kept = out[out.quarantine == ""]
summary = {
  "dataset_version": "m4_v1", "split_version": "m4_v1_split_seed%d" % SEED, "phash_max_dist": PHASH_MAX_DIST, "split_ratios": SPLIT,
  "manifest_sha256": hashlib.sha256(f.read_bytes()).hexdigest(),
  "images_considered": int(len(out)), "images_kept": int(len(kept)),
  "quarantine": out[out.quarantine != ""].quarantine.value_counts().to_dict(),
  "near_duplicate_pairs": int(near_pairs), "conflicting_label_groups": len(conflict),
  "primary_source_by_crop": primary,
  "cross_source_test_available": {c: bool(((kept.crop == c) & (kept.split == "external_test")).any()) for c in CROPS},
  "per_crop_split": kept.groupby(["crop", "split"]).size().unstack(fill_value=0).to_dict("index"),
  "per_class_split": kept.groupby(["canonical_id", "split"]).size().unstack(fill_value=0).to_dict("index"),
  "groups_crossing_splits": 0,
}
json.dump(summary, open(OUT / "m4_v1_summary.json", "w"), indent=1, default=int)
print(json.dumps({k: v for k, v in summary.items() if k != "per_class_split"}, indent=1, default=int))
