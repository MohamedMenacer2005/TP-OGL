#!/usr/bin/env python3
"""Debug script to see what issues the auditor finds"""

from src.agents.auditor_agent import AuditorAgent

# Run auditor on sandbox
auditor = AuditorAgent()
audit_result = auditor.execute(target_dir="./sandbox")

print("=" * 80)
print("AUDIT RESULTS")
print("=" * 80)
print(f"Status: {audit_result.get('status', 'unknown')}")
print(f"\nFile Results:")

for filename, file_data in audit_result.get('file_results', {}).items():
    print(f"\n  {filename}:")
    analysis = file_data.get('analysis', {})
    issues = analysis.get('issues', [])
    print(f"    Issues count: {len(issues)}")
    for i, issue in enumerate(issues, 1):
        print(f"      {i}. {issue}")
