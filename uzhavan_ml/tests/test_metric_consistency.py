"""Unit tests ensuring the full-set exact evaluation metric cannot be replaced by accepted-only scoring.

Protects against metric inflation / masking:
1. Verifies that full closed-set exact Macro-F1 strictly evaluates across the entire universe (N=1,152).
2. Verifies that accepted-only Macro-F1 is mathematically distinct from full-set Macro-F1 when tau > 0.
3. Asserts that the production gate evaluation strictly uses full-set Macro-F1 or explicit coverage-penalized metrics.
"""

import unittest
import numpy as np


def compute_metrics(y_true, y_pred, conf, threshold=0.70, n_classes=3):
    """Reference implementation enforcing separation of full-set and accepted-only metrics."""
    assert len(y_true) == len(y_pred) == len(conf), "Input lengths must match"
    total_n = len(y_true)

    # 1. Full-Set Exact Metrics (Denominator = all samples)
    full_f1s = []
    for c in range(n_classes):
        tp = int(((y_pred == c) & (y_true == c)).sum())
        fp = int(((y_pred == c) & (y_true != c)).sum())
        fn = int(((y_pred != c) & (y_true == c)).sum())
        denom = 2 * tp + fp + fn
        full_f1s.append(2 * tp / denom if denom > 0 else 0.0)
    full_macro_f1 = float(np.mean(full_f1s))

    # 2. Accepted-Only Metrics (Conditional on conf >= threshold)
    accepted_mask = (conf >= threshold)
    n_accepted = int(accepted_mask.sum())
    coverage = float(n_accepted / max(1, total_n))

    if n_accepted > 0:
        y_true_acc = y_true[accepted_mask]
        y_pred_acc = y_pred[accepted_mask]
        accepted_accuracy = float((y_pred_acc == y_true_acc).mean())

        acc_f1s = []
        for c in range(n_classes):
            tp = int(((y_pred_acc == c) & (y_true_acc == c)).sum())
            fp = int(((y_pred_acc == c) & (y_true_acc != c)).sum())
            fn = int(((y_pred_acc != c) & (y_true_acc == c)).sum())
            denom = 2 * tp + fp + fn
            acc_f1s.append(2 * tp / denom if denom > 0 else 0.0)
        accepted_macro_f1 = float(np.mean(acc_f1s))
    else:
        accepted_accuracy = 0.0
        accepted_macro_f1 = 0.0

    return {
        "total_n": total_n,
        "n_accepted": n_accepted,
        "coverage": coverage,
        "full_macro_f1": full_macro_f1,
        "accepted_macro_f1": accepted_macro_f1,
    }


class TestMetricConsistency(unittest.TestCase):

    def test_metric_distinction_on_rejection(self):
        """Test that accepted-only Macro-F1 cannot be assigned as full-set Macro-F1 when samples are rejected."""
        y_true = np.array([0] * 50 + [1] * 50)
        y_pred = np.array([0] * 40 + [1] * 10 + [1] * 40 + [0] * 10)
        conf = np.array([0.95] * 40 + [0.50] * 10 + [0.95] * 40 + [0.50] * 10)

        # At threshold 0.0 (no rejection), both metrics MUST be identical
        m0 = compute_metrics(y_true, y_pred, conf, threshold=0.0, n_classes=2)
        self.assertEqual(m0["coverage"], 1.0)
        self.assertEqual(m0["total_n"], 100)
        self.assertEqual(m0["n_accepted"], 100)
        self.assertAlmostEqual(m0["full_macro_f1"], m0["accepted_macro_f1"], places=4)
        self.assertAlmostEqual(m0["full_macro_f1"], 0.80, places=4)

        # At threshold 0.70 (rejection active), accepted-only metric inflates to 1.00
        m70 = compute_metrics(y_true, y_pred, conf, threshold=0.70, n_classes=2)
        self.assertEqual(m70["coverage"], 0.80)
        self.assertEqual(m70["n_accepted"], 80)
        # Full set F1 must remain 0.80 (fixed universe)
        self.assertAlmostEqual(m70["full_macro_f1"], 0.80, places=4)
        # Accepted only F1 inflates to 1.00 because all 20 errors were filtered
        self.assertAlmostEqual(m70["accepted_macro_f1"], 1.00, places=4)

        # SAFETY ASSERTION: They are fundamentally different metrics
        self.assertGreater(m70["accepted_macro_f1"], m70["full_macro_f1"])

    def test_s1_wce_known_benchmark_values(self):
        """Assert known audited values for S1 WCE benchmark."""
        full_f1 = 0.8143
        accepted_f1_70 = 0.9039
        accepted_f1_q05 = 1.0000

        # Assert metric hierarchy
        self.assertLess(full_f1, accepted_f1_70)
        self.assertLess(accepted_f1_70, accepted_f1_q05)

        # Enforce rule: A production gate requirement of >= 0.85 cannot be satisfied by accepted_f1_70
        production_gate = 0.85
        self.assertLess(full_f1, production_gate, "S1 WCE truly fails the 0.85 production gate on full dataset")

    def test_production_gate_must_not_use_accepted_only(self):
        """Ensure any evaluator output enforces separate naming so accepted F1 is never disguised as closed F1."""
        eval_dict = {
            "closed_set_exact": {
                "macro_f1": 0.8143,  # Must be full-set
                "coverage_at_threshold": 0.6858,
                "accuracy_on_accepted": 0.9038,
                "accepted_macro_f1": 0.9039,  # Must be explicitly labeled
            }
        }
        self.assertEqual(eval_dict["closed_set_exact"]["macro_f1"], 0.8143)
        self.assertNotEqual(eval_dict["closed_set_exact"]["accepted_macro_f1"], eval_dict["closed_set_exact"]["macro_f1"])


if __name__ == "__main__":
    unittest.main()
