"""
End-to-End Test: Full Agent Pipeline (Auditor → Corrector → Judge)
Tests the complete workflow: analyze code → fix issues → validate results
"""

import os
import sys
import json
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

from src.agents.auditor_agent import AuditorAgent
from src.agents.corrector_agent import CorrectorAgent
from src.agents.judge_agent import JudgeAgent
from src.utils.logger import log_experiment, ActionType


def create_buggy_code():
    """Create a temporary directory with buggy code and tests."""
    tmpdir = tempfile.mkdtemp(prefix="e2e_test_")
    
    # Create buggy module
    buggy_module = Path(tmpdir) / "calculator.py"
    buggy_module.write_text("""
def add(a, b):
    '''Add two numbers - BUGGY VERSION'''
    return a - b  # BUG: should be a + b

def multiply(a, b):
    '''Multiply two numbers - BUGGY VERSION'''
    return a + b  # BUG: should be a * b

def divide(a, b):
    '''Divide two numbers - BUGGY VERSION'''
    if b == 0:
        return "Error"  # BUG: should raise ValueError
    return a / b

if __name__ == "__main__":
    print(f"5 + 3 = {add(5, 3)}")
    print(f"5 * 3 = {multiply(5, 3)}")
    print(f"10 / 2 = {divide(10, 2)}")
""")
    
    # Create tests that will fail
    test_file = Path(tmpdir) / "test_calculator.py"
    test_file.write_text("""
import pytest
from calculator import add, multiply, divide

def test_add():
    '''Test addition'''
    assert add(2, 3) == 5, "add(2, 3) should be 5"
    assert add(-1, 1) == 0, "add(-1, 1) should be 0"
    assert add(0, 0) == 0, "add(0, 0) should be 0"

def test_multiply():
    '''Test multiplication'''
    assert multiply(2, 3) == 6, "multiply(2, 3) should be 6"
    assert multiply(-2, 3) == -6, "multiply(-2, 3) should be -6"
    assert multiply(5, 0) == 0, "multiply(5, 0) should be 0"

def test_divide():
    '''Test division'''
    assert divide(10, 2) == 5, "divide(10, 2) should be 5"
    assert divide(9, 3) == 3, "divide(9, 3) should be 3"
    
    with pytest.raises(ValueError):
        divide(10, 0)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
""")
    
    return tmpdir


def print_section(title):
    """Print formatted section header."""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)


def run_e2e_test():
    """Run complete E2E test pipeline."""
    
    print_section("END-TO-END TEST: Agent Pipeline")
    print("Testing: Auditor → Corrector → Judge workflow")
    
    # Step 1: Create buggy code
    print_section("Step 1: Create Buggy Code")
    target_dir = create_buggy_code()
    print(f"✓ Created test code in: {target_dir}")
    
    # Step 2: Initialize agents
    print_section("Step 2: Initialize Agents")
    auditor = AuditorAgent()
    corrector = CorrectorAgent()
    
    # Define corrector callback for judge's self-healing loop
    def corrector_callback(target_dir, error_logs):
        """Corrector callback for self-healing."""
        return corrector.execute(target_dir, audit_result)
    
    judge = JudgeAgent(corrector_callback=corrector_callback, max_retry=3)
    print("✓ Auditor initialized")
    print("✓ Corrector initialized")
    print("✓ Judge initialized with corrector callback")
    
    # Step 3: Run Auditor (analyze code)
    print_section("Step 3: Auditor - Analyze Code")
    try:
        audit_result = auditor.execute(target_dir)
        print(f"✓ Audit completed")
        print(f"  - Total issues found: {audit_result.get('total_issues', 0)}")
        print(f"  - Files analyzed: {len(audit_result.get('file_results', []))}")
        
        all_issues = audit_result.get('all_issues', [])
        print(f"  - Issues across codebase: {len(all_issues)}")
        
        if all_issues:
            print(f"\n  Top issues:")
            for issue in all_issues[:3]:
                print(f"    • {issue}")
    except Exception as e:
        print(f"✗ Auditor failed: {e}")
        return False
    
    # Step 4: Run Corrector (fix issues)
    print_section("Step 4: Corrector - Fix Issues")
    try:
        correction_result = corrector.execute(target_dir, audit_result)
        print(f"✓ Correction completed")
        print(f"  - Status: {correction_result.get('status', 'N/A')}")
        
        corrections = correction_result.get('corrections', {})
        total_corrections = sum(len(c.get('corrections', [])) for c in corrections.values())
        print(f"  - Total corrections: {total_corrections}")
        
        if corrections:
            print(f"\n  Files corrected:")
            for filename, file_corr in list(corrections.items())[:3]:
                status = file_corr.get('status', 'N/A')
                corr_count = len(file_corr.get('corrections', []))
                print(f"    • {filename}: {status} ({corr_count} corrections)")
    except Exception as e:
        print(f"✗ Corrector failed: {e}")
        return False
    
    # Step 5: Run Judge (validate corrected code)
    print_section("Step 5: Judge - Validate & Test")
    try:
        judge_result = judge.execute(target_dir)
        print(f"✓ Judge validation completed")
        print(f"  - Tests passed: {judge_result.get('success', False)}")
        print(f"  - Final status: {judge_result.get('final_status', 'N/A')}")
        print(f"  - Passed: {judge_result.get('passed', 0)}")
        print(f"  - Failed: {judge_result.get('failed', 0)}")
        print(f"  - Errors: {judge_result.get('errors', 0)}")
        print(f"  - Retry count: {judge_result.get('retry_count', 0)}")
        
        if judge_result.get('test_messages'):
            print(f"\n  Test output:")
            for msg in judge_result['test_messages'][:3]:
                print(f"    • {msg}")
    except Exception as e:
        print(f"✗ Judge failed: {e}")
        return False
    
    # Step 6: Verify experiment logs
    print_section("Step 6: Verify Experiment Logs")
    try:
        logs_file = Path("logs/experiment_data.json")
        if logs_file.exists():
            with open(logs_file) as f:
                logs = json.load(f)
            print(f"✓ Experiment logs found")
            print(f"  - Total log entries: {len(logs)}")
            
            # Count by agent
            agent_counts = {}
            for entry in logs:
                agent = entry.get('agent', 'Unknown')
                agent_counts[agent] = agent_counts.get(agent, 0) + 1
            
            print(f"\n  Logs by agent:")
            for agent, count in agent_counts.items():
                print(f"    • {agent}: {count} entries")
        else:
            print(f"⚠ No experiment logs found")
    except Exception as e:
        print(f"⚠ Could not read logs: {e}")
    
    # Summary
    print_section("E2E Test Summary")
    if judge_result.get('success'):
        print("✅ E2E TEST PASSED: All stages completed successfully!")
        print("\nPipeline workflow:")
        print("  1. Auditor found and reported issues ✓")
        print("  2. Corrector fixed the code ✓")
        print("  3. Judge validated all tests pass ✓")
        success = True
    else:
        print("⚠ E2E TEST PARTIAL: Pipeline ran but tests still failing")
        print(f"  Final status: {judge_result.get('final_status')}")
        print(f"  Remaining issues: {judge_result.get('failed', 0)} failed, {judge_result.get('errors', 0)} errors")
        success = False
    
    # Cleanup
    print_section("Cleanup")
    import shutil
    shutil.rmtree(target_dir, ignore_errors=True)
    print(f"✓ Cleaned up test directory")
    
    return success


if __name__ == "__main__":
    try:
        success = run_e2e_test()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
