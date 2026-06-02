from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any


BLOCKED_SHELL_PATTERNS: list[re.Pattern] = [
    re.compile(r"rm\s+(-rf?\s+)?[/~]"),
    re.compile(r"sudo\s+"),
    re.compile(r"chmod\s+777"),
    re.compile(r"dd\s+if="),
    re.compile(r":\(\)\s*\{"),
    re.compile(r">\s*/dev/"),
    re.compile(r"mkfs\."),
    re.compile(r"fdisk"),
    re.compile(r"dd\s"),
    re.compile(r"shutdown"),
    re.compile(r"reboot"),
    re.compile(r"init\s"),
    re.compile(r"poweroff"),
    re.compile(r"halt"),
    re.compile(r">\s*/proc/"),
]

ALLOWED_SHELL_PREFIXES: list[str] = [
    "python", "pip", "npm", "npx", "yarn", "node", "cargo", "go",
    "rustc", "gcc", "clang", "make", "cmake", "git", "docker",
    "ls", "cat", "head", "tail", "wc", "sort", "uniq", "echo",
    "grep", "find", "rg", "ag", "ack", "sed", "awk",
    "pwd", "whoami", "date", "env", "which", "type",
    "cd", "mkdir", "touch", "cp", "mv",
    "ps", "top", "htop", "df", "du", "free",
    "curl", "wget", "ping", "nslookup",
    "pytest", "ruff", "black", "mypy", "isort", "flake8",
    "cargo", "dotnet", "gradle", "mvn",
]


class SessionGuardian:
    def __init__(self, project_dir: str, log=None):
        self._project_root = Path(project_dir).resolve()
        self._sandbox_paths: list[Path] = [self._project_root]
        self._allow_list = list(ALLOWED_SHELL_PREFIXES)
        self._block_patterns = list(BLOCKED_SHELL_PATTERNS)
        self._interactive = False
        self.log = log

    def set_interactive(self, value: bool):
        self._interactive = value

    def add_sandbox(self, path: str):
        p = Path(path).resolve()
        if p.exists():
            self._sandbox_paths.append(p)

    def allow_command(self, command: str) -> str | None:
        cmd_lower = command.strip().lower()

        for pat in self._block_patterns:
            if pat.search(cmd_lower):
                return f"Blocked by security policy: command matches dangerous pattern '{pat.pattern}'"

        first_word = cmd_lower.split()[0] if cmd_lower.split() else ""
        if first_word in ("sudo", "su", "doas"):
            return "Privilege escalation commands are blocked"

        return None

    def contain_path(self, path: str) -> str:
        p = Path(path)
        if p.is_absolute():
            resolved = p.resolve()
        else:
            resolved = (self._project_root / p).resolve()

        for sandbox in self._sandbox_paths:
            try:
                resolved.relative_to(sandbox)
                return str(resolved)
            except ValueError:
                continue

        contained = self._project_root / resolved.name
        if self.log:
            self.log.warn(f"Path containment: {path} -> {contained}")
        return str(contained.resolve())

    def is_path_allowed(self, path: str) -> bool:
        p = Path(path)
        if p.is_absolute():
            resolved = p.resolve()
        else:
            resolved = (self._project_root / p).resolve()
        for sandbox in self._sandbox_paths:
            try:
                resolved.relative_to(sandbox)
                return True
            except ValueError:
                continue
        return False

    def describe_restrictions(self) -> str:
        return (
            f"Sandbox root: {self._project_root}\n"
            f"Shell commands: {len(self._allow_list)} in allow list, "
            f"{len(self._block_patterns)} blocked patterns\n"
            f"File operations confined to: {', '.join(str(s) for s in self._sandbox_paths)}"
        )
