"""Quick diagnostic of pytest runner"""
import sys
import subprocess
from pathlib import Path

target_dir = Path("./sandbox")
print(f"Python executable: {sys.executable}")
print(f"Running pytest from: {target_dir}")

result = subprocess.run(
    ["python", "-m", "pytest", str(target_dir), "-v", "--tb=short"],
    capture_output=True,
    text=True,
    timeout=60
)

print("\n=== STDOUT ===")
print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)

print("\n=== STDERR ===")
print(result.stderr[-300:] if len(result.stderr) > 300 else result.stderr)

print(f"\n=== Return code: {result.returncode} ===")
