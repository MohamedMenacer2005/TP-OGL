# Toolsmith API Contract

This document defines the **internal API** that agents use. Other roles depend on these interfaces—**do not change signatures without coordination**.

## Code Reader API

**Module**: `src.utils.code_reader`

### `CodeReader(target_dir: str)`
Constructor. Raises `ValueError` if target_dir doesn't exist.

```python
from src.utils.code_reader import CodeReader, SandboxSecurityError

reader = CodeReader("./sandbox")
```

### `read_all_python_files() -> Dict[str, str]`
Returns all `.py` files in target_dir.

```python
files = reader.read_all_python_files()
# {'example.py': 'def hello():\n    pass', 'utils/helper.py': '...'}
```

### `read_file(relative_path: str) -> str`
Read specific file. **Security**: Raises `SandboxSecurityError` if path escapes sandbox.

```python
content = reader.read_file("example.py")
# Raises SandboxSecurityError if trying to access "../outside.py"
```

### `write_file(relative_path: str, content: str) -> None`
Write to file in sandbox. **Security**: Raises `SandboxSecurityError` if path escapes sandbox.

```python
reader.write_file("refactored.py", "def improved(): pass")
```

### `list_python_files() -> List[str]`
Get sorted list of all `.py` files.

```python
files = reader.list_python_files()
# ['example.py', 'utils/helper.py']
```

---

## Pylint Runner API

**Module**: `src.utils.pylint_runner`

### `PylintRunner(target_dir: str)`
Constructor.

```python
from src.utils.pylint_runner import PylintRunner

runner = PylintRunner("./sandbox")
```

### `run_pylint(relative_path: str) -> Dict`
Run pylint on single file.

```python
result = runner.run_pylint("example.py")
# {
#   "success": True,
#   "score": 7.5,
#   "messages": [...],  # List of issues
#   "raw_output": "..."
# }
```

### `run_on_directory(py_files: List[str]) -> Dict[str, Dict]`
Run pylint on multiple files.

```python
results = runner.run_on_directory(["example.py", "utils/helper.py"])
# {'example.py': {...}, 'utils/helper.py': {...}}
```

### `summarize_results(results: Dict) -> Dict`
Aggregate results across files.

```python
summary = runner.summarize_results(results)
# {
#   "avg_score": 6.5,
#   "min_score": 5.0,
#   "max_score": 8.0,
#   "total_issues": 23,
#   "files_analyzed": 2,
#   "files_failed": 0
# }
```

---

## Pytest Runner API

**Module**: `src.utils.pytest_runner`

### `PytestRunner(target_dir: str)`
Constructor.

```python
from src.utils.pytest_runner import PytestRunner

runner = PytestRunner("./sandbox")
```

### `run_tests(test_file: str = None) -> Dict`
Run pytest on target code.

```python
results = runner.run_tests()  # All tests
# or
results = runner.run_tests("tests/test_example.py")  # Specific test file

# {
#   "success": True,
#   "passed": 10,
#   "failed": 2,
#   "errors": 0,
#   "messages": [...],
#   "raw_output": "..."
# }
```

### `summarize_results(test_results: Dict) -> Dict`
Create test summary.

```python
summary = runner.summarize_results(results)
# {
#   "total_tests": 12,
#   "passed": 10,
#   "failed": 2,
#   "errors": 0,
#   "pass_rate": 83.33,
#   "success": False
# }
```

---

## Base Agent API

**Module**: `src.agents.base_agent`

### `BaseAgent(agent_name: str, model: str)`
Abstract base class for agents. Subclass this to create new agents.

```python
from src.agents.base_agent import BaseAgent
from src.utils.logger import ActionType

class MyAgent(BaseAgent):
    def analyze(self, code: str, filename: str = "unknown.py") -> dict:
        # Implement your analysis logic
        pass
    
    def execute(self, target_dir: str) -> dict:
        # Implement your execution logic
        pass
```

### `_log_action(action, prompt, response, extra_details=None, status="SUCCESS")`
Automatically log agent action with prompt/response.

```python
self._log_action(
    action=ActionType.ANALYSIS,
    prompt="Analyze this code...",
    response="I found these issues...",
    extra_details={"filename": "example.py", "issues_count": 3}
)
```

---

## Security Guarantees

✅ **Sandbox Enforcement**: `CodeReader` prevents access outside target_dir  
✅ **Path Validation**: All paths resolved to absolute before checking  
✅ **Clear Errors**: `SandboxSecurityError` on violation attempts  

Example security behavior:
```python
reader = CodeReader("./sandbox")

reader.read_file("example.py")           # ✅ OK
reader.read_file("../secret.py")         # ❌ SandboxSecurityError
reader.read_file("../../etc/passwd")     # ❌ SandboxSecurityError
reader.write_file("new_file.py", "...")  # ✅ OK
reader.write_file("../outside.py", "...") # ❌ SandboxSecurityError
```

---

## Code Diff API (Phase 2)

**Module**: `src.utils.code_diff`

### `CodeDiff.compare_code(before: str, after: str) -> DiffStats`
Compare two code versions.

```python
from src.utils.code_diff import CodeDiff

stats = CodeDiff.compare_code(before_code, after_code)
# DiffStats: additions, deletions, modifications, similarity_ratio
```

### `CodeDiff.get_changed_functions(before: str, after: str) -> Dict`
Identify which functions changed.

```python
changes = CodeDiff.get_changed_functions(before, after)
# {'func_name': 'added'|'removed'|'modified', ...}
```

---

## Metrics API (Phase 2)

**Module**: `src.utils.metrics`

### `MetricsCalculator.calculate(code: str) -> CodeMetrics`
Calculate code quality metrics.

```python
from src.utils.metrics import MetricsCalculator

metrics = MetricsCalculator.calculate(code)
# CodeMetrics: lines_of_code, complexity, maintainability_index, etc.
```

### `MetricsComparison.compare(before: str, after: str) -> Dict`
Compare metrics between versions.

```python
comparison = MetricsComparison.compare(before, after)
# {"before": {...}, "after": {...}, "changes": {...}}
```

---

## Import Extractor API (Phase 2)

**Module**: `src.utils.import_extractor`

### `ImportExtractor.extract_imports(code: str) -> Dict`
Extract all imports from code.

```python
from src.utils.import_extractor import ImportExtractor

imports = ImportExtractor.extract_imports(code)
# {"absolute": [...], "from_imports": [...], "all_modules": [...]}
```

### `ImportExtractor.categorize_imports(imports: Dict) -> Dict`
Categorize imports: stdlib, third-party, local.

```python
categories = ImportExtractor.categorize_imports(imports)
# {"stdlib": [...], "third_party": [...], "local": [...]}
```

### `ImportExtractor.find_unused_imports(code: str) -> List`
Detect unused imports.

```python
unused = ImportExtractor.find_unused_imports(code)
# List of import names never used in code
```

---

## Result Aggregator API (Phase 2)

**Module**: `src.utils.result_aggregator`

### `ResultAggregator` & `IterationResult`
Collect agent outputs into structured results.

```python
from src.utils.result_aggregator import ResultAggregator, ResultBuilder

aggregator = ResultAggregator()

# Build iteration result
result = (ResultBuilder(iteration_num=1)
          .with_auditor(output_dict)
          .with_fixer(output_dict)
          .with_judge(output_dict, decision="ACCEPT")
          .build())

aggregator.results.append(result)

# Get summary
summary = aggregator.get_summary()
# {"total_iterations": 1, "accepted": 1, "rejected": 0, ...}
```

---

## API Stability

These APIs are **stable** for Phase 1-2. If you need to change signatures:
1. **Notify all team members immediately**
2. **Update this document**
3. **Provide migration path for dependent code**

Agents depend on these interfaces functioning exactly as documented.

**Note**: Feedback loop orchestration (retry logic, iteration management) is the **Orchestrateur (Lead Dev)** responsibility, not toolsmith. See `src/orchestration/` for execution graph and orchestrator logic.
