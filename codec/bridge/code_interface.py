from __future__ import annotations

import re
from pathlib import Path
from typing import Any


class CodeInterface:
    def __init__(self, project_dir: str):
        self._project_dir = Path(project_dir).resolve()

    def detect_language(self, file_path: str) -> str:
        ext = Path(file_path).suffix.lower()
        lang_map = {
            ".py": "python", ".js": "javascript", ".ts": "typescript",
            ".tsx": "typescriptreact", ".jsx": "javascriptreact",
            ".rs": "rust", ".go": "go", ".java": "java",
            ".c": "c", ".h": "c", ".cpp": "cpp", ".hpp": "cpp",
            ".cs": "csharp", ".rb": "ruby", ".php": "php",
            ".swift": "swift", ".kt": "kotlin", ".kts": "kotlin",
            ".scala": "scala", ".r": "r", ".m": "objectivec",
            ".mm": "objectivec", ".sql": "sql", ".sh": "shell",
            ".bash": "shell", ".zsh": "shell", ".fish": "shell",
            ".ps1": "powershell", ".pl": "perl", ".lua": "lua",
            ".hs": "haskell", ".ex": "elixir", ".exs": "elixir",
            ".clj": "clojure", ".cljs": "clojure",
            ".elm": "elm", ".erl": "erlang",
            ".yaml": "yaml", ".yml": "yaml", ".json": "json",
            ".xml": "xml", ".toml": "toml", ".ini": "ini",
            ".cfg": "ini", ".md": "markdown", ".rst": "markdown",
            ".html": "html", ".css": "css", ".scss": "scss",
            ".less": "less", ".sass": "sass",
            ".dockerfile": "dockerfile", "dockerfile": "dockerfile",
            ".tf": "terraform", ".sqlite": "sql",
        }
        name = Path(file_path).name.lower()
        if name == "dockerfile":
            return "dockerfile"
        if name == "makefile":
            return "makefile"
        return lang_map.get(ext, "text")

    def count_lines(self, file_path: str) -> dict[str, int]:
        p = self._resolve(file_path)
        if not p.is_file():
            return {"total": 0, "code": 0, "blank": 0, "comment": 0}
        try:
            lines = p.read_text(encoding="utf-8", errors="replace").split("\n")
        except Exception:
            return {"total": 0, "code": 0, "blank": 0, "comment": 0}
        total = len(lines)
        blank = sum(1 for l in lines if not l.strip())
        comment = sum(1 for l in lines if l.strip().startswith(("#", "//", "/*", "*", "--")))
        return {"total": total, "code": total - blank - comment, "blank": blank, "comment": comment}

    def find_imports(self, file_path: str) -> list[str]:
        p = self._resolve(file_path)
        if not p.is_file():
            return []
        lang = self.detect_language(file_path)
        try:
            content = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return []
        patterns = {
            "python": [r"^import\s+(\S+)", r"^from\s+(\S+)\s+import"],
            "javascript": [r"(?:import|require)\s*\(?['\"]([^'\"]+)['\"]"],
            "typescript": [r"(?:import|require)\s*\(?['\"]([^'\"]+)['\"]"],
            "go": [r'^import\s+"(.+)"', r'^import\s+\(([^)]+)\)'],
            "rust": [r"^use\s+([^;]+)"],
            "java": [r"^import\s+([^;]+)"],
            "c": [r'#include\s+[<"]([^>"]+)[>"]'],
            "cpp": [r'#include\s+[<"]([^>"]+)[>"]'],
        }
        result = []
        for pat in patterns.get(lang, []):
            result.extend(m.group(1) for m in re.finditer(pat, content, re.MULTILINE))
        return sorted(set(result))

    def find_functions(self, file_path: str) -> list[dict[str, Any]]:
        p = self._resolve(file_path)
        if not p.is_file():
            return []
        lang = self.detect_language(file_path)
        try:
            content = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return []
        patterns = {
            "python": [(r"^def\s+(\w+)\s*\(", "def"), (r"^async\s+def\s+(\w+)\s*\(", "async def"),
                       (r"^class\s+(\w+)", "class")],
            "javascript": [(r"(?:function\s+(\w+)|(\w+)\s*=\s*(?:async\s*)?\()", "function"),
                           (r"^class\s+(\w+)", "class")],
            "typescript": [(r"(?:function\s+(\w+)|(\w+)\s*=\s*(?:async\s*)?\()", "function"),
                           (r"^class\s+(\w+)", "class")],
        }
        result = []
        for pat, kind in patterns.get(lang, []):
            for m in re.finditer(pat, content, re.MULTILINE):
                name = m.group(1) or m.group(2) or "anonymous"
                line = content[:m.start()].count("\n") + 1
                result.append({"name": name, "kind": kind, "line": line})
        return result

    def summarize_project(self) -> dict[str, Any]:
        files = list(self._project_dir.rglob("*"))
        source_files = [f for f in files if f.is_file()
                        and self.detect_language(str(f)) != "text"
                        and ".git" not in str(f)
                        and "__pycache__" not in str(f)
                        and ".codec" not in str(f)]
        by_lang: dict[str, int] = {}
        total_lines = 0
        for f in source_files:
            lang = self.detect_language(str(f))
            by_lang[lang] = by_lang.get(lang, 0) + 1
            try:
                total_lines += len(f.read_text(encoding="utf-8", errors="replace").split("\n"))
            except Exception:
                pass
        return {
            "total_files": len(source_files),
            "total_lines": total_lines,
            "languages": dict(sorted(by_lang.items(), key=lambda x: -x[1])),
        }

    def _resolve(self, path: str) -> Path:
        p = Path(path)
        if p.is_absolute():
            return p
        return (self._project_dir / p).resolve()
