"""
Metrics Calculator Utility
Compute code quality metrics: complexity, LOC, maintainability.
Toolsmith tool for code analysis.
"""

import re
from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class CodeMetrics:
    """Code quality metrics."""
    lines_of_code: int = 0
    lines_of_comments: int = 0
    lines_blank: int = 0
    function_count: int = 0
    class_count: int = 0
    cyclomatic_complexity: float = 0.0
    avg_function_length: float = 0.0
    avg_class_size: float = 0.0
    maintainability_index: float = 0.0


class MetricsCalculator:
    """Calculate code quality metrics."""
    
    @staticmethod
    def calculate(code: str) -> CodeMetrics:
        """
        Calculate comprehensive metrics for code.
        
        Args:
            code: Python code string
            
        Returns:
            CodeMetrics object with calculated values
        """
        metrics = CodeMetrics()
        
        lines = code.splitlines()
        
        # Count different line types
        metrics.lines_blank = sum(1 for line in lines if not line.strip())
        metrics.lines_of_comments = sum(1 for line in lines if line.strip().startswith('#'))
        metrics.lines_of_code = len(lines) - metrics.lines_blank
        
        # Count functions and classes
        metrics.function_count = len(re.findall(r'^\s*def\s+\w+', code, re.MULTILINE))
        metrics.class_count = len(re.findall(r'^\s*class\s+\w+', code, re.MULTILINE))
        
        # Calculate averages
        if metrics.function_count > 0:
            metrics.avg_function_length = metrics.lines_of_code / metrics.function_count
        if metrics.class_count > 0:
            metrics.avg_class_size = metrics.lines_of_code / metrics.class_count
        
        # Cyclomatic complexity (simplified)
        metrics.cyclomatic_complexity = MetricsCalculator._calculate_cyclomatic(code)
        
        # Maintainability index (simplified Halstead-based)
        metrics.maintainability_index = MetricsCalculator._calculate_maintainability(
            code, metrics.cyclomatic_complexity, metrics.lines_of_code
        )
        
        return metrics
    
    @staticmethod
    def _calculate_cyclomatic(code: str) -> float:
        """
        Simplified cyclomatic complexity calculation.
        Counts decision points: if, elif, else, for, while, except, and, or
        """
        decisions = 0
        decisions += len(re.findall(r'\bif\b', code))
        decisions += len(re.findall(r'\belif\b', code))
        decisions += len(re.findall(r'\belse\b', code))
        decisions += len(re.findall(r'\bfor\b', code))
        decisions += len(re.findall(r'\bwhile\b', code))
        decisions += len(re.findall(r'\bexcept\b', code))
        decisions += len(re.findall(r'\band\b', code))
        decisions += len(re.findall(r'\bor\b', code))
        
        return float(decisions) if decisions > 0 else 1.0
    
    @staticmethod
    def _calculate_maintainability(code: str, complexity: float, loc: int) -> float:
        """
        Simplified Maintainability Index (0-100 scale).
        Based on: lines of code, cyclomatic complexity, lines of comments
        """
        if loc == 0:
            return 100.0
        
        comment_ratio = len(re.findall(r'^\s*#', code, re.MULTILINE)) / loc
        
        # MI formula (simplified): higher comment ratio + lower complexity = better
        mi = 100.0 - (complexity * 5) + (comment_ratio * 20)
        mi = max(0.0, min(100.0, mi))  # Clamp to 0-100
        
        return mi
    
    @staticmethod
    def get_function_metrics(code: str) -> List[Dict[str, Any]]:
        """
        Extract metrics for individual functions.
        
        Args:
            code: Python code
            
        Returns:
            List of dicts with function metrics
        """
        functions = []
        
        # Simple regex to find function definitions
        func_pattern = r'^\s*def\s+(\w+)\s*\((.*?)\):'
        
        for match in re.finditer(func_pattern, code, re.MULTILINE):
            func_name = match.group(1)
            params = match.group(2)
            
            # Count parameters
            param_count = len([p.strip() for p in params.split(',') if p.strip() and not p.strip().startswith('*')])
            
            functions.append({
                "name": func_name,
                "parameters": param_count,
                "complexity": 1.0  # Simplified
            })
        
        return functions
    
    @staticmethod
    def get_class_metrics(code: str) -> List[Dict[str, Any]]:
        """
        Extract metrics for individual classes.
        
        Args:
            code: Python code
            
        Returns:
            List of dicts with class metrics
        """
        classes = []
        
        class_pattern = r'^\s*class\s+(\w+)(?:\((.*?)\))?:'
        
        for match in re.finditer(class_pattern, code, re.MULTILINE):
            class_name = match.group(1)
            base_classes = match.group(2) or ""
            
            # Count inherited classes
            base_count = len([b.strip() for b in base_classes.split(',') if b.strip()])
            
            classes.append({
                "name": class_name,
                "base_classes": base_count,
                "complexity": 1.0  # Simplified
            })
        
        return classes


class MetricsComparison:
    """Compare metrics between two code versions."""
    
    @staticmethod
    def compare(before: str, after: str) -> Dict[str, Any]:
        """
        Compare metrics before and after refactoring.
        
        Args:
            before: Original code
            after: Refactored code
            
        Returns:
            Dict with comparison results
        """
        before_metrics = MetricsCalculator.calculate(before)
        after_metrics = MetricsCalculator.calculate(after)
        
        def calc_change(before_val: float, after_val: float) -> float:
            """Calculate percentage change."""
            if before_val == 0:
                return 0.0
            return ((after_val - before_val) / before_val) * 100
        
        return {
            "before": {
                "lines_of_code": before_metrics.lines_of_code,
                "functions": before_metrics.function_count,
                "classes": before_metrics.class_count,
                "complexity": before_metrics.cyclomatic_complexity,
                "maintainability": before_metrics.maintainability_index
            },
            "after": {
                "lines_of_code": after_metrics.lines_of_code,
                "functions": after_metrics.function_count,
                "classes": after_metrics.class_count,
                "complexity": after_metrics.cyclomatic_complexity,
                "maintainability": after_metrics.maintainability_index
            },
            "changes": {
                "loc_change_percent": calc_change(before_metrics.lines_of_code, after_metrics.lines_of_code),
                "complexity_change_percent": calc_change(before_metrics.cyclomatic_complexity, after_metrics.cyclomatic_complexity),
                "maintainability_change_percent": calc_change(before_metrics.maintainability_index, after_metrics.maintainability_index),
                "improved": after_metrics.maintainability_index > before_metrics.maintainability_index
            }
        }
