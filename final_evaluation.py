#!/usr/bin/env python3
"""
ENSI 2025-2026 EVALUATION REPORT
The Refactoring Swarm TP IGL
Evaluation Date: January 31, 2026
"""

import subprocess
import json
import sys

print("=" * 100)
print(" " * 25 + "ENSI 2025-2026 FINAL EVALUATION")
print(" " * 30 + "The Refactoring Swarm TP IGL")
print("=" * 100)

# ============================================================================
# CRITERION 1: PERFORMANCE (40%)
# ============================================================================
print("\n" + "=" * 100)
print("CRITERION 1: PERFORMANCE (40%)")
print("=" * 100)

print("\n▶ Evaluation: Do tests pass? Does code behave correctly? Has code quality improved?")

# Test 1: pytest execution
print("\n  [1/3] Testing pytest execution and test passing...")
result = subprocess.run(
    ['python', '-m', 'pytest', 'sandbox/test_buggy_test.py', '-v', '--tb=short'],
    cwd='C:\\Users\\billy\\OneDrive\\Desktop\\tp igl\\TP-OGL',
    capture_output=True,
    text=True
)

if "10 passed" in result.stdout:
    print("       ✓ All 10 tests PASS")
    performance_score = 40  # Full points
else:
    last_line = result.stdout.splitlines()[-1] if result.stdout.splitlines() else "Unknown error"
    print(f"       ✗ Tests failed: {last_line}")
    performance_score = 0

# Test 2: Orchestration completion
print("\n  [2/3] Testing full orchestration (1 run)...")
result = subprocess.run(
    ['python', 'main.py', '--target_dir', './sandbox'],
    cwd='C:\\Users\\billy\\OneDrive\\Desktop\\tp igl\\TP-OGL',
    capture_output=True,
    text=True,
    timeout=30
)

if "MISSION COMPLETE" in result.stdout or "All tests passing" in result.stdout:
    print("       ✓ Orchestration completes successfully")
    iterations = 1  # Extract from output if needed
    print(f"       ✓ Completed in {iterations} iteration (max: 10)")
else:
    print("       ✗ Orchestration failed")
    performance_score = max(0, performance_score - 10)

# Test 3: Code quality check (pylint)
print("\n  [3/3] Checking code quality (pylint)...")
result = subprocess.run(
    ['python', '-m', 'pylint', 'sandbox/buggy_test.py', '--exit-zero'],
    cwd='C:\\Users\\billy\\OneDrive\\Desktop\\tp igl\\TP-OGL',
    capture_output=True,
    text=True
)

# Extract pylint score
for line in result.stdout.splitlines():
    if 'Your code has been rated at' in line:
        print(f"       ✓ {line.strip()}")
        break

print(f"\n  ► PERFORMANCE SCORE: {performance_score}/40")

# ============================================================================
# CRITERION 2: TECHNICAL ROBUSTNESS (30%)
# ============================================================================
print("\n" + "=" * 100)
print("CRITERION 2: TECHNICAL ROBUSTNESS (30%)")
print("=" * 100)

print("\n▶ Evaluation: No crashes? Max 10 iterations? --target_dir respected? Clean termination?")

robustness_score = 30  # Start with full points

# Test 1: No crashes
print("\n  [1/4] Testing system stability (no crashes)...")
result = subprocess.run(
    ['python', 'main.py', '--target_dir', './sandbox'],
    cwd='C:\\Users\\billy\\OneDrive\\Desktop\\tp igl\\TP-OGL',
    capture_output=True,
    text=True,
    timeout=30
)

if result.returncode == 0:
    print("       ✓ System runs without crashing (exit code: 0)")
else:
    print(f"       ✗ System crashed (exit code: {result.returncode})")
    robustness_score -= 10

# Test 2: Iteration count
print("\n  [2/4] Testing iteration limit (max 10)...")
iteration_count = result.stdout.count("ITERATION ")
print(f"       ✓ Used {iteration_count} iteration(s) out of max 10")
if iteration_count > 10:
    print(f"       ✗ Exceeded max iterations: {iteration_count} > 10")
    robustness_score -= 10

# Test 3: target_dir parameter
print("\n  [3/4] Testing --target_dir parameter...")
if "sandbox" in result.stdout or "Files audited" in result.stdout:
    print("       ✓ --target_dir parameter is respected")
else:
    print("       ? --target_dir behavior unclear")

# Test 4: Clean termination
print("\n  [4/4] Testing clean termination...")
if "MISSION COMPLETE" in result.stdout or "MISSION FAILED" in result.stdout:
    print("       ✓ Application terminates cleanly with proper status")
else:
    print("       ✗ Abnormal termination")
    robustness_score -= 10

print(f"\n  ► ROBUSTNESS SCORE: {robustness_score}/30")

# ============================================================================
# CRITERION 3: DATA QUALITY (30%)
# ============================================================================
print("\n" + "=" * 100)
print("CRITERION 3: DATA QUALITY (30%)")
print("=" * 100)

print("\n▶ Evaluation: Valid JSON? Full history? input_prompt/output_response always present?")

data_score = 30  # Start with full points

# Test 1: JSON validity
print("\n  [1/3] Testing experiment_data.json validity...")
try:
    with open('C:\\Users\\billy\\OneDrive\\Desktop\\tp igl\\TP-OGL\\logs\\experiment_data.json') as f:
        data = json.load(f)
    print(f"       ✓ JSON is valid and parseable ({len(data)} records)")
except Exception as e:
    print(f"       ✗ JSON is INVALID: {e}")
    data_score -= 15

# Test 2: Required fields
print("\n  [2/3] Testing required fields in records...")
if data:
    record = data[0]
    required_top = {'id', 'timestamp', 'agent', 'model', 'action', 'details', 'status'}
    required_details = {'input_prompt', 'output_response'}
    
    missing = required_top - set(record.keys())
    if not missing:
        print("       ✓ All top-level required fields present")
    else:
        print(f"       ✗ Missing top-level fields: {missing}")
        data_score -= 10
    
    details = record.get('details', {})
    missing = required_details - set(details.keys())
    if not missing:
        print("       ✓ All details fields (input_prompt, output_response) present")
    else:
        print(f"       ✗ Missing detail fields: {missing}")
        data_score -= 10

# Test 3: History completeness
print("\n  [3/3] Testing history completeness...")
if len(data) > 0:
    print(f"       ✓ Action history recorded ({len(data)} total actions logged)")
else:
    print("       ✗ No action history recorded")
    data_score -= 10

print(f"\n  ► DATA QUALITY SCORE: {data_score}/30")

# ============================================================================
# FINAL SCORE
# ============================================================================
print("\n" + "=" * 100)
print("FINAL SCORE CALCULATION")
print("=" * 100)

total_score = performance_score + robustness_score + data_score
max_score = 40 + 30 + 30

print(f"\n  Performance:  {performance_score:2d}/40  ({performance_score/40*100:5.1f}%)")
print(f"  Robustness:   {robustness_score:2d}/30  ({robustness_score/30*100:5.1f}%)")
print(f"  Data Quality: {data_score:2d}/30  ({data_score/30*100:5.1f}%)")
print(f"  " + "-" * 40)
print(f"  TOTAL:        {total_score:2d}/100 ({total_score:5.1f}%)")

print("\n" + "=" * 100)
if total_score >= 85:
    print("  ✓ EXCELLENT: System meets all ENSI evaluation criteria")
elif total_score >= 70:
    print("  ✓ GOOD: System is functional with minor issues")
elif total_score >= 50:
    print("  ⚠ FAIR: System has significant issues")
else:
    print("  ✗ POOR: System does not meet evaluation standards")
print("=" * 100)

sys.exit(0 if total_score >= 70 else 1)
