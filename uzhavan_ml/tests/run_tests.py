"""
Standalone test runner for M4 v2 evaluation tests.
Executes test functions and reports pass/fail.
"""
import sys
from pathlib import Path

# Add tests directory
TESTS_DIR = Path(__file__).parent
sys.path.insert(0, str(TESTS_DIR))

import unittest
import test_m4_v2_eval
import test_m4_v2_training

test_funcs = [getattr(test_m4_v2_eval, name) for name in dir(test_m4_v2_eval) if name.startswith("test_")]

print(f"Running {len(test_funcs)} M4 v2 evaluation unit tests...")
passed = 0
failed = 0

for fn in test_funcs:
    try:
        fn()
        print(f"  ✓ {fn.__name__}")
        passed += 1
    except Exception as exc:
        print(f"  ✗ {fn.__name__}: {exc}")
        failed += 1

print("\nRunning M4 v2 data + training package unit tests...")
suite = unittest.defaultTestLoader.loadTestsFromModule(test_m4_v2_training)
runner = unittest.TextTestRunner(verbosity=2)
training_result = runner.run(suite)

total_passed = passed + (training_result.testsRun - len(training_result.failures) - len(training_result.errors))
total_failed = failed + len(training_result.failures) + len(training_result.errors)

print("\n" + "=" * 50)
print(f"M4 v2 Total Test Summary: {total_passed} passed, {total_failed} failed")
print("=" * 50)

if total_failed > 0:
    sys.exit(1)
