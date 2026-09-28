"""Tests for M4 V2 Data + Training Package.

Verifies:
1. Taxonomy mapping
2. Exact training class counts (Tikka: 2,236; Rust: 2,235; Healthy/Abiotic: 1,449; Total: 5,920)
3. No West Bengal external images in training split
4. Split integrity (train/val/test mutual exclusivity)
5. Duplicate experiment collision / overwrite protection
6. CUDA detection and strict CPU halt behavior
7. Checkpoint creation and resume mechanics
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

import pandas as pd
import torch

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ML_DIR = REPO_ROOT / "uzhavan_ml"
V2_MANIFEST = ML_DIR / "m4_v2/manifests/groundnut_v2.csv"
V2_CLASSES = ML_DIR / "m4_v2/classes.json"
TRAIN_SCRIPT = ML_DIR / "scripts/train_m4_v2.py"
PYTHON_BIN = sys.executable


class TestM4V2DataAndTraining(unittest.TestCase):

    def setUp(self):
        self.assertTrue(V2_MANIFEST.exists(), f"Missing manifest: {V2_MANIFEST}")
        self.assertTrue(V2_CLASSES.exists(), f"Missing classes file: {V2_CLASSES}")
        self.assertTrue(TRAIN_SCRIPT.exists(), f"Missing train script: {TRAIN_SCRIPT}")
        self.df = pd.read_csv(V2_MANIFEST)

    def test_taxonomy_mapping(self):
        """Verify taxonomy mapping from v1 biological classes to v2 canonical classes."""
        v1_to_v2 = {
            "groundnut__early_leaf_spot": "groundnut__tikka_leaf_spot",
            "groundnut__late_leaf_spot": "groundnut__tikka_leaf_spot",
            "groundnut__rust": "groundnut__rust",
            "groundnut__healthy": "groundnut__healthy_or_abiotic",
            "groundnut__nutrient_deficiency": "groundnut__healthy_or_abiotic",
        }
        for _, row in self.df.iterrows():
            v1_label = row["v1_canonical_id"]
            if v1_label in v1_to_v2:
                self.assertEqual(row["canonical_id"], v1_to_v2[v1_label])

        with open(V2_CLASSES) as f:
            classes = json.load(f)
        self.assertIn("groundnut", classes)
        self.assertEqual(
            classes["groundnut"],
            [
                "groundnut__healthy_or_abiotic",
                "groundnut__rust",
                "groundnut__tikka_leaf_spot",
            ]
        )

    def test_exact_class_counts(self):
        """Verify exact groundnut training split counts directly from manifest."""
        train_df = self.df[self.df.split == "train"]
        counts = train_df["canonical_id"].value_counts().to_dict()

        self.assertEqual(counts.get("groundnut__tikka_leaf_spot", 0), 2236, "Tikka count mismatch")
        self.assertEqual(counts.get("groundnut__rust", 0), 2235, "Rust count mismatch")
        self.assertEqual(counts.get("groundnut__healthy_or_abiotic", 0), 1449, "Healthy/Abiotic count mismatch")
        self.assertEqual(len(train_df), 5920, "Total training count mismatch")

    def test_no_wb_external_images_in_training(self):
        """Ensure zero West Bengal external images are in training or validation splits."""
        train_sources = self.df[self.df.split == "train"]["source"].unique().tolist()
        val_sources = self.df[self.df.split == "val"]["source"].unique().tolist()

        self.assertNotIn("in_groundnut_wb_sasmal", train_sources)
        self.assertNotIn("in_groundnut_wb_sasmal", val_sources)
        # Verify WB images exist only in external_test
        ext_sources = self.df[self.df.split == "external_test"]["source"].unique().tolist()
        self.assertIn("in_groundnut_wb_sasmal", ext_sources)

    def test_split_integrity(self):
        """Verify train, val, and test splits are mutually exclusive and have no image path overlap."""
        train_paths = set(self.df[self.df.split == "train"]["pkg_path"])
        val_paths = set(self.df[self.df.split == "val"]["pkg_path"])
        test_paths = set(self.df[self.df.split == "test"]["pkg_path"])
        ext_paths = set(self.df[self.df.split == "external_test"]["pkg_path"])

        self.assertEqual(len(train_paths.intersection(val_paths)), 0, "Train and Val overlap!")
        self.assertEqual(len(train_paths.intersection(test_paths)), 0, "Train and Test overlap!")
        self.assertEqual(len(val_paths.intersection(test_paths)), 0, "Val and Test overlap!")
        self.assertEqual(len(train_paths.intersection(ext_paths)), 0, "Train and External overlap!")

    def test_cuda_detection_and_strict_cpu_halt(self):
        """Verify train_m4_v2.py reports hardware and strictly stops when CUDA is missing."""
        cmd = [
            PYTHON_BIN,
            str(TRAIN_SCRIPT),
            "--out-dir", str(ML_DIR / "runs_m4_v2/test_cuda_detect"),
            "--exp-name", "test-cuda-detect",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        # On macOS, CUDA is not available, so it should exit with code 1 and error message
        if not torch.cuda.is_available():
            self.assertEqual(res.returncode, 1)
            self.assertIn("[ERROR] CUDA is not available. Training stopped.", res.stdout)
            self.assertIn("PyTorch Version:", res.stdout)
            self.assertIn("CUDA Available:       False", res.stdout)

    def test_no_duplicate_experiment_overwrite(self):
        """Verify that completed experiments cannot be silently overwritten."""
        test_dir = ML_DIR / "runs_m4_v2/test_collision_exp"
        exp_id = "test-collision"
        exp_dir = test_dir / exp_id
        exp_dir.mkdir(parents=True, exist_ok=True)

        # Create a fake completed experiment.json
        meta = {
            "experiment_id": exp_id,
            "status": "completed",
            "best_val_macro_f1": 0.95,
        }
        with open(exp_dir / "experiment.json", "w") as f:
            json.dump(meta, f)

        # Attempt to run without --resume
        cmd = [
            PYTHON_BIN,
            str(TRAIN_SCRIPT),
            "--allow-cpu",
            "--out-dir", str(test_dir),
            "--exp-name", exp_id,
            "--resume", "none",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        try:
            self.assertNotEqual(res.returncode, 0)
            self.assertIn("[COLLISION PROTECTION]", res.stdout)
        finally:
            shutil.rmtree(test_dir, ignore_errors=True)

    def test_checkpoint_creation_and_resume(self):
        """Verify checkpoint saving and resume behavior using smoke test."""
        test_dir = ML_DIR / "runs_m4_v2/test_resume_exp"
        exp_id = "test-resume-flow"
        exp_dir = test_dir / exp_id
        shutil.rmtree(test_dir, ignore_errors=True)

        try:
            # 1. Run initial 1-epoch smoke test
            cmd1 = [
                PYTHON_BIN,
                str(TRAIN_SCRIPT),
                "--smoke-test",
                "--allow-cpu",
                "--epochs", "1",
                "--out-dir", str(test_dir),
                "--exp-name", exp_id,
            ]
            res1 = subprocess.run(cmd1, capture_output=True, text=True)
            self.assertEqual(res1.returncode, 0, f"Initial run failed: {res1.stderr}")

            # Verify artifacts created
            self.assertTrue((exp_dir / "checkpoint_best.pt").exists())
            self.assertTrue((exp_dir / "checkpoint_last.pt").exists())
            self.assertTrue((exp_dir / "experiment.json").exists())
            self.assertTrue((exp_dir / "history.json").exists())

            # Load checkpoint to check contents
            ckpt = torch.load(exp_dir / "checkpoint_last.pt", map_location="cpu", weights_only=False)
            self.assertIn("model_state_dict", ckpt)
            self.assertIn("optimizer_state_dict", ckpt)
            self.assertEqual(ckpt["last_completed_epoch"], 0)

            # 2. Test resume
            cmd2 = [
                PYTHON_BIN,
                str(TRAIN_SCRIPT),
                "--smoke-test",
                "--allow-cpu",
                "--epochs", "2",
                "--out-dir", str(test_dir),
                "--exp-name", exp_id,
                "--resume", "auto",
            ]
            res2 = subprocess.run(cmd2, capture_output=True, text=True)
            self.assertEqual(res2.returncode, 0, f"Resume run failed: {res2.stderr}")
            self.assertIn("[RESUME] Loading checkpoint", res2.stdout)
            self.assertIn("Resuming from epoch 1", res2.stdout)

        finally:
            shutil.rmtree(test_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
