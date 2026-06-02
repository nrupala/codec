import os
from pathlib import Path

from codec.tools.registry import register_tool


@register_tool("read_file", "Read the contents of a file at the given path")
async def read_file(path: str, project_dir: str = ".") -> str:
    full_path = _resolve(path, project_dir)
    if not full_path.exists():
        return f"Error: file not found: {path}"
    if not full_path.is_file():
        return f"Error: not a file: {path}"
    try:
        content = full_path.read_text(encoding="utf-8")
        lines = content.split("\n")
        max_lines = 2000
        if len(lines) > max_lines:
            content = "\n".join(lines[:max_lines])
            content += f"\n... (truncated, {len(lines)} total lines, showing first {max_lines})"
        return content
    except Exception as e:
        return f"Error reading file: {e}"


@register_tool("write_file", "Write content to a file at the given path (overwrites existing)")
async def write_file(path: str, content: str, project_dir: str = ".") -> str:
    full_path = _resolve(path, project_dir)
    full_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        full_path.write_text(content, encoding="utf-8")
        return f"Written {len(content)} bytes to {path}"
    except Exception as e:
        return f"Error writing file: {e}"


@register_tool("edit_file", "Edit a file by replacing old_string with new_string")
async def edit_file(path: str, old_string: str, new_string: str, project_dir: str = ".") -> str:
    full_path = _resolve(path, project_dir)
    if not full_path.exists():
        return f"Error: file not found: {path}"
    try:
        content = full_path.read_text(encoding="utf-8")
        if old_string not in content:
            return f"Error: old_string not found in {path}"
        count = content.count(old_string)
        if count > 1:
            return f"Error: found {count} matches for old_string. Provide more context."
        new_content = content.replace(old_string, new_string, 1)
        full_path.write_text(new_content, encoding="utf-8")
        return f"Edited {path}: replaced occurrence of old_string"
    except Exception as e:
        return f"Error editing file: {e}"


@register_tool("list_files", "List files in a directory matching an optional glob pattern")
async def list_files(path: str = ".", pattern: str = "*", project_dir: str = ".") -> str:
    full_path = _resolve(path, project_dir)
    if not full_path.exists():
        return f"Error: directory not found: {path}"
    try:
        files = list(full_path.rglob(pattern))
        if not files:
            return f"No files matching '{pattern}' in {path}"
        result = []
        for f in sorted(files):
            size = f.stat().st_size if f.is_file() else 0
            label = "(dir)" if f.is_dir() else f"({size} bytes)"
            rel = f.relative_to(Path(project_dir).resolve())
            result.append(f"  {rel} {label}")
        return "\n".join(result)
    except Exception as e:
        return f"Error listing files: {e}"


def _resolve(path: str, project_dir: str) -> Path:
    base = Path(project_dir).resolve()
    p = Path(path)
    if p.is_absolute():
        return p
    return (base / p).resolve()
