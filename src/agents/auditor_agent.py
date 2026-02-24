"""
Auditor Agent Implementation (Phase 2) - IMPROVED VERSION
Analyzes code using Phase 1 toolsmith APIs (CodeReader, PylintRunner, PytestRunner).
Extends BaseAgent with audit logic.

Improvements:
- AST-based code analysis (replaces naive string matching)
- Comprehensive error handling with specific exceptions
- Type safety with TypedDict
- Input validation
- Parallel processing support
- Structured logging
- Configuration constants
"""

import ast
import os
from typing import Dict, Any, List, Optional, TypedDict
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from src.agents.base_agent import BaseAgent
from src.utils.logger import ActionType
from src.utils.prompt_manager import PromptManager
from src.utils.code_reader import CodeReader
from src.utils.pylint_runner import PylintRunner
from src.utils.pytest_runner import PytestRunner
from src.utils.llm_client import LLMClient


# ============================================================================
# Configuration Constants
# ============================================================================

class AuditorConfig:
    """Configuration constants for AuditorAgent."""
    MAX_CODE_PREVIEW_LINES = 50
    MAX_CODE_PREVIEW_CHARS = 2000
    MAX_WORKERS = 4
    LONG_FILE_THRESHOLD_LINES = 100
    COMPLEX_FUNCTION_THRESHOLD_LINES = 50


# ============================================================================
# Type Definitions
# ============================================================================

class AnalysisResult(TypedDict):
    """Structured result from code analysis."""
    filename: str
    issues: List[str]
    issue_count: int
    code_length: int
    line_count: int
    status: str
    error: Optional[str]


class PylintSummary(TypedDict):
    """Summary of pylint results."""
    score: float
    issue_count: int
    messages: List[str]


class FileAuditResult(TypedDict):
    """Complete audit result for a single file."""
    analysis: AnalysisResult
    pylint: PylintSummary
    status: str
    error: Optional[str]


class AuditSummary(TypedDict):
    """Complete audit summary."""
    agent: str
    files_audited: int
    total_issues: int
    file_results: Dict[str, FileAuditResult]
    all_issues: List[str]
    files_with_errors: int
    status: str


# ============================================================================
# AST-based Code Analyzers
# ============================================================================

class ASTAnalyzer:
    """Utility class for AST-based code analysis."""
    
    @staticmethod
    def has_bare_except(code: str) -> bool:
        """
        Detect bare except clauses using AST.
        
        Args:
            code: Python code to analyze
            
        Returns:
            True if bare except found, False otherwise
        """
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.ExceptHandler) and node.type is None:
                    return True
        except SyntaxError:
            pass
        return False
    
    @staticmethod
    def has_print_statements(code: str) -> bool:
        """
        Detect print() calls (excluding logging context) using AST.
        
        Args:
            code: Python code to analyze
            
        Returns:
            True if print statements found, False otherwise
        """
        try:
            tree = ast.parse(code)
            has_logging_import = False
            has_print_call = False
            
            for node in ast.walk(tree):
                # Check for logging imports
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if 'logging' in alias.name:
                            has_logging_import = True
                elif isinstance(node, ast.ImportFrom):
                    if node.module and 'logging' in node.module:
                        has_logging_import = True
                
                # Check for print calls
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id == 'print':
                        has_print_call = True
            
            return has_print_call and not has_logging_import
        except SyntaxError:
            return False
    
    @staticmethod
    def get_function_complexities(code: str) -> List[tuple[str, int]]:
        """
        Get list of functions with their line counts.
        
        Args:
            code: Python code to analyze
            
        Returns:
            List of (function_name, line_count) tuples
        """
        complexities = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    line_count = node.end_lineno - node.lineno + 1 if node.end_lineno else 0
                    complexities.append((node.name, line_count))
        except SyntaxError:
            pass
        return complexities
    
    @staticmethod
    def has_todo_comments(code: str) -> bool:
        """Check if code contains TODO comments."""
        for line in code.splitlines():
            stripped = line.strip()
            if stripped.startswith('#') and 'TODO' in stripped.upper():
                return True
        return False


# ============================================================================
# Utility Functions
# ============================================================================

def truncate_code(code: str, max_lines: int = AuditorConfig.MAX_CODE_PREVIEW_LINES) -> str:
    """
    Safely truncate code by lines (not characters).
    
    Args:
        code: Code to truncate
        max_lines: Maximum number of lines to include
        
    Returns:
        Truncated code with summary if truncated
    """
    lines = code.splitlines()
    if len(lines) <= max_lines:
        return code
    
    truncated = '\n'.join(lines[:max_lines])
    remaining = len(lines) - max_lines
    return f"{truncated}\n... ({remaining} more lines truncated)"


def validate_directory(target_dir: str) -> Path:
    """
    Validate that target directory exists and is accessible.
    
    Args:
        target_dir: Path to validate
        
    Returns:
        Validated Path object
        
    Raises:
        ValueError: If directory is invalid
        PermissionError: If directory is not accessible
    """
    path = Path(target_dir).resolve()
    
    if not path.exists():
        raise ValueError(f"Target directory does not exist: {target_dir}")
    
    if not path.is_dir():
        raise ValueError(f"Path is not a directory: {target_dir}")
    
    if not os.access(path, os.R_OK):
        raise PermissionError(f"Directory is not readable: {target_dir}")
    
    return path


def validate_file_path(target_dir: Path, filename: str) -> bool:
    """
    Validate that filename doesn't escape target directory (path traversal check).
    
    Args:
        target_dir: Base directory (already validated)
        filename: Filename to check
        
    Returns:
        True if path is safe, False otherwise
    """
    try:
        file_path = (target_dir / filename).resolve()
        return file_path.is_relative_to(target_dir)
    except (ValueError, OSError):
        return False


# ============================================================================
# Main Agent Class
# ============================================================================

class AuditorAgent(BaseAgent):
    """
    Code quality auditor with improved analysis capabilities.
    
    Analyzes code for issues using:
    - AST-based static analysis
    - Pylint integration
    - Pytest integration
    - Heuristic analysis
    
    Phase 2 Toolsmith Agent - Uses Phase 1 tools internally.
    
    Example:
        >>> agent = AuditorAgent()
        >>> result = agent.execute("/path/to/code")
        >>> print(f"Found {result['total_issues']} issues")
    """
    
    def __init__(self, 
                 agent_name: str = "AuditorAgent", 
                 model: str = "models/gemini-2.5-flash",
                 max_workers: int = AuditorConfig.MAX_WORKERS):
        """
        Initialize auditor.
        
        Args:
            agent_name: Name for logging
            model: LLM model to use
            max_workers: Maximum parallel workers for file processing
        """
        super().__init__(agent_name, model)
        self.code_reader: Optional[CodeReader] = None
        self.pylint_runner: Optional[PylintRunner] = None
        self.pytest_runner: Optional[PytestRunner] = None
        self.llm_client: Optional[LLMClient] = None
        self.max_workers = max_workers
        self.ast_analyzer = ASTAnalyzer()
        self.prompt_manager = PromptManager()
    
    def analyze(self, code: str, filename: str = "unknown.py") -> AnalysisResult:
        """
        Analyze single code snippet using AST-based analysis.
        
        Args:
            code: Python code to analyze
            filename: Optional filename for context
            
        Returns:
            Structured analysis result with issues found
            
        Raises:
            ValueError: If code is empty or invalid
        """
        if not code or not code.strip():
            raise ValueError("Cannot analyze empty code")
        
        lines = code.splitlines()
        preview = truncate_code(code)
        prompt = self.prompt_manager.format("auditor_analyze", preview=preview)
        
        issues = []
        
        # AST-based analysis (accurate detection)
        if self.ast_analyzer.has_bare_except(code):
            issues.append("Bare except clause found (bad practice - catches all exceptions)")
        
        if self.ast_analyzer.has_print_statements(code):
            issues.append("Using print() statements without logging module")
        
        if self.ast_analyzer.has_todo_comments(code):
            issues.append("TODO comments found - incomplete implementation")
        
        # Function complexity analysis
        complex_functions = [
            (name, lines) for name, lines in self.ast_analyzer.get_function_complexities(code)
            if lines > AuditorConfig.COMPLEX_FUNCTION_THRESHOLD_LINES
        ]
        
        if complex_functions:
            for func_name, line_count in complex_functions:
                issues.append(
                    f"Complex function '{func_name}' ({line_count} lines) - "
                    f"consider refactoring"
                )
        
        # File length analysis
        if len(lines) > AuditorConfig.LONG_FILE_THRESHOLD_LINES:
            issues.append(
                f"File is long ({len(lines)} lines), consider splitting into modules"
            )
        
        response = f"Found {len(issues)} potential issues in {filename}"
        
        self._log_action(
            action=ActionType.ANALYSIS,
            prompt=prompt,
            response=response,
            extra_details={
                "filename": filename,
                "code_length": len(code),
                "line_count": len(lines),
                "issues_found": len(issues),
                "issues": issues,
                "complex_functions": len(complex_functions)
            }
        )
        
        return AnalysisResult(
            filename=filename,
            issues=issues,
            issue_count=len(issues),
            code_length=len(code),
            line_count=len(lines),
            status="analyzed",
            error=None
        )
    
    def analyze_semantics_with_llm(self, code: str, filename: str = "unknown.py") -> List[str]:
        """
        Use LLM to detect potential logic errors and semantic issues.
        
        Args:
            code: Python code to analyze
            filename: Optional filename for context
            
        Returns:
            List of potential semantic issues found
        """
        if not self.llm_client:
            return []
        
        try:
            # Ask LLM to analyze the code for logic errors
            preview = truncate_code(code, max_lines=30)
            prompt = self.prompt_manager.format("auditor_semantic", preview=preview)
            
            response = self.llm_client.query(prompt)
            
            if response and "no semantic issues" not in response.lower():
                # Parse response to extract issues
                issues = [
                    line.strip() 
                    for line in response.split('\n') 
                    if line.strip() and not line.strip().startswith('#')
                ]
                
                self.logger.info(f"LLM detected {len(issues)} semantic issues in {filename}")
                return issues
            
            return []
        
        except Exception as e:
            self.logger.debug(f"LLM semantic analysis failed: {e}")
            return []
    
    def _process_single_file(self, filename: str, target_dir: Path) -> FileAuditResult:
        """
        Process a single file (used for parallel execution).
        
        Args:
            filename: File to process
            target_dir: Base directory
            
        Returns:
            Audit result for the file
        """
        try:
            # Security check: prevent path traversal
            if not validate_file_path(target_dir, filename):
                raise ValueError(f"Invalid file path (security): {filename}")
            
            # Read file
            code = self.code_reader.read_file(filename)
            
            # Run AST-based analysis
            analysis = self.analyze(code, filename)
            
            # Run semantic analysis with LLM to detect logic errors
            if not filename.startswith("test_"):  # Skip test files
                semantic_issues = self.analyze_semantics_with_llm(code, filename)
                if semantic_issues:
                    analysis["issues"].extend(semantic_issues)
                    analysis["issue_count"] = len(analysis["issues"])
            
            # Run pylint
            try:
                pylint_result = self.pylint_runner.run_pylint(filename)
                pylint_summary = PylintSummary(
                    score=pylint_result.get("score", 0.0),
                    issue_count=len(pylint_result.get("messages", [])),
                    messages=pylint_result.get("messages", [])
                )
                
                # Log pylint score separately (score only, no detailed messages)
                pylint_prompt = f"Analyze code quality with pylint for {filename}"
                pylint_response = f"Pylint score: {pylint_summary['score']:.2f}/10"
                
                self._log_action(
                    action=ActionType.ANALYSIS,
                    prompt=pylint_prompt,
                    response=pylint_response,
                    extra_details={
                        "filename": filename,
                        "pylint_score": pylint_summary["score"]
                    }
                )
                
                self.logger.info(
                    f"{filename}: Pylint score = {pylint_summary['score']:.2f}/10"
                )
                
            except Exception as e:
                self.logger.warning(f"Pylint failed for {filename}: {e}")
                pylint_summary = PylintSummary(
                    score=0.0,
                    issue_count=0,
                    messages=[f"Pylint error: {str(e)}"]
                )
            
            return FileAuditResult(
                analysis=analysis,
                pylint=pylint_summary,
                status="success",
                error=None
            )
        
        except FileNotFoundError as e:
            self.logger.error(f"File not found: {filename} - {e}")
            return FileAuditResult(
                analysis=AnalysisResult(
                    filename=filename,
                    issues=[],
                    issue_count=0,
                    code_length=0,
                    line_count=0,
                    status="error",
                    error=f"File not found: {str(e)}"
                ),
                pylint=PylintSummary(score=0.0, issue_count=0, messages=[]),
                status="error",
                error=f"File not found: {str(e)}"
            )
        
        except PermissionError as e:
            self.logger.error(f"Permission denied: {filename} - {e}")
            return FileAuditResult(
                analysis=AnalysisResult(
                    filename=filename,
                    issues=[],
                    issue_count=0,
                    code_length=0,
                    line_count=0,
                    status="error",
                    error=f"Permission denied: {str(e)}"
                ),
                pylint=PylintSummary(score=0.0, issue_count=0, messages=[]),
                status="error",
                error=f"Permission denied: {str(e)}"
            )
        
        except Exception as e:
            self.logger.error(f"Unexpected error processing {filename}: {e}", exc_info=True)
            return FileAuditResult(
                analysis=AnalysisResult(
                    filename=filename,
                    issues=[],
                    issue_count=0,
                    code_length=0,
                    line_count=0,
                    status="error",
                    error=f"Unexpected error: {str(e)}"
                ),
                pylint=PylintSummary(score=0.0, issue_count=0, messages=[]),
                status="error",
                error=f"Unexpected error: {str(e)}"
            )
    
    def execute(self, target_dir: str, parallel: bool = True) -> AuditSummary:
        """
        Audit all Python files in target directory.
        
        Args:
            target_dir: Path to code directory
            parallel: Whether to use parallel processing (default: True)
            
        Returns:
            Complete audit summary with all results
            
        Raises:
            ValueError: If target_dir is invalid
            PermissionError: If target_dir is not accessible
            RuntimeError: If tool initialization fails
        """
        # Validate directory
        validated_path = validate_directory(target_dir)
        
        # Initialize Phase 1 tools
        try:
            self.code_reader = CodeReader(target_dir)
            self.pylint_runner = PylintRunner(target_dir)
            self.pytest_runner = PytestRunner(target_dir)
            
            # Try to initialize LLM for semantic analysis (optional)
            try:
                self.llm_client = LLMClient()
                self.logger.info("LLM client initialized for semantic analysis")
            except Exception as llm_err:
                self.logger.warning(f"LLM initialization skipped: {llm_err}. Semantic analysis disabled.")
                self.llm_client = None
            
            self.logger.info(f"Initialized tools for directory: {target_dir}")
        except Exception as e:
            self.logger.error(f"Failed to initialize tools: {e}", exc_info=True)
            raise RuntimeError(f"Tool initialization failed: {e}") from e
        
        # Get all Python files
        try:
            files = self.code_reader.list_python_files()
            self.logger.info(f"Found {len(files)} Python files to audit")
        except Exception as e:
            self.logger.error(f"Failed to list files: {e}", exc_info=True)
            raise RuntimeError(f"Failed to list files: {e}") from e
        
        if not files:
            self.logger.warning(f"No Python files found in {target_dir}")
            return AuditSummary(
                agent=self.agent_name,
                files_audited=0,
                total_issues=0,
                file_results={},
                all_issues=[],
                files_with_errors=0,
                status="no_files_found"
            )
        
        audit_results: Dict[str, FileAuditResult] = {}
        
        # Process files (parallel or sequential)
        if parallel and len(files) > 1:
            self.logger.info(f"Processing files in parallel (max {self.max_workers} workers)")
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_file = {
                    executor.submit(self._process_single_file, f, validated_path): f 
                    for f in files
                }
                
                for future in as_completed(future_to_file):
                    filename = future_to_file[future]
                    try:
                        result = future.result()
                        audit_results[filename] = result
                    except Exception as e:
                        self.logger.error(
                            f"Parallel processing error for {filename}: {e}", 
                            exc_info=True
                        )
                        audit_results[filename] = FileAuditResult(
                            analysis=AnalysisResult(
                                filename=filename,
                                issues=[],
                                issue_count=0,
                                code_length=0,
                                line_count=0,
                                status="error",
                                error=str(e)
                            ),
                            pylint=PylintSummary(score=0.0, issue_count=0, messages=[]),
                            status="error",
                            error=str(e)
                        )
        else:
            self.logger.info("Processing files sequentially")
            for filename in files:
                audit_results[filename] = self._process_single_file(filename, validated_path)
        
        # Run tests to detect runtime/logic errors
        self.logger.info("Running tests to detect runtime and logic errors...")
        try:
            test_result = self.pytest_runner.run_tests()
            
            if not test_result.get("success", True):
                # Tests failed - add these as issues
                test_issues = []
                
                # Parse test output to extract meaningful failure messages
                # Look for assertion failures with actual vs expected values
                full_output = "\n".join(test_result.get("messages", []))
                
                # Extract specific assertion failures like "assert -1 == 5"
                import re
                assertions = re.findall(r"assert\s+([^\n]+)", full_output)
                for assertion in assertions:
                    test_issues.append(f"Assertion failed: {assertion.strip()}")
                
                # If no specific assertions, look for generic test names
                if not test_issues:
                    for msg in test_result.get("messages", []):
                        if "FAILED" in msg:
                            # Extract test name like "test_add" from "test_calculator.py::test_add FAILED"
                            test_match = re.search(r"(test_\w+)\s+FAILED", msg)
                            if test_match:
                                test_name = test_match.group(1)
                                test_issues.append(f"Test {test_name} is failing - check logic")
                        elif "assert" in msg:
                            test_issues.append(f"Test failure: {msg.strip()}")
                
                # If we found specific assertion messages, use those
                if test_issues:
                    # Find the main module file (likely first non-test file)
                    main_file = next((f for f in files if not f.startswith("test_")), files[0] if files else None)
                    
                    if main_file and main_file in audit_results:
                        # Add test failures as issues for the main module
                        audit_results[main_file]["analysis"]["issues"].extend(test_issues[:5])
                        audit_results[main_file]["analysis"]["issue_count"] = len(audit_results[main_file]["analysis"]["issues"])
                        self.logger.info(f"Added {len(test_issues)} test failure issues to {main_file}")
                
                # Log test execution details
                self._log_action(
                    action=ActionType.DEBUG,
                    prompt=f"Run tests on {target_dir}",
                    response=f"Test execution: {test_result['failed']} failed, {test_result['errors']} errors",
                    extra_details={
                        "test_passed": False,
                        "test_failed": test_result.get("failed", 0),
                        "test_errors": test_result.get("errors", 0),
                        "test_messages": test_result.get("messages", [])[:3]  # First 3 messages
                    }
                )
            else:
                self.logger.info("All tests passed - no runtime errors detected")
        except Exception as e:
            self.logger.warning(f"Test execution failed during audit: {e}")
        
        # Aggregate results
        all_issues: List[str] = []
        files_with_errors = 0
        
        for filename, result in audit_results.items():
            if result["status"] == "error":
                files_with_errors += 1
            else:
                all_issues.extend(result["analysis"]["issues"])
        
        # Log summary
        summary_prompt = f"Audited {len(files)} files in {target_dir}"
        summary_response = (
            f"Audit complete: {len(all_issues)} total issues found, "
            f"{files_with_errors} files with errors"
        )
        
        self._log_action(
            action=ActionType.ANALYSIS,
            prompt=summary_prompt,
            response=summary_response,
            extra_details={
                "files_audited": len(files),
                "total_issues": len(all_issues),
                "files_with_errors": files_with_errors,
                "parallel_processing": parallel
            }
        )
        
        self.logger.info(summary_response)
        
        return AuditSummary(
            agent=self.agent_name,
            files_audited=len(files),
            total_issues=len(all_issues),
            file_results=audit_results,
            all_issues=all_issues,
            files_with_errors=files_with_errors,
            status="audit_complete"
        )


# ============================================================================
# Report Classes
# ============================================================================

@dataclass
class AuditorReport:
    """
    Structured audit report from AuditorAgent.
    
    Provides convenient access to audit results and analysis methods.
    """
    
    result: AuditSummary
    files: Dict[str, FileAuditResult] = field(default_factory=dict)
    all_issues: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize derived fields from result."""
        self.files = self.result.get("file_results", {})
        self.all_issues = self.result.get("all_issues", [])
    
    def get_critical_issues(self) -> List[str]:
        """
        Get high-priority issues that should be fixed immediately.
        
        Returns:
            List of critical issue descriptions
        """
        critical_patterns = [
            "Bare except",
            "print()",
            "Hard-coded",
            "TODO",
            "security"
        ]
        
        return [
            issue for issue in self.all_issues 
            if any(pattern.lower() in issue.lower() for pattern in critical_patterns)
        ]
    
    def get_files_by_issue_count(self) -> List[tuple[str, int]]:
        """
        Get files sorted by issue count (highest first).
        
        Returns:
            List of (filename, issue_count) tuples
        """
        files_with_counts = []
        
        for filename, data in self.files.items():
            if data["status"] == "success":
                count = data["analysis"]["issue_count"]
                files_with_counts.append((filename, count))
        
        return sorted(files_with_counts, key=lambda x: x[1], reverse=True)
    
    def get_average_pylint_score(self) -> float:
        """
        Calculate average pylint score across all files.
        
        Returns:
            Average score (0-10 scale)
        """
        scores = [
            data["pylint"]["score"]
            for data in self.files.values()
            if data["status"] == "success" and data["pylint"]["score"] > 0
        ]
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def get_files_with_errors(self) -> List[str]:
        """
        Get list of files that failed processing.
        
        Returns:
            List of filenames with errors
        """
        return [
            filename 
            for filename, data in self.files.items() 
            if data["status"] == "error"
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dict for JSON serialization.
        
        Returns:
            Dictionary representation of report
        """
        return {
            "files_audited": self.result.get("files_audited", 0),
            "total_issues": self.result.get("total_issues", 0),
            "files_with_errors": self.result.get("files_with_errors", 0),
            "average_pylint_score": self.get_average_pylint_score(),
            "critical_issues": self.get_critical_issues(),
            "files_by_issue_count": self.get_files_by_issue_count(),
            "error_files": self.get_files_with_errors()
        }
    
    def __str__(self) -> str:
        """String representation of report."""
        return (
            f"AuditorReport(files={self.result['files_audited']}, "
            f"issues={self.result['total_issues']}, "
            f"errors={self.result['files_with_errors']})"
        )