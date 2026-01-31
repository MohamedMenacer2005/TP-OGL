from src.agents.corrector_agent import CorrectorAgent
from src.agents.auditor_agent import AuditorAgent

auditor = AuditorAgent()
audit_result = auditor.execute("./sandbox")

fixer = CorrectorAgent()
fixer_result = fixer.execute("./sandbox", audit_result)

print(f"Total corrections: {fixer_result['total_corrections']}")
print(f"Files corrected: {fixer_result['files_corrected']}")
print(f"Details: {fixer_result['details']}")
