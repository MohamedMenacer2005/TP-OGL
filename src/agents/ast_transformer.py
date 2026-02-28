"""
AST Transformation Utilities for code refactoring.
"""

import ast
import re
from typing import Tuple


class ASTTransformer:
    """Utility class for AST-based code transformations."""
    
    @staticmethod
    def fix_bare_except(code: str) -> Tuple[str, bool]:
        """
        Fix bare except clauses using AST transformation.
        
        Args:
            code: Python code to fix
            
        Returns:
            Tuple of (fixed_code, was_changed)
        """
        try:
            tree = ast.parse(code)
            changed = False
            
            class BareExceptFixer(ast.NodeTransformer):
                def visit_ExceptHandler(self, node):
                    nonlocal changed
                    if node.type is None:
                        # Transform bare except to except Exception
                        changed = True
                        node.type = ast.Name(id='Exception', ctx=ast.Load())
                        if node.name is None:
                            node.name = 'e'
                    return node
            
            fixer = BareExceptFixer()
            new_tree = fixer.visit(tree)
            
            if changed:
                ast.fix_missing_locations(new_tree)
                return ast.unparse(new_tree), True
            
            return code, False
        except SyntaxError:
            # If parsing fails, fall back to regex replacement
            pattern = r'except\s*:'
            replacement = r'except Exception as e:'
            new_code = re.sub(pattern, replacement, code)
            return new_code, new_code != code
    
    @staticmethod
    def replace_print_with_logging(code: str) -> Tuple[str, bool]:
        """
        Replace print statements with logging calls.
        
        Args:
            code: Python code to fix
            
        Returns:
            Tuple of (fixed_code, was_changed)
        """
        try:
            tree = ast.parse(code)
            changed = False
            needs_logging_import = False
            has_logging_import = False
            
            # Check for existing logging import
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if 'logging' in alias.name:
                                has_logging_import = True
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and 'logging' in node.module:
                            has_logging_import = True
            
            class PrintReplacer(ast.NodeTransformer):
                def visit_Expr(self, node):
                    nonlocal changed, needs_logging_import
                    
                    if isinstance(node.value, ast.Call):
                        if isinstance(node.value.func, ast.Name):
                            if node.value.func.id == 'print':
                                changed = True
                                needs_logging_import = True
                                
                                # Transform print(x) to logging.debug(x)
                                node.value.func = ast.Attribute(
                                    value=ast.Name(id='logging', ctx=ast.Load()),
                                    attr='debug',
                                    ctx=ast.Load()
                                )
                    
                    return node
            
            replacer = PrintReplacer()
            new_tree = replacer.visit(tree)
            
            if changed:
                # Add logging import if needed and not present
                if needs_logging_import and not has_logging_import:
                    import_node = ast.Import(names=[ast.alias(name='logging', asname=None)])
                    new_tree.body.insert(0, import_node)
                
                ast.fix_missing_locations(new_tree)
                return ast.unparse(new_tree), True
            
            return code, False
        except SyntaxError:
            # Fallback to simple string replacement
            if 'import logging' not in code:
                code = 'import logging\n\n' + code
            new_code = re.sub(r'\bprint\(', 'logging.debug(', code)
            return new_code, new_code != code
    
    @staticmethod
    def add_type_hints_skeleton(code: str, function_name: str) -> Tuple[str, bool]:
        """
        Add basic type hint skeleton to a function.
        
        Args:
            code: Python code
            function_name: Name of function to add hints to
            
        Returns:
            Tuple of (fixed_code, was_changed)
        """
        try:
            tree = ast.parse(code)
            changed = False
            
            class TypeHintAdder(ast.NodeTransformer):
                def visit_FunctionDef(self, node):
                    nonlocal changed
                    
                    if node.name == function_name:
                        # Only add hints if none exist
                        if node.returns is None:
                            changed = True
                            # Add Any as return type hint
                            node.returns = ast.Name(id='Any', ctx=ast.Load())
                        
                        # Add Any to arguments without annotations
                        for arg in node.args.args:
                            if arg.annotation is None:
                                changed = True
                                arg.annotation = ast.Name(id='Any', ctx=ast.Load())
                    
                    return node
            
            adder = TypeHintAdder()
            new_tree = adder.visit(tree)
            
            if changed:
                ast.fix_missing_locations(new_tree)
                return ast.unparse(new_tree), True
            
            return code, False
        except SyntaxError:
            return code, False
    
    @staticmethod
    def has_bare_except(code: str) -> bool:
        """
        Check if code has bare except clauses.
        
        Args:
            code: Python code to check
            
        Returns:
            True if bare except found
        """
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.ExceptHandler):
                    if node.type is None:
                        return True
            return False
        except SyntaxError:
            return False
    
    @staticmethod
    def has_print_statements(code: str) -> bool:
        """
        Check if code has print statements.
        
        Args:
            code: Python code to check
            
        Returns:
            True if print statements found (and logging not imported)
        """
        try:
            tree = ast.parse(code)
            
            # Check for logging import
            has_logging = False
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if 'logging' in alias.name:
                                has_logging = True
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and 'logging' in node.module:
                            has_logging = True
            
            if has_logging:
                return False
            
            # Check for print calls
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id == 'print':
                            return True
            return False
        except SyntaxError:
            return False
    
    @staticmethod
    def get_function_complexities(code: str) -> list:
        """
        Get complexity metrics for all functions in code.
        
        Args:
            code: Python code to analyze
            
        Returns:
            List of (function_name, line_count) tuples
        """
        try:
            tree = ast.parse(code)
            complexities = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Count lines in function
                    start_line = node.lineno
                    end_line = node.end_lineno or start_line
                    line_count = end_line - start_line
                    complexities.append((node.name, line_count))
            
            return complexities
        except SyntaxError:
            return []
    
    @staticmethod
    def has_todo_comments(code: str) -> bool:
        """
        Check if code has TODO comments.
        
        Args:
            code: Python code to check
            
        Returns:
            True if TODO comments found
        """
        return '# TODO' in code or '#TODO' in code
