#!/usr/bin/env python
"""Quick test of pylint runner"""

from src.utils.pylint_runner import PylintRunner

runner = PylintRunner('./sandbox')
result = runner.run_pylint('buggy_test.py')

print(f"Score: {result['score']}")
print(f"Messages: {result['messages']}")
print(f"Success: {result['success']}")
print(f"Raw output: {result['raw_output']}")


