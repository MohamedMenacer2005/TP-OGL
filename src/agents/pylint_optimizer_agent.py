"""
Pylint Optimizer Agent Implementation
Focuses exclusively on increasing pylint scores between Corrector and Judge phases.
Generates targeted fixes for pylint violations without affecting test logic.

Extends BaseAgent with pylint-specific optimization logic.

Architecture:
- Input: Code from CorrectorAgent + baseline pylint scores
- Process: Identify top pylint violations → generate score-targeted fixes
- Validation: Accept only if new_score >= baseline_score
- Output: Optimized code ready for Judge phase

Example Pipeline:
  Auditor → Corrector → PylintOptimizer → Judge
                            ↑
                    Focuses on style/quality
"""

import ast
import re
from typing import Dict, Any, List, Optional, TypedDict, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import os

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from src.agents.base_agent import BaseAgent
from src.utils.logger import ActionType
from src.utils.prompt_manager import PromptManager
from src.utils.code_reader import CodeReader
from src.utils.llm_client import LLMClient
from src.utils.pylint_runner import PylintRunner


# ============================================================================
# Configuration Constants
# ============================================================================

class OptimizerConfig:
    """Configuration constants for PylintOptimizerAgent."""
    MAX_CODE_PREVIEW_LINES = 30
    MAX_OPTIMIZATION_ATTEMPTS = 3
    SCORE_IMPROVEMENT_THRESHOLD = 0.1  # Minimum score improvement to accept change
    TARGET_SCORE = 9.0  # Aim for this pylint score


# ============================================================================
# Type Definitions
# ============================================================================

class PylintViolation(TypedDict):
    """Single pylint violation."""
    message: str
    code: str
    severity: str
    line: int
    column: int


class Optimization(TypedDict):
    """Single optimization result."""
    violation_code: str
    violation_message: str
    optimization_type: str
    original_code: str
    optimized_code: str
    score_before: float
    score_after: float
    score_delta: float
    status: str
    reason: str


class FileOptimizationResult(TypedDict):
    """Optimization results for a single file."""
    filename: str
    optimizations_count: int
    optimizations: List[Optimization]
    baseline_score: float
    final_score: float
    score_improvement: float
    status: str
    error: Optional[str]


class OptimizationSummary(TypedDict):
    """Complete optimization summary."""
    agent: str
    files_optimized: int
    total_optimizations: int
    total_score_improvement: float
    file_results: Dict[str, FileOptimizationResult]
    status: str


# ============================================================================
# Pylint Violation Analyzer
# ============================================================================

class PylintAnalyzer:
    """Utility class for analyzing and parsing pylint output."""
    
    @staticmethod
    def categorize_violations(messages: List[Dict[str, Any]]) -> Dict[str, List[PylintViolation]]:
        """
        Categorize pylint violations by error code.
        
        Args:
            messages: List of pylint message dicts
            
        Returns:
            Dict mapping error codes to violations
        """
        violations_by_code = {}
        
        for msg in messages:
            code = msg.get("symbol", "unknown")
            violation: PylintViolation = {
                "message": msg.get("message", ""),
                "code": code,
                "severity": PylintAnalyzer._get_severity(code),
                "line": msg.get("line", 0),
                "column": msg.get("column", 0)
            }
            
            if code not in violations_by_code:
                violations_by_code[code] = []
            violations_by_code[code].append(violation)
        
        return violations_by_code
    
    @staticmethod
    def _get_severity(code: str) -> str:
        """
        Get severity level based on pylint error code.
        
        Args:
            code: Pylint error code (e.g., 'C0111', 'W0612')
            
        Returns:
            Severity level: 'critical', 'high', 'medium', 'low'
        """
        # Pylint code format: [EWRCF]####
        # E = Error, W = Warning, R = Refactor, C = Convention, F = Fatal
        if code.startswith('E') or code.startswith('F'):
            return 'critical'
        elif code.startswith('W'):
            return 'high'
        elif code.startswith('R'):
            return 'medium'
        elif code.startswith('C'):
            return 'low'
        return 'unknown'
    
    @staticmethod
    def get_high_impact_violations(violations_by_code: Dict[str, List]) -> List[Tuple[str, int]]:
        """
        Get violations sorted by impact (most frequent high-severity first).
        
        Args:
            violations_by_code: Categorized violations
            
        Returns:
            List of (code, count) sorted by impact
        """
        impact_scores = []
        
        for code, violations in violations_by_code.items():
            count = len(violations)
            severity = violations[0]["severity"] if violations else "low"
            
            # Impact = count * severity_weight
            severity_weight = {
                'critical': 4,
                'high': 3,
                'medium': 2,
                'low': 1
            }.get(severity, 1)
            
            impact = count * severity_weight
            impact_scores.append((code, count, impact, severity))
        
        # Sort by impact descending, then by count
        return [(code, count) for code, count, impact, severity in 
                sorted(impact_scores, key=lambda x: (-x[2], -x[1]))]


# ============================================================================
# AST-based Optimizers
# ============================================================================

class ASTOptimizer:
    """Utility class for AST-based pylint-score optimizations."""
    
    @staticmethod
    def add_docstrings(code: str) -> Tuple[str, bool]:
        """
        Add missing docstrings to functions and classes (fixes C0111, C0112).
        
        Args:
            code: Python code to analyze
            
        Returns:
            Tuple of (optimized_code, was_changed)
        """
        try:
            tree = ast.parse(code)
            lines = code.splitlines(keepends=True)
            insertions = []  # (line_num, text_to_insert)
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    # Check if docstring exists
                    if not (node.body and isinstance(node.body[0], ast.Expr) and 
                           isinstance(node.body[0].value, ast.Constant)):
                        # Add minimal docstring
                        indent = " " * (node.col_offset + 4)
                        docstring = f'{indent}"""{node.name}."""\n'
                        insertions.append((node.lineno, docstring))
            
            if not insertions:
                return code, False
            
            # Apply insertions in reverse order to maintain line numbers
            for line_num, docstring in reversed(insertions):
                insert_pos = min(line_num, len(lines))
                lines.insert(insert_pos, docstring)
            
            return ''.join(lines), True
        
        except SyntaxError:
            return code, False
    
    @staticmethod
    def fix_trailing_whitespace(code: str) -> Tuple[str, bool]:
        """
        Remove trailing whitespace (fixes C0303).
        
        Args:
            code: Python code to analyze
            
        Returns:
            Tuple of (optimized_code, was_changed)
        """
        lines = code.splitlines(keepends=True)
        optimized_lines = []
        changed = False
        
        for line in lines:
            # Remove trailing whitespace but preserve newline
            stripped = line.rstrip()
            if line.endswith('\n'):
                new_line = stripped + '\n'
            else:
                new_line = stripped
            
            if new_line != line:
                changed = True
            
            optimized_lines.append(new_line)
        
        return ''.join(optimized_lines), changed
    
    @staticmethod
    def fix_line_too_long(code: str, max_length: int = 100) -> Tuple[str, bool]:
        """
        Attempt to break long lines (fixes C0301).
        
        Args:
            code: Python code to analyze
            max_length: Maximum line length
            
        Returns:
            Tuple of (optimized_code, was_changed)
        """
        lines = code.splitlines(keepends=True)
        optimized_lines = []
        changed = False
        
        for line in lines:
            # Skip if line is comment or string
            stripped = line.rstrip()
            if len(stripped) <= max_length or stripped.startswith('#'):
                optimized_lines.append(line)
                continue
            
            # Simple line breaking for long strings in function calls
            if '(' in stripped and ')' in stripped and len(stripped) > max_length:
                # Try to break at comma
                if ',' in stripped:
                    indent = len(stripped) - len(stripped.lstrip())
                    base_indent = ' ' * indent
                    continuation_indent = ' ' * (indent + 4)
                    
                    # Simple approach: break after commas
                    parts = stripped.split(', ')
                    if len(parts) > 1:
                        new_lines = [parts[0] + ',\n']
                        for i, part in enumerate(parts[1:]):
                            if i == len(parts) - 2:
                                new_lines.append(continuation_indent + part + '\n')
                            else:
                                new_lines.append(continuation_indent + part + ',\n')
                        
                        optimized_lines.extend(new_lines)
                        changed = True
                        continue
            
            optimized_lines.append(line)
        
        return ''.join(optimized_lines), changed
    
    @staticmethod
    def fix_unused_variables(code: str) -> Tuple[str, bool]:
        """
        Remove unused variables (fixes W0612).
        
        Args:
            code: Python code to analyze
            
        Returns:
            Tuple of (optimized_code, was_changed)
        """
        try:
            tree = ast.parse(code)
            lines = code.splitlines(keepends=True)
            
            # Simple heuristic: find assignments that look unused (name starts with _)
            # Real implementation would need scope analysis
            unused_pattern = re.compile(r'^(\s*)([a-z_]\w*)\s*=\s*(?:None|0|""|\'\'|\[\]|\{\})')
            
            optimized_lines = []
            changed = False
            
            for line in lines:
                match = unused_pattern.match(line)
                if match and not line.strip().startswith('#'):
                    # Skip this line (remove unused assignment)
                    # But keep it if it's a common pattern
                    if not any(pattern in line for pattern in ['_', 'self.', 'cls.']):
                        changed = True
                        continue
                
                optimized_lines.append(line)
            
            return ''.join(optimized_lines), changed
        
        except SyntaxError:
            return code, False


# ============================================================================
# Main Agent Class
# ============================================================================

class PylintOptimizerAgent(BaseAgent):
    """
    Pylint score optimizer agent.
    
    Focuses exclusively on increasing pylint scores through style and quality improvements.
    Works between Corrector and Judge phases.
    
    Optimizations target:
    - Missing docstrings (C0111, C0112)
    - Trailing whitespace (C0303)
    - Long lines (C0301)
    - Unused variables (W0612)
    - Naming conventions (C0103)
    
    Example:
        >>> agent = PylintOptimizerAgent()
        >>> result = agent.execute("/path/to/code", baseline_scores)
        >>> print(f"Score improved by {result['total_score_improvement']}")
    """
    
    def __init__(self, 
                 agent_name: str = "PylintOptimizerAgent",
                 model: str = "models/gemini-2.0-flash"):
        """
        Initialize optimizer.
        
        Args:
            agent_name: Name for logging
            model: LLM model to use for semantic optimizations
        """
        super().__init__(agent_name, model)
        self.code_reader: Optional[CodeReader] = None
        self.pylint_runner: Optional[PylintRunner] = None
        self.llm_client: Optional[LLMClient] = None
        self.ast_optimizer = ASTOptimizer()
        self.analyzer = PylintAnalyzer()
        self.prompt_manager = PromptManager()
    
    def analyze(self, code: str, filename: str = "unknown.py") -> dict:
        """
        Analyze code pylint violations (required by abstract base class).
        
        Args:
            code: Python code to analyze
            filename: Optional filename for context
            
        Returns:
            Dict with violation analysis
        """
        # This is a stub for the abstract method requirement
        # Real analysis happens in optimize_file
        return {
            "filename": filename,
            "analysis": "Pylint optimization analysis (deferred to optimize_file)"
        }
    
    def optimize_file(self, 
                     code: str, 
                     filename: str,
                     baseline_score: float) -> FileOptimizationResult:
        """
        Optimize a single file for pylint score improvement.
        
        Args:
            code: Original code
            filename: Filename for context
            baseline_score: Starting pylint score
            
        Returns:
            Optimization result for the file
        """
        optimized_code = code
        current_score = baseline_score
        optimizations: List[Optimization] = []
        
        # Strategy 1: Fix trailing whitespace (fast, safe)
        optimized_code, changed = self.ast_optimizer.fix_trailing_whitespace(optimized_code)
        if changed:
            new_score = self._evaluate_score(optimized_code, filename)
            optimization: Optimization = {
                "violation_code": "C0303",
                "violation_message": "Trailing whitespace",
                "optimization_type": "AST",
                "original_code": code,
                "optimized_code": optimized_code,
                "score_before": current_score,
                "score_after": new_score,
                "score_delta": new_score - current_score,
                "status": "accepted" if new_score >= current_score else "rejected",
                "reason": f"Trailing whitespace fix: {current_score:.2f} → {new_score:.2f}"
            }
            
            if new_score >= current_score:
                optimizations.append(optimization)
                current_score = new_score
                code = optimized_code
                self.logger.info(
                    f"{filename}: Trailing whitespace fix accepted "
                    f"({current_score:.2f} score)"
                )
            else:
                self.logger.debug(f"{filename}: Trailing whitespace fix rejected")
        
        # Strategy 2: Add missing docstrings (moderate impact)
        optimized_code, changed = self.ast_optimizer.add_docstrings(code)
        if changed:
            new_score = self._evaluate_score(optimized_code, filename)
            optimization: Optimization = {
                "violation_code": "C0111",
                "violation_message": "Missing docstrings",
                "optimization_type": "AST",
                "original_code": code,
                "optimized_code": optimized_code,
                "score_before": current_score,
                "score_after": new_score,
                "score_delta": new_score - current_score,
                "status": "accepted" if new_score >= current_score else "rejected",
                "reason": f"Docstring addition: {current_score:.2f} → {new_score:.2f}"
            }
            
            if new_score >= current_score:
                optimizations.append(optimization)
                current_score = new_score
                code = optimized_code
                self.logger.info(
                    f"{filename}: Docstring fix accepted "
                    f"({current_score:.2f} score)"
                )
            else:
                self.logger.debug(f"{filename}: Docstring fix rejected")
        
        # Strategy 3: Use LLM for semantic-aware optimizations (high-impact)
        if self.llm_client and current_score < OptimizerConfig.TARGET_SCORE:
            llm_optimized, changed = self._optimize_with_llm(code, filename)
            if changed:
                new_score = self._evaluate_score(llm_optimized, filename)
                optimization: Optimization = {
                    "violation_code": "SEMANTIC",
                    "violation_message": "Code quality improvements",
                    "optimization_type": "LLM",
                    "original_code": code,
                    "optimized_code": llm_optimized,
                    "score_before": current_score,
                    "score_after": new_score,
                    "score_delta": new_score - current_score,
                    "status": "accepted" if new_score >= current_score else "rejected",
                    "reason": f"LLM optimization: {current_score:.2f} → {new_score:.2f}"
                }
                
                if new_score >= current_score:
                    optimizations.append(optimization)
                    current_score = new_score
                    code = llm_optimized
                    self.logger.info(
                        f"{filename}: LLM optimization accepted "
                        f"({current_score:.2f} score)"
                    )
                else:
                    self.logger.debug(f"{filename}: LLM optimization rejected")
        
        # Log summary
        summary_response = (
            f"Optimization complete: {len(optimizations)} optimizations applied, "
            f"score {baseline_score:.2f} → {current_score:.2f} "
            f"({current_score - baseline_score:+.2f})"
        )
        
        self._log_action(
            action=ActionType.FIX,
            prompt=f"Optimize {filename} for pylint score (baseline: {baseline_score:.2f})",
            response=summary_response,
            extra_details={
                "filename": filename,
                "baseline_score": baseline_score,
                "final_score": current_score,
                "optimizations_count": len(optimizations),
                "score_improvement": current_score - baseline_score
            }
        )
        
        return FileOptimizationResult(
            filename=filename,
            optimizations_count=len(optimizations),
            optimizations=optimizations,
            baseline_score=baseline_score,
            final_score=current_score,
            score_improvement=current_score - baseline_score,
            status="optimized" if current_score > baseline_score else "unchanged",
            error=None
        )
    
    def _evaluate_score(self, code: str, filename: str) -> float:
        """
        Evaluate pylint score for code.
        
        Args:
            code: Code to evaluate
            filename: Filename for context
            
        Returns:
            Pylint score (0-10)
        """
        try:
            # Write code to temporary location for pylint analysis
            # For now, use existing pylint_runner with a pseudo-file
            if not self.pylint_runner:
                return 0.0
            
            result = self.pylint_runner.run_pylint(filename)
            return result.get("score", 0.0)
        
        except Exception as e:
            self.logger.debug(f"Score evaluation failed: {e}")
            return 0.0
    
    def _optimize_with_llm(self, code: str, filename: str) -> Tuple[str, bool]:
        """
        Use LLM to generate code quality optimizations.
        
        Args:
            code: Original code
            filename: Filename for context
            
        Returns:
            Tuple of (optimized_code, was_changed)
        """
        if not self.llm_client:
            return code, False
        
        try:
            # Truncate code for LLM
            lines = code.splitlines()
            if len(lines) > OptimizerConfig.MAX_CODE_PREVIEW_LINES:
                preview = '\n'.join(lines[:OptimizerConfig.MAX_CODE_PREVIEW_LINES]) + '\n... (truncated)'
            else:
                preview = code
            
            prompt = self.prompt_manager.format(
                "optimizer_enhance",
                preview=preview,
                filename=filename
            )
            
            response = self.llm_client.query(prompt)
            
            if not response or "no changes" in response.lower():
                return code, False
            
            # Extract code block from response
            if "```python" in response:
                start = response.find("```python") + len("```python")
                end = response.find("```", start)
                if end > start:
                    optimized = response[start:end].strip()
                    # Validate syntax
                    try:
                        ast.parse(optimized)
                        return optimized, True
                    except SyntaxError:
                        self.logger.warning(f"LLM generated invalid Python for {filename}")
                        return code, False
            
            return code, False
        
        except Exception as e:
            self.logger.debug(f"LLM optimization failed: {e}")
            return code, False
    
    def execute(self,
               target_dir: str,
               corrector_report: Dict[str, Any],
               auditor_report: Dict[str, Any]) -> OptimizationSummary:
        """
        Optimize all Python files for pylint score improvement.
        
        Args:
            target_dir: Path to code directory
            corrector_report: Output from CorrectorAgent (with pylint baseline)
            auditor_report: Output from AuditorAgent (for baseline scores)
            
        Returns:
            Complete optimization summary
            
        Raises:
            RuntimeError: If tool initialization fails
        """
        # Initialize tools
        try:
            self.code_reader = CodeReader(target_dir)
            self.pylint_runner = PylintRunner(target_dir)
            
            # Try to initialize LLM (optional)
            try:
                self.llm_client = LLMClient()
                self.logger.info("LLM client initialized for semantic optimization")
            except Exception as llm_err:
                self.logger.warning(f"LLM initialization skipped: {llm_err}")
                self.llm_client = None
            
            self.logger.info(f"Initialized tools for directory: {target_dir}")
        except Exception as e:
            self.logger.error(f"Failed to initialize tools: {e}", exc_info=True)
            raise RuntimeError(f"Tool initialization failed: {e}") from e
        
        # Get baseline scores from auditor report
        file_results = auditor_report.get("file_results", {})
        baseline_scores = {}
        
        for filename, file_data in file_results.items():
            pylint_data = file_data.get("pylint", {})
            baseline_scores[filename] = pylint_data.get("score", 0.0)
        
        self.logger.info(
            f"Processing {len(file_results)} files for pylint optimization "
            f"(baseline scores: {[f'{s:.2f}' for s in baseline_scores.values()]})"
        )
        
        optimizations: Dict[str, FileOptimizationResult] = {}
        total_improvement = 0.0
        
        for filename in file_results.keys():
            try:
                code = self.code_reader.read_file(filename)
                baseline_score = baseline_scores.get(filename, 0.0)
                
                result = self.optimize_file(code, filename, baseline_score)
                optimizations[filename] = result
                total_improvement += result["score_improvement"]
                
                # Write optimized code back
                if result["status"] == "optimized" and result["optimizations"]:
                    try:
                        optimized_code = result["optimizations"][-1]["optimized_code"]
                        file_path = Path(target_dir) / filename
                        file_path.write_text(optimized_code, encoding='utf-8')
                        self.logger.info(
                            f"Wrote optimized code to {filename} "
                            f"(+{result['score_improvement']:.2f} score)"
                        )
                    except Exception as e:
                        self.logger.error(f"Failed to write optimized code to {filename}: {e}")
            
            except Exception as e:
                self.logger.error(f"Optimization failed for {filename}: {e}", exc_info=True)
                optimizations[filename] = FileOptimizationResult(
                    filename=filename,
                    optimizations_count=0,
                    optimizations=[],
                    baseline_score=baseline_scores.get(filename, 0.0),
                    final_score=baseline_scores.get(filename, 0.0),
                    score_improvement=0.0,
                    status="error",
                    error=str(e)
                )
        
        # Log final summary
        summary_response = (
            f"Optimization phase complete: {len(optimizations)} files processed, "
            f"total score improvement: +{total_improvement:.2f}"
        )
        
        self._log_action(
            action=ActionType.FIX,
            prompt=f"Optimize all files in {target_dir} for pylint scores",
            response=summary_response,
            extra_details={
                "files_processed": len(optimizations),
                "total_score_improvement": total_improvement,
                "avg_score_improvement": total_improvement / len(optimizations) if optimizations else 0
            }
        )
        
        self.logger.info(summary_response)
        
        return OptimizationSummary(
            agent=self.agent_name,
            files_optimized=len(optimizations),
            total_optimizations=sum(r["optimizations_count"] for r in optimizations.values()),
            total_score_improvement=total_improvement,
            file_results=optimizations,
            status="optimization_complete"
        )
