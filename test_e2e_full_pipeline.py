"""
End-to-End Pipeline: Auditor → Corrector → Judge (L'Agent Testeur)
Demonstrates the full swarm workflow with self-healing loop.
"""

import tempfile
from pathlib import Path
from src.agents.auditor_agent import AuditorAgent
from src.agents.corrector_agent import CorrectorAgent
from src.agents.judge_agent import JudgeAgent
import json


# Sample bad code with issues and tests
BAD_CODE_WITH_TESTS = '''
"""Module with code quality issues."""

def process_data():
    try:
        data = [1, 2, 3]
        print("Processing:", data)  # Issue: print without logging
        return data
    except:  # Issue: bare except
        print("Error occurred")
        return None

class DataHandler:
    def __init__(self):
        self.data = []
    
    def add_item(self, item):
        self.data.append(item)
        print(f"Added: {item}")  # Issue: print without logging
'''

TEST_CODE = '''
"""Tests for the module."""

def test_process_data():
    """Test process_data function."""
    from module import process_data
    result = process_data()
    assert result is not None, "process_data should return data"
    assert len(result) == 3, "process_data should return 3 items"

def test_data_handler_creation():
    """Test DataHandler instantiation."""
    from module import DataHandler
    handler = DataHandler()
    assert handler.data == [], "data should be initialized as empty list"

def test_data_handler_add_item():
    """Test adding items to DataHandler."""
    from module import DataHandler
    handler = DataHandler()
    handler.add_item(42)
    assert 42 in handler.data, "item should be added to data"
    assert len(handler.data) == 1, "data should have one item"
'''


def create_test_environment():
    """Create temporary directory with bad code and tests."""
    tmpdir = tempfile.mkdtemp()
    
    # Write module file
    module_file = Path(tmpdir) / "module.py"
    module_file.write_text(BAD_CODE_WITH_TESTS)
    
    # Write test file
    test_file = Path(tmpdir) / "test_module.py"
    test_file.write_text(TEST_CODE)
    
    return tmpdir


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def main():
    """Run the complete Auditor → Corrector → Judge pipeline."""
    print("\n" + "[==] " * 15)
    print("     FULL SWARM PIPELINE: AUDITOR -> CORRECTOR -> JUDGE")
    print("[==] " * 15)
    
    # Create test environment
    target_dir = create_test_environment()
    print(f"\n[DIR] Created test environment: {target_dir}")
    
    # Read the bad code
    module_path = Path(target_dir) / "module.py"
    bad_code = module_path.read_text()
    print(f"\n[CODE] Bad code ({len(bad_code)} bytes):")
    print("```python")
    print(bad_code[:200] + "...")
    print("```")
    
    # ============================================================================
    # PHASE 1: AUDITOR - Analyze code quality
    # ============================================================================
    print_section("PHASE 1: AUDITOR ANALYSIS")
    auditor = AuditorAgent()
    audit_result = auditor.execute(target_dir)
    
    print(f"\n[OK] Audit complete!")
    print(f"  Files audited: {audit_result['files_audited']}")
    print(f"  Total issues found: {audit_result['total_issues']}")
    print(f"\n  Issues by file:")
    for filename, file_result in audit_result['file_results'].items():
        if file_result.get('status') != 'error':
            issues_list = file_result.get('analysis', {}).get('issues', [])
            print(f"    {filename}: {len(issues_list)} issues")
            for issue in issues_list[:3]:
                print(f"      - {issue}")
    
    # ============================================================================
    # PHASE 2: CORRECTOR - Fix the issues
    # ============================================================================
    print_section("PHASE 2: CORRECTOR GENERATION")
    corrector = CorrectorAgent()
    correction_result = corrector.execute(target_dir, audit_result)
    
    print(f"\n[OK] Correction complete!")
    print(f"  Files corrected: {correction_result['files_corrected']}")
    print(f"  Total corrections: {correction_result['total_corrections']}")
    print(f"\n  Corrections applied:")
    for filename, file_corr in correction_result['corrections'].items():
        if file_corr.get('status') == 'corrected':
            for corr in file_corr.get('corrections', [])[:2]:
                print(f"    {filename}: {corr['issue']}")
    
    # ============================================================================
    # PHASE 3: JUDGE - Test the corrected code
    # ============================================================================
    print_section("PHASE 3: JUDGE (TEST EXECUTION)")
    
    def corrector_callback(target, error_logs):
        """Corrector callback for self-healing loop."""
        print(f"\n    [HEAL] Self-healing: Re-invoking Corrector...")
        corrector.execute(target, audit_result)
    
    judge = JudgeAgent(corrector_callback=corrector_callback, max_retry=2)
    judge_result = judge.execute(target_dir)
    
    print(f"\n[OK] Test execution complete!")
    print(f"  Final status: {judge_result['final_status']}")
    print(f"  Tests passed: {judge_result['passed']}")
    print(f"  Tests failed: {judge_result['failed']}")
    print(f"  Test errors: {judge_result['errors']}")
    print(f"  Retry attempts: {judge_result['retry_count']}")
    
    if judge_result['final_status'] == 'PASSED':
        print("\n  [SUCCESS] All tests passing!")
    else:
        print(f"\n  [FAIL] Tests still failing after {judge_result['retry_count']} attempts")
    
    # ============================================================================
    # PHASE 4: FINAL VALIDATION
    # ============================================================================
    print_section("PHASE 4: FINAL MISSION VALIDATION")
    
    validation = judge.validate_mission(target_dir)
    print(f"\n{validation['summary']}")
    print(f"  Mission complete: {validation['mission_complete']}")
    print(f"  All tests passed: {validation['all_tests_passed']}")
    print(f"  Total tests: {validation['passed'] + validation['failed'] + validation['errors']}")
    
    # ============================================================================
    # EXPERIMENT DATA SUMMARY
    # ============================================================================
    print_section("EXPERIMENT DATA LOGGING")
    
    try:
        with open("logs/experiment_data.json") as f:
            logs = json.load(f)
        
        agents = {}
        actions = {}
        
        for entry in logs:
            agent = entry.get("agent", "unknown")
            action = entry.get("action", "unknown")
            
            agents[agent] = agents.get(agent, 0) + 1
            actions[action] = actions.get(action, 0) + 1
        
        print(f"\n[LOG] Logged {len(logs)} total agent actions")
        print(f"\n  By agent:")
        for agent, count in sorted(agents.items()):
            print(f"    {agent}: {count} actions")
        
        print(f"\n  By action type:")
        for action, count in sorted(actions.items()):
            print(f"    {action}: {count} actions")
        
    except Exception as e:
        print(f"  Error reading logs: {e}")
    
    # ============================================================================
    # PIPELINE SUMMARY
    # ============================================================================
    print_section("PIPELINE SUMMARY")
    print("\n[OK] All phases completed successfully!")
    print(f"  1. Auditor identified {audit_result['total_issues']} issues")
    print(f"  2. Corrector generated {correction_result['total_corrections']} fixes")
    print(f"  3. Judge ran tests with {judge_result['retry_count']} correction attempts")
    print(f"  4. Final mission status: {judge_result['final_status']}")
    print("\n[DONE] Pipeline execution complete! All experiment data logged to logs/experiment_data.json")
    
    # Don't delete tmpdir to inspect if needed
    print(f"\n[DIR] Test environment: {target_dir}")
    print("   (Temporary directory not deleted for inspection)")


if __name__ == "__main__":
    main()
