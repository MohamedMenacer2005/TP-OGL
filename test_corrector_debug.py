#!/usr/bin/env python3
"""Debug corrector to see if it's actually fixing code."""

import tempfile
import logging
from pathlib import Path
from src.agents.corrector_agent import CorrectorAgent

# Enable logging to see what's happening
logging.basicConfig(level=logging.DEBUG, format='%(name)s: %(message)s')

# Create test
tmpdir = tempfile.mkdtemp(prefix='test_')
print(f'Created: {tmpdir}')

# Create buggy module
mod = Path(tmpdir) / 'calculator.py'
mod.write_text('''def add(a, b):
    return a - b

def multiply(a, b):
    return a + b
''')

print('Original code:')
print(mod.read_text())

# Create corrector
corrector = CorrectorAgent()

# Create audit report with specific issues
audit_report = {
    'all_issues': [
        'In function add(a, b): Currently returns -1 for add(2, 3) but should return 5. Change "return a - b" to "return a + b" (use + not -)',
        'In function multiply(a, b): Currently returns 5 for multiply(2, 3) but should return 6. Change "return a + b" to "return a * b" (use * not +)'
    ],
    'file_results': {
        'calculator.py': {
            'status': 'success',
            'error': None,
            'analysis': {
                'issues': [
                    'In function add(a, b): Currently returns -1 for add(2, 3) but should return 5. Change "return a - b" to "return a + b" (use + not -)',
                    'In function multiply(a, b): Currently returns 5 for multiply(2, 3) but should return 6. Change "return a + b" to "return a * b" (use * not +)'
                ]
            },
            'pylint': {
                'score': 0.0,
                'issue_count': 2,
                'messages': []
            }
        }
    }
}

# Run corrector
print('\nRunning corrector...')
result = corrector.execute(tmpdir, audit_report)
print(f'\nCorrection result status: {result.get("status")}')
print(f'Total corrections: {result.get("total_corrections")}')
print(f'Files corrected: {result.get("files_corrected")}')

# Check corrections in detail
for filename, file_result in result.get('corrections', {}).items():
    print(f'\n{filename}:')
    print(f'  Status: {file_result["status"]}')
    print(f'  Corrections count: {file_result["corrections_count"]}')
    for i, corr in enumerate(file_result['corrections']):
        print(f'  [{i}] Issue: {corr["issue"][:50]}...')
        print(f'      Status: {corr["status"]}')
        print(f'      Changed: {corr["change_summary"][:50]}...')

print('\n\nCorrected code:')
corrected = mod.read_text()
print(corrected)

# Check if fixes were applied
if 'a + b' in corrected and 'a * b' in corrected:
    print("\n✓ Corrections were applied!")
else:
    print("\n✗ Corrections were NOT applied")
    if 'a - b' in corrected:
        print("  - 'a - b' still present (add not fixed)")
    if 'a + b' in corrected and 'multiply' in corrected:
        print("  - multiply still has 'a + b' (not fixed to '*')")

# Clean up
import shutil
shutil.rmtree(tmpdir)

