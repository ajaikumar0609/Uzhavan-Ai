"""Unit tests for M4 V2.3 Targeted Pure-Green Healthy Oversampling Sampler.
NO TRAINING - UNIT TESTS ONLY.

Verifies:
1. Exact identification of the 285 pure-green Healthy images in the training split.
2. Exact absence of pure-green images from other classes (zero false positives).
3. Exact sampling weights calculation ($w_{green} = 2236 / 285 \approx 7.8456$).
4. Empirical sampling ratio: pure-green Healthy to Tikka is 1.00 +- 0.02.
5. Determinism: identical random seed produces identical sample sequence.
6. Seed variance: different seeds produce different, reproducible sample sequences.
7. Data integrity: zero external West Bengal samples in training or sampler.
"""

import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
import torch

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ML_DIR = REPO_ROOT / "uzhavan_ml"
sys.path.insert(0, str(ML_DIR / "scripts"))

import v2_3_sampler as v23s

V2_MANIFEST = ML_DIR / "m4_v2/manifests/groundnut_v2.csv"
EXPECTED_SHA = "6768c740a0bc32ec45be08237c564e0be153a610caab9909196c1a0c123a4cfe"


class TestM4V23Sampler(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        assert V2_MANIFEST.exists(), f"Missing manifest: {V2_MANIFEST}"
        cls.df = pd.read_csv(V2_MANIFEST)
        cls.gn_df = cls.df[cls.df.crop == "groundnut"].copy().reset_index(drop=True)
        cls.train_df = cls.gn_df[cls.gn_df.split == "train"].copy().reset_index(drop=True)

    def test_01_pure_green_identification(self):
        """Test that exactly 285 pure-green Healthy images are identified in the training split."""
        green_mask = v23s.identify_pure_green_healthy(self.train_df)
        n_green = int(green_mask.sum())
        self.assertEqual(n_green, 285, f"Expected exactly 285 pure-green images, found {n_green}")

        # Check sub-properties of all 285 identified samples
        green_samples = self.train_df[green_mask]
        self.assertTrue((green_samples["canonical_id"] == "groundnut__healthy_or_abiotic").all())
        self.assertTrue((green_samples["v1_canonical_id"] == "groundnut__healthy").all())
        self.assertTrue((green_samples["original_label"] == "groundnut_healthy").all())

    def test_02_pure_green_exclusivity(self):
        """Test that nutrient deficiency, Tikka, and Rust are never flagged as pure-green."""
        green_mask = v23s.identify_pure_green_healthy(self.train_df)
        
        # Check nutrient deficiency (1,164 samples)
        nut_mask = (self.train_df["v1_canonical_id"] == "groundnut__nutrient_deficiency")
        self.assertEqual(int((green_mask & nut_mask).sum()), 0)
        
        # Check Tikka (2,236 samples)
        tikka_mask = (self.train_df["canonical_id"] == "groundnut__tikka_leaf_spot")
        self.assertEqual(int((green_mask & tikka_mask).sum()), 0)
        
        # Check Rust (2,235 samples)
        rust_mask = (self.train_df["canonical_id"] == "groundnut__rust")
        self.assertEqual(int((green_mask & rust_mask).sum()), 0)

    def test_03_sample_weights_calculation(self):
        """Test exact calculation of sample weights and analytical exposure ratio."""
        weights, stats = v23s.compute_v2_3_sample_weights(self.train_df)
        
        self.assertEqual(len(weights), 5920)
        expected_w_green = 2236.0 / 285.0
        self.assertAlmostEqual(stats["w_green"], expected_w_green, places=5)
        
        # Pure-green Healthy vs Tikka analytical ratio must be mathematically exactly 1.0
        self.assertAlmostEqual(stats["exposure_ratio_green_to_tikka"], 1.0, places=5)
        self.assertAlmostEqual(stats["prob_green"], stats["prob_tikka"], places=5)
        
        # Total weight sum: 2236 + 2236 + 2235 + 1164 = 7871
        self.assertAlmostEqual(stats["total_weight_sum"], 7871.0, places=1)

    def test_04_empirical_sampling_ratio(self):
        """Test that empirical draws from the sampler yield ~1:1 pure-green Healthy to Tikka ratio."""
        sampler, _, stats = v23s.build_v2_3_training_sampler(self.train_df, seed=42, policy="balanced")
        
        # Simulate 10 epochs of balanced sampling (10 * 7,871 = 78,710 draws)
        draws = []
        for _ in range(10):
            draws.extend(list(sampler))
        draws = np.array(draws)
        
        green_mask = v23s.identify_pure_green_healthy(self.train_df).to_numpy()
        tikka_mask = (self.train_df["canonical_id"] == "groundnut__tikka_leaf_spot").to_numpy()
        
        n_green_draws = int(green_mask[draws].sum())
        n_tikka_draws = int(tikka_mask[draws].sum())
        
        empirical_ratio = n_green_draws / float(n_tikka_draws)
        print(f"\n[TEST INFO] Empirical 10-epoch draws: Green={n_green_draws}, Tikka={n_tikka_draws}, Ratio={empirical_ratio:.4f}")
        
        # Must be within 2% of 1.00
        self.assertAlmostEqual(empirical_ratio, 1.0, delta=0.02)

    def test_05_sampler_determinism(self):
        """Test that the sampler produces identical sequences for identical seeds."""
        s1, _, _ = v23s.build_v2_3_training_sampler(self.train_df, seed=42, policy="dataset_size")
        s2, _, _ = v23s.build_v2_3_training_sampler(self.train_df, seed=42, policy="dataset_size")
        
        list1 = list(s1)
        list2 = list(s2)
        self.assertEqual(list1, list2, "Sampler failed determinism on identical seed (42)!")
        
        # Different seeds must produce different sequences
        s3, _, _ = v23s.build_v2_3_training_sampler(self.train_df, seed=1337, policy="dataset_size")
        list3 = list(s3)
        self.assertNotEqual(list1, list3, "Different seeds produced identical sequences!")

    def test_06_zero_external_leakage(self):
        """Test that no West Bengal external samples exist in the training set or sampler."""
        train_sources = self.train_df["source"].unique().tolist()
        self.assertNotIn("in_groundnut_wb_sasmal", train_sources)
        
        ext_df = self.gn_df[self.gn_df.split == "external_test"]
        ext_shas = set(ext_df["sha256"])
        train_shas = set(self.train_df["sha256"])
        
        overlap = ext_shas.intersection(train_shas)
        self.assertEqual(len(overlap), 0, f"Found {len(overlap)} overlapping samples between train and external test!")


if __name__ == "__main__":
    unittest.main()
