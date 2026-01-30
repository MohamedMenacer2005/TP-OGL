"""
Unit Tests for JudgeAgent (L'Agent Testeur)
Tests self-healing loops, test execution, and mission validation.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from src.agents.judge_agent import JudgeAgent


class TestJudgeAgentBasics:
    """Basic JudgeAgent functionality tests."""

    def test_judge_agent_initialization(self):
        """Test JudgeAgent can be instantiated."""
        judge = JudgeAgent()
        assert judge.agent_name == "JudgeAgent"
        assert judge.model == "gemini-1.5-flash"
        assert judge.max_retry == 3
        assert judge.corrector_callback is None

    def test_judge_agent_with_custom_params(self):
        """Test JudgeAgent initialization with custom parameters."""
        def dummy_corrector(target_dir, error_logs):
            pass
        
        judge = JudgeAgent(
            agent_name="CustomJudge",
            model="gemini-2.0",
            corrector_callback=dummy_corrector,
            max_retry=5
        )
        assert judge.agent_name == "CustomJudge"
        assert judge.model == "gemini-2.0"
        assert judge.max_retry == 5
        assert judge.corrector_callback == dummy_corrector

    def test_judge_analyze_method(self):
        """Test analyze method for testability assessment."""
        judge = JudgeAgent()
        
        # Code with pytest imports
        code_with_tests = "import pytest\ndef test_something(): pass"
        result = judge.analyze(code_with_tests, "test_file.py")
        
        assert result["testable"] is True
        assert result["has_test_imports"] is True
        assert result["filename"] == "test_file.py"

    def test_judge_analyze_code_without_tests(self):
        """Test analyze method on code without test imports."""
        judge = JudgeAgent()
        
        code_without_tests = "def my_function():\n    return 42"
        result = judge.analyze(code_without_tests, "module.py")
        
        assert result["testable"] is False
        assert result["has_test_imports"] is False


class TestJudgeAgentExecution:
    """Test Judge execution and test running."""

    @patch('src.agents.judge_agent.PytestRunner')
    def test_judge_execute_all_tests_pass(self, mock_pytest_runner_class):
        """Test execute when all tests pass."""
        # Mock PytestRunner
        mock_runner = Mock()
        mock_pytest_runner_class.return_value = mock_runner
        mock_runner.run_tests.return_value = {
            "success": True,
            "passed": 5,
            "failed": 0,
            "errors": 0,
            "messages": ["test1 PASSED", "test2 PASSED"],
            "raw_output": "5 passed in 0.42s"
        }
        
        judge = JudgeAgent()
        result = judge.execute("/fake/target")
        
        assert result["success"] is True
        assert result["final_status"] == "PASSED"
        assert result["passed"] == 5
        assert result["failed"] == 0
        assert result["retry_count"] == 0

    @patch('src.agents.judge_agent.PytestRunner')
    def test_judge_execute_some_tests_fail_no_corrector(self, mock_pytest_runner_class):
        """Test execute when tests fail and no corrector available."""
        mock_runner = Mock()
        mock_pytest_runner_class.return_value = mock_runner
        mock_runner.run_tests.return_value = {
            "success": False,
            "passed": 3,
            "failed": 2,
            "errors": 0,
            "messages": ["test1 PASSED", "test2 FAILED", "test3 FAILED"],
            "raw_output": "3 passed, 2 failed in 0.42s"
        }
        
        judge = JudgeAgent(corrector_callback=None)
        result = judge.execute("/fake/target")
        
        assert result["success"] is False
        assert result["final_status"] == "FAILED"
        assert result["failed"] == 2
        assert result["retry_count"] == 0

    @patch('src.agents.judge_agent.PytestRunner')
    def test_judge_self_healing_loop_success(self, mock_pytest_runner_class):
        """Test self-healing loop: first fail, then pass after correction."""
        mock_runner = Mock()
        mock_pytest_runner_class.return_value = mock_runner
        
        # First call: tests fail; second call: tests pass
        mock_runner.run_tests.side_effect = [
            {
                "success": False,
                "passed": 3,
                "failed": 1,
                "errors": 0,
                "messages": ["test1 PASSED", "test2 FAILED"],
                "raw_output": "3 passed, 1 failed"
            },
            {
                "success": True,
                "passed": 4,
                "failed": 0,
                "errors": 0,
                "messages": ["test1 PASSED", "test2 PASSED"],
                "raw_output": "4 passed in 0.42s"
            }
        ]
        
        corrector_called = []
        def mock_corrector(target_dir, error_logs):
            corrector_called.append({"target_dir": target_dir, "error_logs": error_logs})
        
        judge = JudgeAgent(corrector_callback=mock_corrector, max_retry=3)
        result = judge.execute("/fake/target")
        
        assert result["success"] is True
        assert result["final_status"] == "PASSED"
        assert result["retry_count"] == 1
        assert len(corrector_called) == 1
        assert corrector_called[0]["target_dir"] == "/fake/target"

    @patch('src.agents.judge_agent.PytestRunner')
    def test_judge_max_retries_exceeded(self, mock_pytest_runner_class):
        """Test self-healing loop hitting max retries."""
        mock_runner = Mock()
        mock_pytest_runner_class.return_value = mock_runner
        
        # Always return failures
        mock_runner.run_tests.return_value = {
            "success": False,
            "passed": 1,
            "failed": 3,
            "errors": 0,
            "messages": ["test1 PASSED", "test2 FAILED", "test3 FAILED", "test4 FAILED"],
            "raw_output": "1 passed, 3 failed"
        }
        
        corrector_call_count = [0]
        def mock_corrector(target_dir, error_logs):
            corrector_call_count[0] += 1
        
        judge = JudgeAgent(corrector_callback=mock_corrector, max_retry=2)
        result = judge.execute("/fake/target")
        
        assert result["success"] is False
        assert result["final_status"] == "MAX_RETRIES_EXCEEDED"
        assert result["retry_count"] == 2
        assert corrector_call_count[0] == 2

    @patch('src.agents.judge_agent.PytestRunner')
    def test_judge_corrector_callback_error(self, mock_pytest_runner_class):
        """Test handling when corrector callback raises an exception."""
        mock_runner = Mock()
        mock_pytest_runner_class.return_value = mock_runner
        mock_runner.run_tests.return_value = {
            "success": False,
            "passed": 1,
            "failed": 2,
            "errors": 0,
            "messages": ["test1 PASSED", "test2 FAILED"],
            "raw_output": "1 passed, 2 failed"
        }
        
        def failing_corrector(target_dir, error_logs):
            raise ValueError("Corrector failed!")
        
        judge = JudgeAgent(corrector_callback=failing_corrector, max_retry=1)
        result = judge.execute("/fake/target")
        
        # Should stop after error and return failure
        assert result["success"] is False
        assert result["retry_count"] == 1


class TestJudgeAgentMethods:
    """Test individual JudgeAgent methods."""

    @patch('src.agents.judge_agent.PytestRunner')
    def test_run_single_test_file(self, mock_pytest_runner_class):
        """Test running a single test file."""
        mock_runner = Mock()
        mock_pytest_runner_class.return_value = mock_runner
        mock_runner.run_tests.return_value = {
            "success": True,
            "passed": 3,
            "failed": 0,
            "errors": 0,
            "messages": ["All tests passed"],
            "raw_output": "3 passed"
        }
        
        judge = JudgeAgent()
        result = judge.run_single_test_file("/fake/target", "test_module.py")
        
        assert result["success"] is True
        assert result["passed"] == 3
        # Verify PytestRunner.run_tests was called with test_file parameter
        mock_runner.run_tests.assert_called_once_with(test_file="test_module.py")

    @patch('src.agents.judge_agent.PytestRunner')
    def test_validate_mission_complete(self, mock_pytest_runner_class):
        """Test mission validation when complete."""
        mock_runner = Mock()
        mock_pytest_runner_class.return_value = mock_runner
        mock_runner.run_tests.return_value = {
            "success": True,
            "passed": 10,
            "failed": 0,
            "errors": 0,
            "messages": [],
            "raw_output": "10 passed"
        }
        
        judge = JudgeAgent()
        result = judge.validate_mission("/fake/target")
        
        assert result["mission_complete"] is True
        assert result["all_tests_passed"] is True
        assert result["summary"] == "✓ Mission Complete!"

    @patch('src.agents.judge_agent.PytestRunner')
    def test_validate_mission_incomplete(self, mock_pytest_runner_class):
        """Test mission validation when incomplete."""
        mock_runner = Mock()
        mock_pytest_runner_class.return_value = mock_runner
        mock_runner.run_tests.return_value = {
            "success": False,
            "passed": 8,
            "failed": 2,
            "errors": 0,
            "messages": [],
            "raw_output": "8 passed, 2 failed"
        }
        
        judge = JudgeAgent()
        result = judge.validate_mission("/fake/target")
        
        assert result["mission_complete"] is False
        assert result["all_tests_passed"] is False
        assert result["failed"] == 2
        assert result["summary"] == "✗ Tests still failing"


class TestJudgeAgentLogging:
    """Test JudgeAgent logging and experiment data."""

    @patch('src.agents.judge_agent.PytestRunner')
    @patch('src.agents.base_agent.log_experiment')
    def test_judge_logs_test_execution(self, mock_log, mock_pytest_runner_class):
        """Test that JudgeAgent logs test execution."""
        mock_runner = Mock()
        mock_pytest_runner_class.return_value = mock_runner
        mock_runner.run_tests.return_value = {
            "success": True,
            "passed": 5,
            "failed": 0,
            "errors": 0,
            "messages": [],
            "raw_output": "5 passed"
        }
        
        judge = JudgeAgent()
        judge.execute("/fake/target")
        
        # Verify log_experiment was called
        assert mock_log.call_count >= 1
        # Check that first log call has ActionType.DEBUG and SUCCESS status
        first_call_args = mock_log.call_args_list[0]
        assert first_call_args.kwargs["status"] == "SUCCESS"

    @patch('src.agents.judge_agent.PytestRunner')
    @patch('src.agents.base_agent.log_experiment')
    def test_judge_logs_retry_attempts(self, mock_log, mock_pytest_runner_class):
        """Test that JudgeAgent logs each retry attempt."""
        mock_runner = Mock()
        mock_pytest_runner_class.return_value = mock_runner
        
        # Fail first, pass second
        mock_runner.run_tests.side_effect = [
            {
                "success": False,
                "passed": 2,
                "failed": 1,
                "errors": 0,
                "messages": ["FAILED"],
                "raw_output": "2 passed, 1 failed"
            },
            {
                "success": True,
                "passed": 3,
                "failed": 0,
                "errors": 0,
                "messages": ["PASSED"],
                "raw_output": "3 passed"
            }
        ]
        
        def mock_corrector(target_dir, error_logs):
            pass
        
        judge = JudgeAgent(corrector_callback=mock_corrector)
        judge.execute("/fake/target")
        
        # Should have logged: initial execution, retry attempt, final status = 3 calls
        assert mock_log.call_count >= 3


class TestJudgeAgentIntegration:
    """Integration tests with real temp directories."""

    def test_judge_with_real_temp_directory(self):
        """Test JudgeAgent with a real temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a simple test file that passes
            test_file = Path(tmpdir) / "test_sample.py"
            test_file.write_text("""
def test_addition():
    assert 1 + 1 == 2

def test_string():
    assert "hello".upper() == "HELLO"
""")
            
            # Create module file
            module_file = Path(tmpdir) / "sample.py"
            module_file.write_text("""
def add(a, b):
    return a + b
""")
            
            judge = JudgeAgent()
            # Note: This requires pytest to be installed
            # If pytest not installed, PytestRunner will handle gracefully
            result = judge.analyze(module_file.read_text(), "sample.py")
            
            assert result["filename"] == "sample.py"
            assert result["code_length"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
