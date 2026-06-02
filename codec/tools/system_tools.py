from codec.tools.registry import register_tool


@register_tool("project_summary", "Get a summary of the current project: file counts, languages, line counts")
async def project_summary(project_dir: str = "."):
    from codec.bridge.code_interface import CodeInterface
    ci = CodeInterface(project_dir)
    s = ci.summarize_project()
    lines = [f"Files: {s['total_files']}  Lines: {s['total_lines']}"]
    for lang, count in s["languages"].items():
        lines.append(f"  {lang}: {count} files")
    return "\n".join(lines)


@register_tool("detect_language", "Detect the programming language of a file")
async def detect_language(file_path: str, project_dir: str = "."):
    from codec.bridge.code_interface import CodeInterface
    ci = CodeInterface(project_dir)
    return ci.detect_language(file_path)


@register_tool("find_functions", "List all functions/classes defined in a file")
async def find_functions(file_path: str, project_dir: str = "."):
    from codec.bridge.code_interface import CodeInterface
    ci = CodeInterface(project_dir)
    funcs = ci.find_functions(file_path)
    if not funcs:
        return "No functions or classes found."
    return "\n".join(f"  {f['line']:>4} {f['kind']} {f['name']}" for f in funcs)


@register_tool("count_lines", "Count total, code, blank, and comment lines in a file")
async def count_lines(file_path: str, project_dir: str = "."):
    from codec.bridge.code_interface import CodeInterface
    ci = CodeInterface(project_dir)
    c = ci.count_lines(file_path)
    return f"Total: {c['total']}  Code: {c['code']}  Blank: {c['blank']}  Comment: {c['comment']}"


@register_tool("find_imports", "List all imports in a file")
async def find_imports(file_path: str, project_dir: str = "."):
    from codec.bridge.code_interface import CodeInterface
    ci = CodeInterface(project_dir)
    imports = ci.find_imports(file_path)
    return "\n".join(imports) if imports else "No imports found."
