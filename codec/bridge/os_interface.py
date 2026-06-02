from __future__ import annotations

import os
import sys
import platform
from pathlib import Path
from typing import Any


class OSInterface:
    def __init__(self, project_dir: str):
        self._project_dir = Path(project_dir).resolve()

    def info(self) -> dict[str, Any]:
        return {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "python_version": sys.version,
            "cwd": str(Path.cwd()),
            "project_dir": str(self._project_dir),
            "home": str(Path.home()),
            "env_keys": list(os.environ.keys()),
            "pathsep": os.pathsep,
            "sep": os.sep,
            "cpu_count": os.cpu_count(),
            "pid": os.getpid(),
        }

    def env(self, key: str, default: str | None = None) -> str | None:
        return os.environ.get(key, default)

    def is_terminal(self) -> bool:
        return sys.stdin.isatty()

    def terminal_width(self) -> int:
        try:
            import shutil
            return shutil.get_terminal_size().columns
        except Exception:
            return 80

    def resolve_path(self, path: str) -> str:
        p = Path(path)
        if p.is_absolute():
            return str(p.resolve())
        return str((self._project_dir / p).resolve())

    def path_exists(self, path: str) -> bool:
        return Path(self.resolve_path(path)).exists()

    def is_file(self, path: str) -> bool:
        return Path(self.resolve_path(path)).is_file()

    def is_dir(self, path: str) -> bool:
        return Path(self.resolve_path(path)).is_dir()

    def list_dir(self, path: str = ".") -> list[str]:
        p = Path(self.resolve_path(path))
        if not p.is_dir():
            return []
        return sorted(str(x.name) for x in p.iterdir())

    def get_files_by_extension(self, ext: str, path: str = ".") -> list[str]:
        p = Path(self.resolve_path(path))
        if not p.is_dir():
            return []
        return sorted(str(x.relative_to(self._project_dir))
                      for x in p.rglob(f"*.{ext.lstrip('.')}") if x.is_file())

    def detect_project_type(self) -> dict[str, Any]:
        info = {}
        if (self._project_dir / "package.json").exists():
            import json
            try:
                pkg = json.loads((self._project_dir / "package.json").read_text())
                info["type"] = "node"
                info["scripts"] = list(pkg.get("scripts", {}).keys())
                info["deps"] = len(pkg.get("dependencies", {}))
                info["dev_deps"] = len(pkg.get("devDependencies", {}))
            except Exception:
                info["type"] = "node"
        elif (self._project_dir / "Cargo.toml").exists():
            info["type"] = "rust"
        elif (self._project_dir / "pyproject.toml").exists():
            info["type"] = "python"
        elif (self._project_dir / "requirements.txt").exists():
            info["type"] = "python"
        elif (self._project_dir / "go.mod").exists():
            info["type"] = "go"
        elif (self._project_dir / "Gemfile").exists():
            info["type"] = "ruby"
        elif list(self._project_dir.glob("*.sln")):
            info["type"] = "dotnet"
        elif list(self._project_dir.glob("*.csproj")):
            info["type"] = "dotnet"
        else:
            info["type"] = "unknown"
        return info
