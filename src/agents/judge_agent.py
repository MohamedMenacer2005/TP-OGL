"""
Judge Agent (L'Agent Testeur)
Executes tests on corrected code.
Returns test results for evaluation.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional
from src.agents.base_agent import BaseAgent
from src.utils.logger import ActionType
from src.utils.pytest_runner import PytestRunner


class JudgeAgent(BaseAgent):
    """
    Test execution and validation agent.
    Runs tests and reports results. Self-healing loop is managed by orchestrator (main.py).
    """

    def __init__(
        self,
        agent_name: str = "JudgeAgent",
        model: str = "models/gemini-2.0-flash"
    ):
        """
        Initialize Judge Agent.
        
        Args:
            agent_name: Unique identifier for this agent
            model: LLM model in use (for logging context)
        """
        super().__init__(agent_name, model)
        self.pytest_runner = None

    def _analyze_test_failures(self, test_result: dict) -> str:
        """
        Analyze test failures and generate specific correction instructions.
        
        Args:
            test_result: Pytest execution result with failures
            
        Returns:
            Actionable correction instructions formatted for Corrector
        """
        import re
        
        messages = test_result.get("messages", [])
        full_output = "\n".join(messages)
        
        instructions = []
        instructions.append("=== SPECIFIC TEST FAILURES TO FIX ===\n")
        
        # Parse pytest failure patterns
        # Pattern: FAILED test_file.py::TestClass::test_method - AssertionError
        failure_pattern = r"FAILED\s+([\w/\\\.]+\.py)::([\w:]+)\s*-?\s*(.*)"
        
        for match in re.finditer(failure_pattern, full_output):
            test_file = match.group(1)
            test_name = match.group(2)
            error_hint = match.group(3).strip() if match.group(3) else ""
            
            # Extract assertion details from output
            assertion_context = self._extract_assertion_context(full_output, test_name)
            
            instructions.append(f"\n[FAILURE {len(instructions)}]")
            instructions.append(f"Test: {test_name}")
            instructions.append(f"File: {test_file}")
            if assertion_context:
                instructions.append(f"Issue: {assertion_context}")
            elif error_hint:
                instructions.append(f"Error: {error_hint}")
            instructions.append("Action: Fix the code that this test is checking")
            instructions.append("-" * 60)
        
        # Add specific guidance based on common failure patterns
        if "AssertionError" in full_output:
            instructions.append("\n[HINT] AssertionErrors indicate logic bugs:")
            instructions.append("- Check arithmetic operators (+, -, *, /)")
            instructions.append("- Verify return values match expected results")
            instructions.append("- Look for off-by-one errors")
        
        if "AttributeError" in full_output or "NameError" in full_output:
            instructions.append("\n[HINT] Name/Attribute errors indicate:")
            instructions.append("- Typos in variable/function names")
            instructions.append("- Missing imports")
            instructions.append("- Undefined variables")
        
        instructions.append(f"\n=== END OF {len(instructions)-2} FAILURES ===")
        
        return "\n".join(instructions)
    
    def _extract_assertion_context(self, output: str, test_name: str) -> str:
        """
        Extract assertion failure context for a specific test.
        
        Args:
            output: Full pytest output
            test_name: Name of failed test
            
        Returns:
            Human-readable description of what failed
        """
        import re
        
        # Find the section for this test
        test_section_pattern = rf"{test_name}.*?(?:FAILED|PASSED|={10,})"
        match = re.search(test_section_pattern, output, re.DOTALL)
        
        if not match:
            return ""
        
        section = match.group(0)
        
        # Extract assertion details
        # Pattern: "assert X == Y" where X != Y
        assert_pattern = r"assert\s+(.+?)\s*(==|!=|>|<|>=|<=)\s*(.+?)$"
        assert_match = re.search(assert_pattern, section, re.MULTILINE)
        
        if assert_match:
            left = assert_match.group(1).strip()
            operator = assert_match.group(2)
            right = assert_match.group(3).strip()
            return f"Expected {left} {operator} {right} but assertion failed"
        
        # Pattern: "AssertionError: message"
        error_msg_pattern = r"AssertionError:\s*(.+?)(?:\n|$)"
        error_match = re.search(error_msg_pattern, section)
        
        if error_match:
            return error_match.group(1).strip()
        
        return "Assertion failed (see test output for details)"

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
            Dict with test results:
                - success (bool): All tests passed
                - total_tests (int): Number of tests executed
                - passed (int): Number of tests passed
                - failed (int): Number of tests failed
                - errors (int): Number of test errors
                - messages (list): Test output
        """
        self.pytest_runner = PytestRunner(target_dir)
        
        # Run tests
        test_result = self.pytest_runner.run_tests()
        
        # Log test execution
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
        
        return test_result

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

    def _map_test_to_source_file(self, test_file_path: str) -> str:
        """
        Map a test file path to its corresponding source file.
        
        Examples:
            "tests/test_calculator.py" → "calculator.py"
            "test_utils.py" → "utils.py"
            "test_validator.py" → "validator.py"
        
        Args:
            test_file_path: Path to test file (e.g., "tests/test_calculator.py")
            
        Returns:
            Source file name (e.g., "calculator.py")
        """
        from pathlib import Path
        
        # Extract filename without path
        test_filename = Path(test_file_path).name  # "test_calculator.py"
        
        # Remove "test_" prefix
        if test_filename.startswith("test_"):
            source_filename = test_filename[5:]  # "calculator.py"
        else:
            source_filename = test_filename
        
        return source_filename

    def create_correction_report(self, test_result: dict, target_dir: str) -> dict:
        """
        Analyze test failures and create a Corrector-compatible report.
        Maps test files to their corresponding source files.
        
        Args:
            test_result: Dict from execute() with test results
            target_dir: Path to source code directory
            
        Returns:
            Dict with structure:
            {
                "file_results": {
                    "calculator.py": {  # Source file, not test file
                        "analysis": {
                            "issues": [
                                "Test test_add expects 5 but got -1",
                                "Function add() has wrong operator"
                            ],
                            "issue_count": 2
                        },
                        "status": "error"
                    }
                },
                "all_issues": ["Test test_add expects 5 but got -1", ...],
                "total_issues": 2,
                "source": "test_execution"
            }
        """
        import re
        
        # If all tests pass, return empty report
        if test_result.get('failed', 0) == 0 and test_result.get('errors', 0) == 0:
            return {
                "file_results": {},
                "all_issues": [],
                "total_issues": 0,
                "source": "test_execution"
            }
        
        # Get detailed analysis from existing method
        analysis_text = self._analyze_test_failures(test_result)
        
        # Parse the output to extract structured data
        messages = test_result.get("messages", [])
        full_output = "\n".join(messages)
        
        file_results = {}
        all_issues = []
        
        # Extract failed tests with file mapping
        # Pattern: FAILED test_file.py::TestClass::test_method or FAILED test_file.py::test_function
        failure_pattern = r"FAILED\s+([\w/\\\.]+\.py)::([\w:]+)"
        
        for match in re.finditer(failure_pattern, full_output):
            test_file_path = match.group(1)
            test_name = match.group(2)
            
            # Map test file to source file
            source_file = self._map_test_to_source_file(test_file_path)
            
            # Extract specific failure context
            assertion_context = self._extract_assertion_context(full_output, test_name)
            
            # Build issue description
            if assertion_context:
                issue_desc = f"Test {test_name}: {assertion_context}"
            else:
                issue_desc = f"Test {test_name} failed - check logic"
            
            # Add to file_results
            if source_file not in file_results:
                file_results[source_file] = {
                    "analysis": {
                        "issues": [],
                        "issue_count": 0
                    },
                    "status": "error"
                }
            
            file_results[source_file]["analysis"]["issues"].append(issue_desc)
            file_results[source_file]["analysis"]["issue_count"] += 1
            all_issues.append(issue_desc)
        
        # Also extract TypeError, AttributeError, etc.
        error_pattern = r"(TypeError|AttributeError|NameError|KeyError):\s*(.+?)(?:\n|$)"
        for match in re.finditer(error_pattern, full_output):
            error_type = match.group(1)
            error_msg = match.group(2).strip()
            issue_desc = f"{error_type}: {error_msg}"
            
            # Try to find which source file this relates to
            # Look backwards for FAILED line
            error_pos = match.start()
            preceding_text = full_output[:error_pos]
            last_failed = None
            for failed_match in re.finditer(failure_pattern, preceding_text):
                last_failed = failed_match
            
            if last_failed:
                test_file_path = last_failed.group(1)
                source_file = self._map_test_to_source_file(test_file_path)
                
                if source_file not in file_results:
                    file_results[source_file] = {
                        "analysis": {"issues": [], "issue_count": 0},
                        "status": "error"
                    }
                
                # Avoid duplicates
                if issue_desc not in file_results[source_file]["analysis"]["issues"]:
                    file_results[source_file]["analysis"]["issues"].append(issue_desc)
                    file_results[source_file]["analysis"]["issue_count"] += 1
                    all_issues.append(issue_desc)
        
        return {
            "file_results": file_results,
            "all_issues": all_issues,
            "total_issues": len(all_issues),
            "source": "test_execution"
        }
