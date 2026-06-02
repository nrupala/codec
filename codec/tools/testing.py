import os
from pathlib import Path

from codec.tools.registry import register_tool


def _detect_test_command(project_dir: str) -> str | None:
    root = Path(project_dir).resolve()
    has_pyproject = (root / "pyproject.toml").exists()
    has_cargo = (root / "Cargo.toml").exists()
    has_package = (root / "package.json").exists()
    has_gradle = (root / "build.gradle").exists() or (root / "build.gradle.kts").exists()
    has_makefile = (root / "Makefile").exists()
    has_justfile = (root / "justfile").exists()

    if has_pyproject:
        return "python -m pytest"
    if has_cargo:
        return "cargo test"
    if has_package:
        return "npm test 2>&1" if os.name == "nt" else "npm test"
    if has_gradle:
        return "./gradlew test" if os.name != "nt" else "gradlew.bat test"
    if has_makefile:
        return "make test"
    if (root / "tests").is_dir() or list(root.glob("test_*.py")) or list(root.glob("*_test.py")):
        return "python -m pytest"
    return None


@register_tool("run_tests", "Auto-detect and run tests for the project. Returns test output.")
async def run_tests(command: str = "", project_dir: str = "."):
    from codec.tools.shell import run_shell

    cmd = command or _detect_test_command(project_dir) or ""
    if not cmd:
        return "No test command detected. Specify one with command= parameter."

    os.chdir(project_dir)
    return await run_shell(cmd)


@register_tool("detect_test_command", "Detect what test runner is configured for this project")
async def detect_test_command(project_dir: str = "."):
    cmd = _detect_test_command(project_dir)
    if cmd:
        return f"Detected: {cmd}"
    return "No test command detected."
