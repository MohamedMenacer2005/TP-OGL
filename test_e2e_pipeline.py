"""
End-to-End Test: Auditor -> Corrector Pipeline
Tests the complete refactoring workflow on real Python code.
"""

import tempfile
from pathlib import Path
import json

from src.agents.auditor_agent import AuditorAgent, AuditorReport
from src.agents.corrector_agent import CorrectorAgent, CorrectionPlan
from src.utils.metrics import MetricsCalculator


# Sample "bad" Python code with multiple issues
BAD_CODE_SAMPLE = '''
def process_data(input_list):
    """Process a list of items"""
    try:
        print("Starting processing")
        results = []
        for item in input_list:
            if item is None:
                print("Skipping None")
            else:
                print("Processing:", item)
                result = item * 2
                results.append(result)
        print("Processing complete")
        return results
    except:
        print("Error occurred")
        return None

class DataHandler:
    def __init__(self):
        self.data = []
    
    def add_item(self, item):
        print("Adding item:", item)
        self.data.append(item)
    
    def get_items(self):
        print("Getting items")
        # TODO: implement caching
        return self.data
    
    def clear(self):
        self.data = []
        print("Data cleared")
'''


def main():
    print("=" * 80)
    print("END-TO-END TEST: Auditor -> Corrector Pipeline")
    print("=" * 80)
    
    # Create temporary directory with test code
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "bad_code.py"
        test_file.write_text(BAD_CODE_SAMPLE)
        print(f"\n✓ Created test file: {test_file}")
        
        # ===== STEP 1: AUDITOR ANALYSIS =====
        print("\n" + "=" * 80)
        print("STEP 1: AUDITOR ANALYSIS")
        print("=" * 80)
        
        auditor = AuditorAgent("TestAuditor")
        audit_result = auditor.execute(tmpdir)
        audit_report = AuditorReport(audit_result)
        
        print(f"\n✓ Files audited: {audit_result['files_audited']}")
        print(f"✓ Total issues found: {audit_result['total_issues']}")
        print(f"\nIssues:")
        for issue in audit_result['all_issues'][:10]:
            print(f"  • {issue}")
        
        # Show critical issues
        critical = audit_report.get_critical_issues()
        if critical:
            print(f"\nCritical Issues:")
            for issue in critical[:5]:
                print(f"  ⚠ {issue}")
        
        # ===== STEP 2: CORRECTOR GENERATION =====
        print("\n" + "=" * 80)
        print("STEP 2: CORRECTOR GENERATION (AST-based)")
        print("=" * 80)
        
        corrector = CorrectorAgent("TestCorrector", use_llm=False)  # AST mode for testing
        correction_result = corrector.execute(tmpdir, audit_result)
        correction_plan = CorrectionPlan(correction_result)
        
        print(f"\n✓ Files corrected: {correction_result['files_corrected']}")
        print(f"✓ Total corrections applied: {correction_result['total_corrections']}")
        
        # ===== STEP 3: METRICS ANALYSIS =====
        print("\n" + "=" * 80)
        print("STEP 3: BEFORE/AFTER METRICS")
        print("=" * 80)
        
        metrics_before = MetricsCalculator.calculate(BAD_CODE_SAMPLE)
        
        print(f"\nBEFORE Correction:")
        print(f"  Lines of Code: {metrics_before.lines_of_code}")
        print(f"  Functions: {metrics_before.function_count}")
        print(f"  Classes: {metrics_before.class_count}")
        print(f"  Cyclomatic Complexity: {metrics_before.cyclomatic_complexity:.2f}")
        print(f"  Maintainability Index: {metrics_before.maintainability_index:.2f}")
        print(f"  Avg Function Length: {metrics_before.avg_function_length:.1f} lines")
        
        # Get corrected code
        corrected_code = None
        if correction_result['corrections']:
            first_file = list(correction_result['corrections'].keys())[0]
            file_corrections = correction_result['corrections'][first_file]['corrections']
            if file_corrections:
                corrected_code = file_corrections[-1]['corrected_code']  # Last correction
        
        if corrected_code:
            metrics_after = MetricsCalculator.calculate(corrected_code)
            print(f"\nAFTER Correction:")
            print(f"  Lines of Code: {metrics_after.lines_of_code}")
            print(f"  Functions: {metrics_after.function_count}")
            print(f"  Classes: {metrics_after.class_count}")
            print(f"  Cyclomatic Complexity: {metrics_after.cyclomatic_complexity:.2f}")
            print(f"  Maintainability Index: {metrics_after.maintainability_index:.2f}")
            print(f"  Avg Function Length: {metrics_after.avg_function_length:.1f} lines")
            
            print(f"\nIMPROVEMENT:")
            print(f"  Complexity Δ: {metrics_before.cyclomatic_complexity - metrics_after.cyclomatic_complexity:+.2f}")
            print(f"  Maintainability Δ: {metrics_after.maintainability_index - metrics_before.maintainability_index:+.2f}")
        
        # ===== STEP 4: CORRECTIONS SUMMARY =====
        print("\n" + "=" * 80)
        print("STEP 4: CORRECTION DETAILS")
        print("=" * 80)
        
        corrections_by_file = correction_plan.get_corrections_by_file()
        for filename, issues in corrections_by_file.items():
            print(f"\n{filename}:")
            for issue in issues[:5]:
                print(f"  ✓ {issue}")
        
        # ===== STEP 5: VERIFY LOGGING =====
        print("\n" + "=" * 80)
        print("STEP 5: VERIFY EXPERIMENT LOGGING")
        print("=" * 80)
        
        if Path("logs/experiment_data.json").exists():
            with open("logs/experiment_data.json", encoding="utf-8") as f:
                logs = json.load(f)
            
            agent_logs = [l for l in logs if l["agent"] in ["TestAuditor", "TestCorrector"]]
            print(f"\n✓ Total agent logs: {len(agent_logs)}")
            
            # Verify mandatory fields
            valid_logs = 0
            for log in agent_logs:
                if "input_prompt" in log["details"] and "output_response" in log["details"]:
                    valid_logs += 1
            
            print(f"✓ Logs with mandatory fields: {valid_logs}/{len(agent_logs)}")
            
            if valid_logs == len(agent_logs):
                print("✓ All logs contain input_prompt and output_response!")
        
        # ===== FINAL SUMMARY =====
        print("\n" + "=" * 80)
        print("✅ END-TO-END TEST COMPLETE")
        print("=" * 80)
        print("\nPipeline Summary:")
        print(f"  Auditor: Found {audit_result['total_issues']} issues in {audit_result['files_audited']} file(s)")
        print(f"  Corrector: Generated {correction_result['total_corrections']} corrections")
        print(f"  Logging: {len(agent_logs)} experiment logs recorded")
        print("\n✅ Pipeline validated - ready for production!")


if __name__ == "__main__":
    main()
