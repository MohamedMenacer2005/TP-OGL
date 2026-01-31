#!/usr/bin/env python3
"""Debug why auditor doesn't detect issues"""

from src.agents.auditor_agent import AuditorAgent
from pathlib import Path

# Create test with obvious bugs
test_dir = Path("./test_audit_debug")
test_dir.mkdir(exist_ok=True)

test_code = '''def broken_func():
    undefined_var = some_undefined_function()
    return undefined_var
'''

test_file = test_dir / "broken.py"
test_file.write_text(test_code)

print("Test file created with undefined function reference")
print("\nRunning Auditor...\n")

auditor = AuditorAgent()
result = auditor.execute(target_dir=str(test_dir))

print(f"Status: {result.get('status')}")
print(f"Files audited: {result.get('file_results', {}).keys()}")

for fname, fdata in result.get('file_results', {}).items():
    issues = fdata.get('analysis', {}).get('issues', [])
    print(f"\n{fname}:")
    print(f"  Issues: {len(issues)}")
    if issues:
        for issue in issues:
            print(f"    - {issue}")
    else:
        print("  (no issues detected)")

# Cleanup
import shutil
shutil.rmtree(test_dir)
