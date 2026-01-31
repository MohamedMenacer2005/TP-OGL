"""
ORCHESTRATION LAYER - The Refactoring Swarm
ENSI Technical Specification 2025-2026

Mandatory Entry Point: main.py
Orchestrates exactly THREE agents:
  1. AuditorAgent (runs ONCE at start)
  2. FixerAgent (iterative fixing)
  3. JudgeAgent (validation with self-healing loop)

Execution Graph:
  START → Auditor → Fixer → Judge → {
    if FAIL: Fixer → Judge (loop, max 10 iterations)
    if PASS: END
  }

STRICT CONSTRAINT: Only orchestration control flow implemented.
All agent interfaces are pre-existing and callable.
"""

import argparse
import sys
from pathlib import Path

# Data Officer integration
from src.data_officer import DataOfficer


def parse_arguments():
    """Parse --target_dir as per ENSI specification"""
    parser = argparse.ArgumentParser(
        description='The Refactoring Swarm - Multi-agent orchestration'
    )
    parser.add_argument(
        '--target_dir',
        type=str,
        required=True,
        help='Target directory containing Python code to refactor'
    )
    return parser.parse_args()


def validate_target_directory(target_dir: str) -> bool:
    """Validate target directory exists"""
    path = Path(target_dir)
    if not path.exists():
        print(f"ERROR: Target directory does not exist: {target_dir}", file=sys.stderr)
        return False
    if not path.is_dir():
        print(f"ERROR: Target path is not a directory: {target_dir}", file=sys.stderr)
        return False
    return True


def main():
    """
    Main orchestration loop - Controls execution of The Refactoring Swarm
    
    CRITICAL CONCEPT:
    ─────────────────
    Static analysis success (Auditor/pylint) does NOT imply runtime correctness.
    Only the JudgeAgent (pytest) can validate actual correctness.
    
    Therefore:
    - Auditor ALWAYS runs once to generate refactoring plan
    - Auditor's "no issues" DOES NOT skip test execution
    - Tests MUST ALWAYS be executed via JudgeAgent
    - Only JudgeAgent results determine success/failure
    
    Execution Flow (ENSI Spec):
    1. Parse and validate arguments
    2. Phase 1: Run Auditor ONCE (produces refactoring plan)
    3. Phase 2: Run Fixer (applies corrections based on audit)
    4. Phase 3: Run Judge (ACTUAL validation via pytest)
    5. Self-Healing Loop: If Judge fails, return to Fixer (max 10 iterations)
       - Auditor is NEVER called again in this loop
    6. Exit on Judge success or max iterations reached
    """
    try:
        # ===== DATA OFFICER: PRE-FLIGHT CHECK =====
        print("\n" + "="*70)
        print("DATA OFFICER: PRE-FLIGHT VALIDATION")
        print("="*70)
        
        officer = DataOfficer()
        is_valid, validation_msg = officer.verify_data_integrity()
        print(validation_msg)
        
        if not is_valid:
            print("\n⚠️  Warning: Data integrity issues detected (may be first run)")
        
        # ===== ARGUMENT PARSING =====
        args = parse_arguments()
        target_dir = args.target_dir
        
        if not validate_target_directory(target_dir):
            sys.exit(1)
        
        # Import agents (pre-existing, callable interfaces)
        from src.agents.auditor_agent import AuditorAgent
        from src.agents.corrector_agent import CorrectorAgent as FixerAgent
        from src.agents.judge_agent import JudgeAgent
        
        # ===== PHASE 1: AUDITOR (RUN ONCE ONLY) =====
        print("\n" + "="*70)
        print("PHASE 1: AUDITOR ANALYSIS")
        print("="*70)
        
        auditor = AuditorAgent()
        audit_result = auditor.execute(target_dir)
        
        print(f"[OK] Audit complete!")
        print(f"  Files audited: {audit_result.get('files_audited', 0)}")
        print(f"  Static issues found: {audit_result.get('total_issues', 0)}")
        
        print("\n[NOTE] Auditor provides REFACTORING PLAN only.")
        print("       Static analysis success does NOT guarantee runtime correctness.")
        print("       Proceeding to test execution via JudgeAgent...")
        
        # ===== ROLE BOUNDARY COMMENT =====
        # IMPORTANT: The orchestration layer ONLY controls the FLOW between agents.
        # The correctness of agent internals (including PytestRunner subprocess calls)
        # belongs to the Toolsmith and Agent implementation layers, NOT orchestration.
        # Orchestration does not compensate for tool layer issues.
        # Reference: src/agents/judge_agent.py and src/utils/pytest_runner.py
        # ================================
        
        # ===== PHASE 2-3: FIXER <-> JUDGE LOOP =====
        # CRITICAL: Always execute tests, even if Auditor found no static issues
        fixer = FixerAgent()
        judge = JudgeAgent()
        
        max_iterations = 10
        iteration = 0
        judge_result = None
        
        while iteration < max_iterations:
            iteration += 1
            print("\n" + "="*70)
            print(f"ITERATION {iteration}/{max_iterations}")
            print("="*70)
            
            # ===== FIXER PHASE =====
            print(f"\n[FIXER] Applying corrections (iteration {iteration})...")
            fixer_input = audit_result if iteration == 1 else judge_result
            fixer_result = fixer.execute(target_dir, fixer_input)
            print(f"[OK] Fixer applied corrections")
            print(f"  Total corrections: {fixer_result.get('total_corrections', 0)}")
            
            # ===== JUDGE PHASE (ACTUAL VALIDATION) =====
            print(f"\n[JUDGE] Running tests (VALIDATION via pytest)...")
            judge_result = judge.execute(target_dir)
            
            passed = judge_result.get('passed', 0)
            failed = judge_result.get('failed', 0)
            print(f"[JUDGE RESULTS] {passed} passed, {failed} failed")
            
            # ===== JUDGE DECISION =====
            if judge_result.get('success', False) and failed == 0:
                # SUCCESS: All tests pass - runtime correctness validated
                print("\n" + "="*70)
                print("MISSION COMPLETE!")
                print("="*70)
                print(f"[OK] All tests passing after {iteration} iteration(s)")
                print(f"[OK] Runtime correctness VALIDATED by JudgeAgent")
                print(f"  Final status: SUCCESS")
                
                # ===== DATA OFFICER: POST-FLIGHT VALIDATION =====
                print(f"\n[DATA OFFICER] Verifying experiment telemetry...")
                officer_final = DataOfficer()
                officer_report = officer_final.generate_report()
                print(officer_report)
                
                sys.exit(0)
            
            # FAILURE: Tests still failing - continue loop or exit
            if iteration < max_iterations:
                print(f"\n[RETRY] Tests failed - retrying (iteration {iteration + 1}/{max_iterations})")
            else:
                print(f"\n[STOP] Max iterations ({max_iterations}) reached")
                break
        
        # ===== FINAL STATUS =====
        print("\n" + "="*70)
        print("MISSION FAILED")
        print("="*70)
        print(f"[FAIL] Runtime correctness NOT achieved after {max_iterations} iterations")
        if judge_result:
            print(f"  Failed tests: {judge_result.get('failed', 0)}")
            print(f"  Test errors: {judge_result.get('errors', 0)}")
        sys.exit(1)
    
    except KeyboardInterrupt:
        print("\nRefactoring interrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"FATAL ERROR: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()