"""Test Phase 2 toolsmith utilities."""

from src.utils.code_diff import CodeDiff
from src.utils.metrics import MetricsCalculator, MetricsComparison
from src.utils.import_extractor import ImportExtractor
from src.utils.result_aggregator import ResultAggregator, ResultBuilder

print("=" * 60)
print("🧪 Testing Phase 2 Toolsmith Utilities")
print("=" * 60)

# Test code samples
before_code = """
def calculate(x, y):
    result = x + y
    return result

def process(data):
    for item in data:
        print(item)
"""

after_code = """
def calculate(x: int, y: int) -> int:
    '''Calculate sum of two numbers.'''
    return x + y

def process(data: list) -> None:
    '''Process data items.'''
    for item in data:
        print(f"Processing: {item}")
"""

# Test 1: Code Diff
print("\n1️⃣ CodeDiff Tests")
print("-" * 40)

diff_stats = CodeDiff.compare_code(before_code, after_code)
print(f"✅ Additions: {diff_stats.additions}")
print(f"✅ Deletions: {diff_stats.deletions}")
print(f"✅ Similarity: {diff_stats.similarity_ratio:.1%}")

functions = CodeDiff.get_changed_functions(before_code, after_code)
print(f"✅ Function changes: {functions}")

# Test 2: Metrics Calculator
print("\n2️⃣ MetricsCalculator Tests")
print("-" * 40)

before_metrics = MetricsCalculator.calculate(before_code)
after_metrics = MetricsCalculator.calculate(after_code)

print(f"✅ Before: {before_metrics.lines_of_code} LOC, "
      f"complexity={before_metrics.cyclomatic_complexity}")
print(f"✅ After: {after_metrics.lines_of_code} LOC, "
      f"complexity={after_metrics.cyclomatic_complexity}")

comparison = MetricsComparison.compare(before_code, after_code)
print(f"✅ Improved: {comparison['changes']['improved']}")
print(f"✅ Maintainability change: {comparison['changes']['maintainability_change_percent']:.1f}%")

# Test 3: Import Extractor
print("\n3️⃣ ImportExtractor Tests")
print("-" * 40)

import_code = """
import os
import sys
from pathlib import Path
from typing import Dict, List
import pandas as pd
"""

imports = ImportExtractor.extract_imports(import_code)
print(f"✅ Absolute imports: {imports['absolute']}")
print(f"✅ From imports: {len(imports['from_imports'])}")
print(f"✅ All modules: {imports['all_modules']}")

categorized = ImportExtractor.categorize_imports(imports)
print(f"✅ Stdlib: {categorized['stdlib']}")
print(f"✅ Third-party: {categorized['third_party']}")

unused = ImportExtractor.find_unused_imports(import_code)
print(f"✅ Potentially unused: {unused}")

# Test 4: Result Aggregator
print("\n4️⃣ ResultAggregator Tests")
print("-" * 40)

aggregator = ResultAggregator()

# Create iteration using builder
result = (ResultBuilder(1)
          .with_target_file("example.py")
          .with_auditor({"issues": 3, "severity": "medium"})
          .with_fixer({"fixes_applied": 3, "lines_changed": 15})
          .with_judge({"score": 8.5}, decision="ACCEPT")
          .build())

aggregator.results.append(result)
print(f"✅ Created iteration 1 with decision: {result.judge_decision}")

# Create another iteration
result2 = (ResultBuilder(2)
           .with_target_file("utils.py")
           .with_auditor({"issues": 1, "severity": "low"})
           .with_fixer({"fixes_applied": 1, "lines_changed": 3})
           .with_judge({"score": 9.2}, decision="ACCEPT")
           .build())

aggregator.results.append(result2)

summary = aggregator.get_summary()
print(f"✅ Total iterations: {summary['total_iterations']}")
print(f"✅ Accepted: {summary['accepted']}")
print(f"✅ Total execution time: {summary['total_execution_time']}s")

print("\n" + "=" * 60)
print("✅ All Phase 2 toolsmith utilities working!")
print("=" * 60)
