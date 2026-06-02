from __future__ import annotations

import difflib
from pathlib import Path
from typing import Any


class DiffEngine:
    def __init__(self, project_dir: str):
        self._project_dir = Path(project_dir).resolve()

    def compute_edit_diff(self, file_path: str, old_string: str, new_string: str) -> str:
        p = self._resolve(file_path)
        old_lines = old_string.splitlines(keepends=True)
        new_lines = new_string.splitlines(keepends=True)
        diff = difflib.unified_diff(
            old_lines, new_lines,
            fromfile=str(p), tofile=str(p),
            lineterm="",
        )
        return "\n".join(diff)

    def compute_file_diff(self, file_path: str, after_content: str) -> str:
        p = self._resolve(file_path)
        if not p.exists():
            return f"(new file) {file_path}\n{after_content}"
        before = p.read_text(encoding="utf-8", errors="replace")
        return self.compute_edit_diff(file_path, before, after_content)

    def compute_file_diff_before_after(self, file_path: str, new_content: str) -> dict[str, Any]:
        p = self._resolve(file_path)
        old_content = p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""
        diff = self.compute_edit_diff(file_path, old_content, new_content)
        return {
            "file": file_path,
            "before": old_content,
            "after": new_content,
            "diff": diff,
            "lines_added": sum(1 for l in diff.split("\n") if l.startswith("+") and not l.startswith("+++")),
            "lines_removed": sum(1 for l in diff.split("\n") if l.startswith("-") and not l.startswith("---")),
        }

    def format_diff(self, diff: str) -> str:
        lines = diff.split("\n")
        result = []
        for line in lines[:100]:
            if line.startswith("+") and not line.startswith("+++"):
                result.append(f"  [green]+{line[1:]}[/green]")
            elif line.startswith("-") and not line.startswith("---"):
                result.append(f"  [red]-{line[1:]}[/red]")
            elif line.startswith("@@"):
                result.append(f"  [cyan]{line}[/cyan]")
            else:
                result.append(f"  {line}")
        if len(lines) > 100:
            result.append(f"  ... ({len(lines)} total diff lines)")
        return "\n".join(result)

    def _resolve(self, path: str) -> Path:
        p = Path(path)
        if p.is_absolute():
            return p
        return (self._project_dir / p).resolve()
