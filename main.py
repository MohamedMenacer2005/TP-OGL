"""
FEATURE 3: main.py - Mandatory Entry Point
Implements the official entry point for automated evaluation.

Usage:
    python main.py --target_dir "./sandbox/dataset_inconnu"

Requirements (from official documents):
- Parse --target_dir argument
- Validate directory existence
- Launch orchestration
- Exit cleanly
"""

import argparse
import sys
from pathlib import Path


def parse_arguments():
    """Parse command-line arguments as specified in official documents"""
    parser = argparse.ArgumentParser(
        description='The Refactoring Swarm - Multi-agent code refactoring system'
    )
    
    parser.add_argument(
        '--target_dir',
        type=str,
        required=True,
        help='Target directory containing Python code to refactor'
    )
    
    return parser.parse_args()


def validate_target_directory(target_dir: str) -> bool:
    """Validate that target directory exists"""
    path = Path(target_dir)
    
    if not path.exists():
        print(f"ERROR: Target directory does not exist: {target_dir}", file=sys.stderr)
        return False
    
    if not path.is_dir():
        print(f"ERROR: Target path is not a directory: {target_dir}", file=sys.stderr)
        return False
    
    return True


def main():
    """Main entry point for The Refactoring Swarm"""
    try:
        # Parse arguments
        args = parse_arguments()
        target_dir = args.target_dir
        
        # Validate directory
        if not validate_target_directory(target_dir):
            sys.exit(1)
        
        # Import agents
        from src.agents.auditor_agent import AuditorAgent
        from src.agents.corrector_agent import CorrectorAgent
        from src.agents.pylint_optimizer_agent import PylintOptimizerAgent
        from src.agents.judge_agent import JudgeAgent
        
        print("\n" + "="*70)
        print("PHASE 1: AUDITOR ANALYSIS")
        print("="*70)
        
        # Phase 1: Audit code
        auditor = AuditorAgent()
        audit_result = auditor.execute(target_dir)
        
        print(f"\n[OK] Audit complete!")
        print(f"  Files audited: {audit_result['files_audited']}")
        print(f"  Total issues found: {audit_result['total_issues']}")
        
        # Display pylint scores by file
        file_results = audit_result.get('file_results', {})
        if file_results:
            print(f"\n  Issues by file:")
            for filename, file_data in file_results.items():
                if file_data.get("status") == "success":
                    issues_count = file_data.get("analysis", {}).get("issue_count", 0)
                    pylint_score = file_data.get("pylint", {}).get("score", 0.0)
                    print(f"    {filename}: {issues_count} issues (pylint: {pylint_score:.2f}/10)")
                    
                    # Show specific issues
                    issues = file_data.get("analysis", {}).get("issues", [])
                    for issue in issues:
                        print(f"      - {issue}")
        
        if audit_result['total_issues'] == 0:
            print("\n[OK] No issues found - code is clean!")
            sys.exit(0)
        
        print("\n" + "="*70)
        print("PHASE 2: CORRECTOR GENERATION")
        print("="*70)
        
        # Phase 2: Generate corrections
        corrector = CorrectorAgent()
        correction_result = corrector.execute(target_dir, audit_result)
        
        print(f"\n[OK] Correction complete!")
        print(f"  Files corrected: {correction_result['files_corrected']}")
        print(f"  Total corrections: {correction_result['total_corrections']}")
        
        print("\n" + "="*70)
        print("PHASE 3: PYLINT OPTIMIZATION")
        print("="*70)
        
        # Phase 3: Optimize for pylint scores
        optimizer = PylintOptimizerAgent()
        optimization_result = optimizer.execute(target_dir, correction_result, audit_result)
        
        print(f"\n[OK] Optimization complete!")
        print(f"  Files optimized: {optimization_result['files_optimized']}")
        print(f"  Total optimizations: {optimization_result['total_optimizations']}")
        print(f"  Total score improvement: +{optimization_result['total_score_improvement']:.2f}")
        
        print("\n" + "="*70)
        print("PHASE 4: JUDGE (TEST EXECUTION)")
        print("="*70)
        
        # Phase 4: Run tests with self-healing loop
        judge = JudgeAgent()
        max_judge_retries = 3
        retry_count = 0
        judge_result = judge.execute(target_dir)
        
        # Track progress to avoid infinite loops
        previous_failed_count = judge_result['failed']
        
        # Self-healing loop: retry with corrector if tests fail
        while (judge_result['failed'] > 0 or judge_result['errors'] > 0) and retry_count < max_judge_retries:
            retry_count += 1
            print(f"\n[RETRY {retry_count}/{max_judge_retries}] Tests failed - triggering correction...")
            
            # Use Judge's create_correction_report method
            failure_report = judge.create_correction_report(judge_result, target_dir)
            
            # Validate report has actionable issues
            if not failure_report.get('file_results'):
                print("  [WARNING] No actionable failures detected - stopping retry loop")
                break
            
            # Display what will be fixed
            print(f"\n  CORRECTOR WILL FIX:")
            for filename, file_data in failure_report['file_results'].items():
                issues = file_data['analysis']['issues']
                print(f"    {filename}: {len(issues)} issue(s)")
                for issue in issues[:3]:  # Show first 3
                    print(f"       - {issue}")
            
            # Call Corrector with structured report
            correction_result = corrector.execute(target_dir, failure_report)
            
            # Check if corrections were actually applied
            if correction_result['total_corrections'] == 0:
                print("  [WARNING] Corrector made no changes - stopping retry loop")
                break
            
            print(f"  [OK] Corrector applied {correction_result['total_corrections']} corrections")
            
            # Re-run tests
            judge_result = judge.execute(target_dir)
            
            # Check for progress
            current_failed_count = judge_result['failed']
            if current_failed_count >= previous_failed_count:
                print(f"  [WARNING] No progress: {previous_failed_count} -> {current_failed_count} failures")
                if retry_count >= 2:  # Allow one retry without progress
                    print("  [WARNING] Stopping retry loop - no improvement detected")
                    break
            
            previous_failed_count = current_failed_count
            print(f"  Test results: {judge_result['passed']} passed, {judge_result['failed']} failed")
        
        print(f"\n[OK] Test execution complete!")
        print(f"  Final status: {'PASSED' if judge_result['success'] else 'FAILED'}")
        print(f"  Tests passed: {judge_result['passed']}")
        print(f"  Tests failed: {judge_result['failed']}")
        
        print("\n" + "="*70)
        print("FINAL MISSION VALIDATION")
        print("="*70)
        
        if judge_result['success'] and judge_result['failed'] == 0 and judge_result['errors'] == 0:
            print("\n[OK] Mission Complete!")
            print("  All refactoring phases succeeded")
            print(f"  All {judge_result['total_tests']} tests are passing")
            sys.exit(0)
        else:
            print("\n[FAIL] Mission Failed!")
            if judge_result['failed'] > 0 or judge_result['errors'] > 0:
                print(f"  Tests failed: {judge_result['failed']}, Errors: {judge_result['errors']}")
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