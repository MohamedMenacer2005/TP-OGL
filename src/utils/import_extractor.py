"""
Import Extractor Utility
Analyze Python imports and dependencies.
Toolsmith tool for dependency analysis.
"""

import re
from typing import Dict, List, Set, Tuple
from collections import defaultdict


class ImportExtractor:
    """Extract and analyze Python imports."""
    
    @staticmethod
    def extract_imports(code: str) -> Dict[str, List[str]]:
        """
        Extract all imports from Python code.
        
        Args:
            code: Python code
            
        Returns:
            Dict with keys: "absolute", "relative", "from_imports"
        """
        imports = {
            "absolute": [],      # import os
            "relative": [],      # from . import foo
            "from_imports": [],  # from module import name
            "all_modules": set()
        }
        
        lines = code.splitlines()
        
        for line in lines:
            # Skip comments
            if line.strip().startswith('#'):
                continue
            
            # Handle continuation lines
            if '\\' in line:
                continue
            
            # Match: import module
            abs_match = re.match(r'^\s*import\s+([\w\s.,]+)', line)
            if abs_match:
                modules = [m.strip().split(' as ')[0] for m in abs_match.group(1).split(',')]
                imports["absolute"].extend(modules)
                imports["all_modules"].update(modules)
            
            # Match: from module import name
            from_match = re.match(r'^\s*from\s+([\w.]+)\s+import\s+([\w\s,*]+)', line)
            if from_match:
                module = from_match.group(1)
                names = from_match.group(2)
                imports["from_imports"].append({"module": module, "names": names})
                
                # Extract module name (before first dot)
                root_module = module.split('.')[0]
                imports["all_modules"].add(root_module)
            
            # Match: relative imports
            rel_match = re.match(r'^\s*from\s+(\.+[\w.]*)\s+import', line)
            if rel_match:
                imports["relative"].append(line.strip())
        
        # Convert set to list for serialization
        imports["all_modules"] = sorted(list(imports["all_modules"]))
        
        return imports
    
    @staticmethod
    def categorize_imports(imports: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """
        Categorize imports into standard library, third-party, local.
        
        Args:
            imports: Output from extract_imports()
            
        Returns:
            Dict with keys: "stdlib", "third_party", "local"
        """
        stdlib_modules = {
            'os', 'sys', 're', 'json', 'csv', 'math', 'random', 'datetime',
            'collections', 'itertools', 'functools', 'operator', 'pathlib',
            'tempfile', 'shutil', 'glob', 'subprocess', 'threading', 'multiprocessing',
            'queue', 'socket', 'urllib', 'http', 'email', 'smtplib', 'ssl',
            'hashlib', 'hmac', 'secrets', 'unittest', 'pytest', 'logging',
            'argparse', 'getpass', 'configparser', 'codecs', 'io', 'pickle',
            'shelve', 'sqlite3', 'decimal', 'fractions', 'statistics',
            'enum', 'dataclasses', 'typing', 'abc', 'atexit', 'traceback'
        }
        
        categorized = {
            "stdlib": [],
            "third_party": [],
            "local": []
        }
        
        for module in imports.get("all_modules", []):
            root = module.split('.')[0]
            if root in stdlib_modules:
                categorized["stdlib"].append(module)
            elif root.startswith('.'):
                categorized["local"].append(module)
            else:
                categorized["third_party"].append(module)
        
        return categorized
    
    @staticmethod
    def find_unused_imports(code: str) -> List[str]:
        """
        Detect potentially unused imports (simple heuristic).
        
        Args:
            code: Python code
            
        Returns:
            List of potentially unused import names
        """
        imports_dict = ImportExtractor.extract_imports(code)
        unused = []
        
        # Extract all imported names
        imported_names = set()
        for imp in imports_dict["absolute"]:
            imported_names.add(imp.split('.')[0])
        
        for item in imports_dict["from_imports"]:
            names = item["names"].split(',')
            for name in names:
                clean_name = name.strip().split(' as ')[-1]
                if clean_name != '*':
                    imported_names.add(clean_name)
        
        # Remove import statements and comments from code
        lines_to_check = []
        for line in code.splitlines():
            if not line.strip().startswith('import ') and \
               not line.strip().startswith('from '):
                lines_to_check.append(line)
        
        code_without_imports = '\n'.join(lines_to_check)
        
        # Check if each import is used
        for name in imported_names:
            # Check if name appears in code (simple word boundary check)
            pattern = rf'\b{re.escape(name)}\b'
            if not re.search(pattern, code_without_imports):
                unused.append(name)
        
        return unused
    
    @staticmethod
    def find_circular_imports(code_files: Dict[str, str]) -> List[Tuple[str, str]]:
        """
        Detect potential circular import dependencies.
        
        Args:
            code_files: Dict mapping filename -> code content
            
        Returns:
            List of tuples: (file_a, file_b) indicating circular dependency
        """
        # Extract module name from filename
        def get_module_name(filename: str) -> str:
            return filename.replace('.py', '').replace('/', '.')
        
        # Build dependency graph
        dependencies = defaultdict(set)
        
        for filename, code in code_files.items():
            module_name = get_module_name(filename)
            imports = ImportExtractor.extract_imports(code)
            
            for from_import in imports["from_imports"]:
                module = from_import["module"]
                dependencies[module_name].add(module)
        
        # Find cycles (simplified: check bidirectional imports)
        cycles = []
        for module_a, deps_a in dependencies.items():
            for dep_b in deps_a:
                if dep_b in dependencies:
                    if module_a in dependencies[dep_b]:
                        cycle = tuple(sorted([module_a, dep_b]))
                        if cycle not in cycles:
                            cycles.append(cycle)
        
        return cycles


class DependencyGraph:
    """Build and analyze dependency graph."""
    
    def __init__(self):
        """Initialize dependency graph."""
        self.graph = defaultdict(set)
        self.reverse_graph = defaultdict(set)
    
    def add_dependency(self, from_module: str, to_module: str):
        """Add dependency: from_module imports to_module."""
        self.graph[from_module].add(to_module)
        self.reverse_graph[to_module].add(from_module)
    
    def get_dependents(self, module: str) -> Set[str]:
        """Get modules that depend on this module."""
        return self.reverse_graph.get(module, set())
    
    def get_dependencies(self, module: str) -> Set[str]:
        """Get modules this module depends on."""
        return self.graph.get(module, set())
    
    def get_all_modules(self) -> Set[str]:
        """Get all modules in graph."""
        return set(self.graph.keys()) | set(self.reverse_graph.keys())
