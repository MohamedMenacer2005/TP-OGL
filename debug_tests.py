#!/usr/bin/env python3
"""Check actual test failures"""

from src.utils.pytest_runner import PytestRunner

runner = PytestRunner(target_dir="./sandbox")
results = runner.run_tests()

print("=" * 80)
print("TEST RESULTS")
print("=" * 80)
print(f"Passed: {results['passed']}")
print(f"Failed: {results['failed']}")
print(f"Errors: {results['errors']}")

print("\n\nTest Output:")
print(results.get('output', 'No output'))
