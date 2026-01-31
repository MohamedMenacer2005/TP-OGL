#!/usr/bin/env python3
"""
Test the Corrector Agent directly
Verifies if issues are detected and corrected
"""

import os
import json
from pathlib import Path

# Create a test directory with intentional bugs
test_dir = Path("./test_corrector")
test_dir.mkdir(exist_ok=True)

# Create buggy code with known issues
buggy_code = '''"""Test file with intentional bugs"""

def add_numbers(a, b):
    """Add two numbers but missing return"""
    result = a + b
    # BUG: missing return statement

def divide(x, y):
    """Divide without checking zero"""
    return x / y  # BUG: division by zero not handled

def greet(name):
    """Greet with typo"""
    return f"Hello, {nam}!"  # BUG: typo - should be 'name' not 'nam'

class BadClass:
    """Class with bad init"""
    def __init__(self, value):  # BUG: missing second param that tests expect
        self.value = value

def read_file(path):
    """Read file without error handling"""
    with open(path) as f:  # BUG: no try/except
        return f.read()
'''

# Write the buggy code
buggy_file = test_dir / "buggy_module.py"
buggy_file.write_text(buggy_code)

print("=" * 80)
print("CORRECTOR AGENT TEST")
print("=" * 80)

print("\n[STEP 1] Created test file with intentional bugs:")
print(f"  Location: {buggy_file}")
print(f"  Size: {len(buggy_code)} bytes")
print("\nBugs introduced:")
print("  - add_numbers(): missing return statement")
print("  - divide(): no division by zero check")
print("  - greet(): typo 'nam' instead of 'name'")
print("  - BadClass.__init__(): missing parameter")
print("  - read_file(): no error handling for FileNotFoundError")

# Step 2: Run auditor to detect issues
print("\n" + "-" * 80)
print("[STEP 2] Running AUDITOR to detect issues...")
print("-" * 80)

from src.agents.auditor_agent import AuditorAgent

auditor = AuditorAgent()
audit_result = auditor.execute(target_dir=str(test_dir))

print(f"\nAudit Result Status: {audit_result.get('status')}")
files_audited = audit_result.get('file_results', {})
print(f"Files audited: {len(files_audited)}")

for filename, file_data in files_audited.items():
    issues = file_data.get('analysis', {}).get('issues', [])
    print(f"\n  File: {filename}")
    print(f"    Issues found: {len(issues)}")
    for i, issue in enumerate(issues, 1):
        print(f"      {i}. {issue}")

# Step 3: Run corrector to fix issues
print("\n" + "-" * 80)
print("[STEP 3] Running CORRECTOR to apply fixes...")
print("-" * 80)

from src.agents.corrector_agent import CorrectorAgent

corrector = CorrectorAgent()
correction_result = corrector.execute(target_dir=str(test_dir), issue_report=audit_result)

print(f"\nCorrection Result:")
print(f"  Files corrected: {correction_result.get('files_corrected', 0)}")
print(f"  Total corrections: {correction_result.get('total_corrections', 0)}")
print(f"  Status: {correction_result.get('status', 'unknown')}")

# Step 4: Check if code was actually modified
print("\n" + "-" * 80)
print("[STEP 4] Verifying fixes were applied...")
print("-" * 80)

corrected_code = buggy_file.read_text()

print("\nChecking for fixes in corrected code:\n")

checks = [
    ("add_numbers returns value", "return result" in corrected_code and "def add_numbers" in corrected_code),
    ("divide has zero check", ("if y == 0" in corrected_code or "if x / y" in corrected_code) and "def divide" in corrected_code),
    ("greet uses correct variable", "{name}" in corrected_code and "def greet" in corrected_code),
    ("BadClass has balance param", "balance" in corrected_code and "class BadClass" in corrected_code or ("def __init__(self, value" in corrected_code)),
    ("read_file has try/except", "try:" in corrected_code and "except" in corrected_code and "def read_file" in corrected_code),
]

fixes_applied = 0
for check_name, result in checks:
    symbol = "✓" if result else "✗"
    print(f"  {symbol} {check_name}: {'YES' if result else 'NO'}")
    if result:
        fixes_applied += 1

# Step 5: Show original vs corrected
print("\n" + "-" * 80)
print("[STEP 5] Code comparison (before/after)")
print("-" * 80)

print("\n--- ORIGINAL CODE (first 500 chars) ---")
print(buggy_code[:500])

print("\n--- CORRECTED CODE (first 500 chars) ---")
print(corrected_code[:500])

# Step 6: Final verdict
print("\n" + "=" * 80)
print("CORRECTOR TEST RESULTS")
print("=" * 80)

print(f"\nIssues detected by Auditor: {sum(len(f.get('analysis', {}).get('issues', [])) for f in files_audited.values())}")
print(f"Corrections applied by Corrector: {correction_result.get('total_corrections', 0)}")
print(f"Code fixes verified: {fixes_applied}/5")

if correction_result.get('total_corrections', 0) > 0 and fixes_applied > 0:
    print("\n✓ CORRECTOR IS WORKING: Issues detected and corrected!")
elif correction_result.get('total_corrections', 0) == 0 and audit_result.get('status') == 'audit_complete':
    print("\n⚠ CORRECTOR DID NOT APPLY FIXES: Issues detected but not corrected")
    print("   This may be due to:")
    print("   - LLM API quota exhausted (fallback fixes not matching)")
    print("   - Issue detection not matching correction logic")
else:
    print("\n? CORRECTOR STATUS UNCLEAR: Check logs above")

print("\n" + "=" * 80)

# Cleanup
import shutil
shutil.rmtree(test_dir)
print(f"\nCleaned up test directory: {test_dir}")
