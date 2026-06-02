import re
from pathlib import Path

from codec.tools.registry import register_tool


@register_tool("grep_search", "Search file contents using a regex pattern")
async def grep_search(pattern: str, include: str = "*", path: str = ".", project_dir: str = ".") -> str:
    base = Path(project_dir).resolve()
    search_path = base / path if path != "." else base
    if not search_path.exists():
        return f"Error: path not found: {path}"

    try:
        regex = re.compile(pattern, re.IGNORECASE)
    except re.error as e:
        return f"Error in regex pattern: {e}"

    results = []
    try:
        for f in search_path.rglob(include):
            if f.is_file():
                try:
                    content = f.read_text(encoding="utf-8", errors="replace")
                    content = content.replace("\ufffd", "?")
                    for i, line in enumerate(content.split("\n"), 1):
                        if regex.search(line):
                            rel = f.relative_to(base)
                            results.append(f"{rel}:{i}: {line.strip()[:200]}")
                except (PermissionError, OSError):
                    continue
    except Exception as e:
        return f"Error during search: {e}"

    if not results:
        return f"No matches found for pattern '{pattern}'"

    max_results = 100
    if len(results) > max_results:
        results = results[:max_results]
        results.append(f"... ({len(results)} more results not shown)")

    return "\n".join(results)


@register_tool("glob_files", "Find files by glob pattern")
async def glob_files(pattern: str, path: str = ".", project_dir: str = ".") -> str:
    base = Path(project_dir).resolve()
    search_path = base / path if path != "." else base
    if not search_path.exists():
        return f"Error: path not found: {path}"

    try:
        matches = list(search_path.rglob(pattern))
    except Exception as e:
        return f"Error during glob: {e}"

    if not matches:
        return f"No files matching '{pattern}'"

    max_results = 100
    if len(matches) > max_results:
        matches = matches[:max_results]

    result = []
    for m in sorted(matches):
        rel = m.relative_to(base)
        suffix = "/" if m.is_dir() else ""
        result.append(f"  {rel}{suffix}")

    output = "\n".join(result)
    if len(matches) > max_results:
        output += f"\n... ({len(matches)} total matches, showing first {max_results})"
    return output
