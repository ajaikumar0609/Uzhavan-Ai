"""
Builds the M4 v2 Groundnut Manifest and metadata:
- uzhavan_ml/m4_v2/manifests/groundnut_v2.csv
- uzhavan_ml/m4_v2/manifests/groundnut_v2.json
- uzhavan_ml/m4_v2/classes.json

Validates exact expected class counts from the source manifest:
  tikka_leaf_spot: 2,236
  rust: 2,235
  healthy_or_abiotic: 1,449
  total training: 5,920
"""
import hashlib
import json
from pathlib import Path
import pandas as pd

REPO_ROOT = Path("/Users/ajaikumarn/Desktop/agri")
SOURCE_MANIFEST = REPO_ROOT / "uzhavan_ml/packages/m4_v1/manifest.csv"
V2_DIR = REPO_ROOT / "uzhavan_ml/m4_v2"
MANIFEST_DIR = V2_DIR / "manifests"
MANIFEST_DIR.mkdir(parents=True, exist_ok=True)

print("Reading source manifest:", SOURCE_MANIFEST)
df = pd.read_csv(SOURCE_MANIFEST)

# Filter groundnut only
gn = df[df.crop == "groundnut"].copy()
print(f"Total groundnut rows in source manifest: {len(gn)}")

# Taxonomy mapping rules
V2_MAPPING = {
    "groundnut__early_leaf_spot": "groundnut__tikka_leaf_spot",
    "groundnut__late_leaf_spot": "groundnut__tikka_leaf_spot",
    "groundnut__rust": "groundnut__rust",
    "groundnut__healthy": "groundnut__healthy_or_abiotic",
    "groundnut__nutrient_deficiency": "groundnut__healthy_or_abiotic",
    # External test mappings
    "groundnut__tikka_leaf_spot": "groundnut__tikka_leaf_spot",
    "groundnut__alternaria_leaf_spot": "groundnut__alternaria_leaf_spot",
    "groundnut__rosette_virus": "groundnut__rosette_virus",
}

# Preserve v1 canonical id
gn["v1_canonical_id"] = gn["canonical_id"]
gn["canonical_id"] = gn["v1_canonical_id"].map(V2_MAPPING)

# Check for unmapped labels
unmapped = gn[gn["canonical_id"].isna()]
if len(unmapped) > 0:
    raise ValueError(f"Found unmapped labels: {unmapped['v1_canonical_id'].unique()}")

# Verify training counts
train_counts = gn[gn.split == "train"]["canonical_id"].value_counts().to_dict()
print("\n--- Verified Groundnut V2 Training Counts ---")
for cls, count in sorted(train_counts.items()):
    print(f"  {cls}: {count}")

expected_train_counts = {
    "groundnut__tikka_leaf_spot": 2236,
    "groundnut__rust": 2235,
    "groundnut__healthy_or_abiotic": 1449,
}

total_train = sum(train_counts.values())
print(f"  TOTAL TRAINING SAMPLES: {total_train}")

# Strict count verification
for cls, expected in expected_train_counts.items():
    actual = train_counts.get(cls, 0)
    if actual != expected:
        raise ValueError(
            f"COUNT MISMATCH for {cls}: expected {expected}, computed {actual}. "
            "Stopping immediately as mandated by instructions."
        )

if total_train != 5920:
    raise ValueError(f"TOTAL COUNT MISMATCH: expected 5920, computed {total_train}")

print("\n✓ Strict class count verification PASSED successfully.")

# Verify external images not in train
train_sources = gn[gn.split == "train"]["source"].unique().tolist()
print(f"Training split sources: {train_sources}")
if "in_groundnut_wb_sasmal" in train_sources:
    raise ValueError("FATAL: External West Bengal images detected in training split!")
print("✓ No West Bengal external images in training split.")

# Save CSV
csv_out = MANIFEST_DIR / "groundnut_v2.csv"
gn.to_csv(csv_out, index=False)
print(f"Saved: {csv_out}")

# Compute SHA256 checksum of manifest
sha256 = hashlib.sha256(csv_out.read_bytes()).hexdigest()
print(f"Manifest SHA256: {sha256}")

# Create summary JSON
summary_json = {
    "manifest_version": "m4_v2_groundnut",
    "source_manifest": str(SOURCE_MANIFEST.relative_to(REPO_ROOT)),
    "sha256": sha256,
    "total_samples": len(gn),
    "splits": {
        "train": {
            "total": int((gn.split == "train").sum()),
            "sources": gn[gn.split == "train"]["source"].unique().tolist(),
            "classes": {k: int(v) for k, v in gn[gn.split == "train"]["canonical_id"].value_counts().items()},
        },
        "val": {
            "total": int((gn.split == "val").sum()),
            "sources": gn[gn.split == "val"]["source"].unique().tolist(),
            "classes": {k: int(v) for k, v in gn[gn.split == "val"]["canonical_id"].value_counts().items()},
        },
        "test": {
            "total": int((gn.split == "test").sum()),
            "sources": gn[gn.split == "test"]["source"].unique().tolist(),
            "classes": {k: int(v) for k, v in gn[gn.split == "test"]["canonical_id"].value_counts().items()},
        },
        "external_test": {
            "total": int((gn.split == "external_test").sum()),
            "sources": gn[gn.split == "external_test"]["source"].unique().tolist(),
            "classes": {k: int(v) for k, v in gn[gn.split == "external_test"]["canonical_id"].value_counts().items()},
        },
    },
    "taxonomy_mapping": V2_MAPPING,
}

json_out = MANIFEST_DIR / "groundnut_v2.json"
with open(json_out, "w") as f:
    json.dump(summary_json, f, indent=2)
print(f"Saved: {json_out}")

# Save m4_v2/classes.json (groundnut updated, others preserved)
v1_classes_path = REPO_ROOT / "uzhavan_ml/runs_m4/UZ-M4-v1.0-a898475e-s1/classes.json"
with open(v1_classes_path) as f:
    classes_v2 = json.load(f)

classes_v2["groundnut"] = [
    "groundnut__healthy_or_abiotic",
    "groundnut__rust",
    "groundnut__tikka_leaf_spot",
]

classes_out = V2_DIR / "classes.json"
with open(classes_out, "w") as f:
    json.dump(classes_v2, f, indent=1)
print(f"Saved: {classes_out}")
print("M4 v2 groundnut manifest generation complete!")
