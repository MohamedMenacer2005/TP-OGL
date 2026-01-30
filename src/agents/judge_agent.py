"""
Judge Agent (L'Agent Testeur)
Executes tests on corrected code and manages self-healing loops.
On test failure: returns code to Corrector with error details.
On test success: validates mission completion.
"""

import logging
from pathlib import Path
from typing import Dict, List, Callable, Optional
from src.agents.base_agent import BaseAgent
from src.utils.logger import ActionType
from src.utils.pytest_runner import PytestRunner


class JudgeAgent(BaseAgent):
    """
    Test execution and validation agent.
    Orchestrates the self-healing feedback loop between Corrector and test suite.
    """

    def __init__(
        self,
        agent_name: str = "JudgeAgent",
        model: str = "gemini-1.5-flash",
        corrector_callback: Optional[Callable] = None,
        max_retry: int = 3
    ):
        """
        Initialize Judge Agent.
        
        Args:
            agent_name: Unique identifier for this agent
            model: LLM model in use (for logging context)
            corrector_callback: Function to call on test failure to re-correct code.
                              Signature: corrector_callback(target_dir, error_logs) -> corrected_code
            max_retry: Maximum correction attempts before giving up (default: 3)
        """
        super().__init__(agent_name, model)
        self.corrector_callback = corrector_callback
        self.max_retry = max_retry
        self.pytest_runner = None

    def analyze(self, code: str, filename: str = "unknown.py") -> dict:
        """
        Analyze code by checking if it has associated tests.
        
        Args:
            code: Python code to analyze
            filename: Optional filename for context
            
        Returns:
            Dict with testability assessment
        """
        # Judge doesn't analyze code directly; it runs tests.
        # This method returns metadata about testability.
        has_test_imports = any(
            imp in code for imp in ["import unittest", "import pytest", "from pytest"]
        )
        
        return {
            "filename": filename,
            "testable": has_test_imports,
            "has_test_imports": has_test_imports,
            "code_length": len(code)
        }

    def execute(self, target_dir: str) -> dict:
        """
        Execute Judge Agent: run tests on target directory.
        
        Args:
            target_dir: Path to code directory
            
        Returns:
            Dict with test results and healing loop info:
                - success (bool): All tests passed
                - total_tests (int): Number of tests executed
                - passed (int): Number of tests passed
                - failed (int): Number of tests failed
                - errors (int): Number of test errors
                - test_messages (list): Test output
                - retry_count (int): Number of correction retries
                - final_status (str): "PASSED", "FAILED", or "MAX_RETRIES_EXCEEDED"
        """
        self.pytest_runner = PytestRunner(target_dir)
        
        # Initial test run
        test_result = self.pytest_runner.run_tests()
        retry_count = 0
        
        # Log initial test execution
        self._log_action(
            action=ActionType.DEBUG,
            prompt=f"Execute tests on {target_dir}",
            response=f"Test execution completed: {test_result['passed']} passed, "
                    f"{test_result['failed']} failed, {test_result['errors']} errors",
            extra_details={
                "target_dir": target_dir,
                "passed": test_result["passed"],
                "failed": test_result["failed"],
                "errors": test_result["errors"],
                "total_issues": test_result["failed"] + test_result["errors"]
            },
            status="SUCCESS" if test_result["success"] else "FAILURE"
        )
        
        # Self-healing loop: if tests fail and corrector available, retry
        while (not test_result["success"] and 
               retry_count < self.max_retry and 
               self.corrector_callback):
            
            retry_count += 1
            self.logger.warning(
                f"Tests failed (attempt {retry_count}/{self.max_retry}). "
                f"Triggering correction..."
            )
            
            # Invoke corrector with error logs
            error_logs = "\n".join(test_result.get("messages", []))
            
            try:
                # Call corrector callback to re-fix code
                self.corrector_callback(target_dir, error_logs)
                
                # Re-run tests
                test_result = self.pytest_runner.run_tests()
                
                # Log retry
                self._log_action(
                    action=ActionType.DEBUG,
                    prompt=f"Re-test after correction (attempt {retry_count})",
                    response=f"Test execution: {test_result['passed']} passed, "
                            f"{test_result['failed']} failed, {test_result['errors']} errors",
                    extra_details={
                        "retry_attempt": retry_count,
                        "passed": test_result["passed"],
                        "failed": test_result["failed"],
                        "errors": test_result["errors"],
                        "total_issues": test_result["failed"] + test_result["errors"]
                    },
                    status="SUCCESS" if test_result["success"] else "FAILURE"
                )
                
            except Exception as e:
                self.logger.error(f"Correction callback failed: {e}")
                self._log_action(
                    action=ActionType.DEBUG,
                    prompt=f"Invoke corrector (attempt {retry_count})",
                    response=f"Correction failed: {str(e)}",
                    extra_details={"error": str(e), "retry_attempt": retry_count},
                    status="FAILURE"
                )
                break
        
        # Determine final status
        if test_result["success"]:
            final_status = "PASSED"
            status_msg = "✓ All tests passed! Mission complete."
        elif retry_count >= self.max_retry:
            final_status = "MAX_RETRIES_EXCEEDED"
            status_msg = f"✗ Max retries ({self.max_retry}) exceeded. Code still has failures."
        else:
            final_status = "FAILED"
            status_msg = "✗ Tests failed and no corrector available for retry."
        
        # Log final mission status
        self._log_action(
            action=ActionType.DEBUG,
            prompt=f"Judge final validation",
            response=status_msg,
            extra_details={
                "final_status": final_status,
                "retry_count": retry_count,
                "passed": test_result["passed"],
                "failed": test_result["failed"],
                "errors": test_result["errors"]
            },
            status="SUCCESS" if final_status == "PASSED" else "FAILURE"
        )
        
        return {
            "success": final_status == "PASSED",
            "total_tests": test_result["passed"] + test_result["failed"] + test_result["errors"],
            "passed": test_result["passed"],
            "failed": test_result["failed"],
            "errors": test_result["errors"],
            "test_messages": test_result.get("messages", []),
            "retry_count": retry_count,
            "final_status": final_status
        }

    def run_single_test_file(self, target_dir: str, test_file: str) -> dict:
        """
        Run tests from a specific test file.
        
        Args:
            target_dir: Path to code directory
            test_file: Relative path to test file
            
        Returns:
            Test results dict
        """
        runner = PytestRunner(target_dir)
        result = runner.run_tests(test_file=test_file)
        
        self._log_action(
            action=ActionType.DEBUG,
            prompt=f"Run single test file: {test_file}",
            response=f"Tests: {result['passed']} passed, {result['failed']} failed, "
                    f"{result['errors']} errors",
            extra_details={
                "test_file": test_file,
                "passed": result["passed"],
                "failed": result["failed"],
                "errors": result["errors"]
            },
            status="SUCCESS" if result["success"] else "FAILURE"
        )
        
        return result

    def validate_mission(self, target_dir: str) -> dict:
        """
        Final validation: all tests pass and mission is complete.
        
        Args:
            target_dir: Path to code directory
            
        Returns:
            Dict with validation result
        """
        runner = PytestRunner(target_dir)
        result = runner.run_tests()
        
        is_mission_complete = result["success"] and result["failed"] == 0
        
        self._log_action(
            action=ActionType.DEBUG,
            prompt=f"Validate mission completion",
            response=f"Mission status: {'COMPLETE' if is_mission_complete else 'INCOMPLETE'}",
            extra_details={
                "mission_complete": is_mission_complete,
                "all_tests_passed": result["success"],
                "failed_count": result["failed"],
                "error_count": result["errors"]
            },
            status="SUCCESS" if is_mission_complete else "FAILURE"
        )
        
        return {
            "mission_complete": is_mission_complete,
            "all_tests_passed": result["success"],
            "passed": result["passed"],
            "failed": result["failed"],
            "errors": result["errors"],
            "summary": "✓ Mission Complete!" if is_mission_complete else "✗ Tests still failing"
        }
