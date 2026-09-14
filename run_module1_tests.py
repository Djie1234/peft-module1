"""One-click PyCharm entry point for the Module 1 automated test suite."""

from pathlib import Path
import subprocess
import sys


def main():
    project_root = Path(__file__).resolve().parent
    result_dir = project_root / "test-results"
    result_dir.mkdir(exist_ok=True)

    command = [
        sys.executable,
        "-B",
        "-m",
        "pytest",
        "tests_module1",
        "peft/test",
        "-q",
        f"--junitxml={result_dir / 'pytest-results.xml'}",
        "--cov=peft",
        "--cov-report=term-missing",
        f"--cov-report=html:{result_dir / 'coverage'}",
    ]
    completed = subprocess.run(command, cwd=project_root, check=False)
    print(f"\nModule 1 test process finished with exit code {completed.returncode}.")
    print(f"JUnit result: {result_dir / 'pytest-results.xml'}")
    print(f"Coverage report: {result_dir / 'coverage' / 'index.html'}")
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
