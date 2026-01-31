"""
Code Diff Utility
Compare before/after refactoring and generate diff statistics.
Toolsmith tool for analyzing code changes.
"""

import difflib
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class DiffStats:
    """Statistics about code changes."""
    additions: int = 0
    deletions: int = 0
    modifications: int = 0
    total_changes: int = 0
    similarity_ratio: float = 0.0  # 0.0 to 1.0
    lines_added: List[str] = None
    lines_removed: List[str] = None
    lines_modified: List[Tuple[str, str]] = None
    
    def __post_init__(self):
        if self.lines_added is None:
            self.lines_added = []
        if self.lines_removed is None:
            self.lines_removed = []
        if self.lines_modified is None:
            self.lines_modified = []


class CodeDiff:
    """Utilities for comparing code versions."""
    
    @staticmethod
    def compare_code(before: str, after: str) -> DiffStats:
        """
        Compare two code versions and generate diff statistics.
        
        Args:
            before: Original code
            after: Refactored code
            
        Returns:
            DiffStats object with comparison results
        """
        before_lines = before.splitlines(keepends=False)
        after_lines = after.splitlines(keepends=False)
        
        # Use difflib for detailed comparison
        diff = difflib.unified_diff(before_lines, after_lines, lineterm='')
        diff_list = list(diff)
        
        # Calculate statistics
        additions = sum(1 for line in diff_list if line.startswith('+') and not line.startswith('+++'))
        deletions = sum(1 for line in diff_list if line.startswith('-') and not line.startswith('---'))
        
        # Extract actual changes
        added_lines = [line[1:] for line in diff_list if line.startswith('+') and not line.startswith('+++')]
        removed_lines = [line[1:] for line in diff_list if line.startswith('-') and not line.startswith('---')]
        
        # Calculate similarity ratio (0.0 to 1.0)
        matcher = difflib.SequenceMatcher(None, before, after)
        similarity = matcher.ratio()
        
        stats = DiffStats(
            additions=additions,
            deletions=deletions,
            modifications=min(additions, deletions),  # Rough estimate
            total_changes=additions + deletions,
            similarity_ratio=similarity,
            lines_added=added_lines,
            lines_removed=removed_lines
        )
        
        return stats
    
    @staticmethod
    def compare_files(before_file: str, after_file: str) -> DiffStats:
        """
        Compare two code files.
        
        Args:
            before_file: Path to original file
            after_file: Path to refactored file
            
        Returns:
            DiffStats object
        """
        try:
            with open(before_file, 'r', encoding='utf-8') as f:
                before = f.read()
            with open(after_file, 'r', encoding='utf-8') as f:
                after = f.read()
            return CodeDiff.compare_code(before, after)
        except IOError as e:
            raise IOError(f"Error reading files: {e}")
    
    @staticmethod
    def generate_patch(before: str, after: str, filename: str = "code") -> str:
        """
        Generate unified diff patch format.
        
        Args:
            before: Original code
            after: Refactored code
            filename: Filename for patch header
            
        Returns:
            Unified diff format string
        """
        before_lines = before.splitlines(keepends=True)
        after_lines = after.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            before_lines,
            after_lines,
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
            lineterm=''
        )
        
        return ''.join(diff)
    
    @staticmethod
    def get_changed_functions(before: str, after: str) -> Dict[str, str]:
        """
        Identify which functions changed between versions.
        
        Args:
            before: Original code
            after: Refactored code
            
        Returns:
            Dict mapping function names to their status: "added", "removed", "modified"
        """
        def extract_functions(code: str) -> Dict[str, int]:
            """Extract function definitions and their line hashes."""
            functions = {}
            for i, line in enumerate(code.splitlines()):
                if line.strip().startswith("def "):
                    func_name = line.split("def ")[1].split("(")[0]
                    functions[func_name] = hash(line)
            return functions
        
        before_funcs = extract_functions(before)
        after_funcs = extract_functions(after)
        
        changes = {}
        
        # Find added/removed
        for func in before_funcs:
            if func not in after_funcs:
                changes[func] = "removed"
            elif before_funcs[func] != after_funcs[func]:
                changes[func] = "modified"
        
        for func in after_funcs:
            if func not in before_funcs:
                changes[func] = "added"
        
        return changes


class LineDiffAnalyzer:
    """Analyze line-by-line differences."""
    
    @staticmethod
    def get_colored_diff(before: str, after: str) -> List[Dict]:
        """
        Generate side-by-side diff with coloring hints.
        
        Args:
            before: Original code
            after: Refactored code
            
        Returns:
            List of dicts with line comparison data
        """
        before_lines = before.splitlines()
        after_lines = after.splitlines()
        
        differ = difflib.Differ()
        diff_result = list(differ.compare(before_lines, after_lines))
        
        changes = []
        for line in diff_result:
            if line.startswith('- '):
                changes.append({"type": "removed", "line": line[2:]})
            elif line.startswith('+ '):
                changes.append({"type": "added", "line": line[2:]})
            elif line.startswith('? '):
                changes.append({"type": "hint", "line": line[2:]})
            elif line.startswith('  '):
                changes.append({"type": "unchanged", "line": line[2:]})
        
        return changes
