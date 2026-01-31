import json
from src.agents.auditor_agent import AuditorAgent

auditor = AuditorAgent()
result = auditor.execute("./sandbox")

for fname, data in result['file_results'].items():
    analysis = data.get('analysis', {})
    issues = analysis.get('issues', [])
    print(f"{fname}:")
    print(f"  Issues count: {len(issues)}")
    if issues:
        for issue in issues[:2]:
            print(f"    - {issue}")
