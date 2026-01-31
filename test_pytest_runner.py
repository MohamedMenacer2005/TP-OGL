from src.utils.pytest_runner import PytestRunner

runner = PytestRunner("./sandbox")
result = runner.run_tests()

print(f"Passed: {result['passed']}")
print(f"Failed: {result['failed']}")
print(f"Errors: {result['errors']}")
print(f"Raw output (last 300 chars):")
print(result['raw_output'][-300:] if result['raw_output'] else "Empty")
