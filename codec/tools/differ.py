import sys

from codec.tools.registry import register_tool
from codec.session.diff_engine import DiffEngine


@register_tool("diff_file", "Show a diff of proposed changes to a file before applying them")
async def diff_file(file_path: str, new_content: str, project_dir: str = "."):
    de = DiffEngine(project_dir)
    info = de.compute_file_diff_before_after(file_path, new_content)
    if not info["diff"]:
        return "(no changes)"
    summary = f"File: {file_path}\n+{info['lines_added']} -{info['lines_removed']}\n"
    return summary + "\n" + info["diff"]


@register_tool("edit_file_with_diff",
               "Edit a file showing diff first. Use `old_string` and `new_string` like edit_file.")
async def edit_file_with_diff(path: str, old_string: str, new_string: str,
                              project_dir: str = "."):
    from codec.tools.file_ops import read_file, edit_file
    current = await read_file(path, project_dir=project_dir)
    if current.startswith("Error"):
        return current

    new_content = current.replace(old_string, new_string, 1)
    de = DiffEngine(project_dir)
    diff = de.compute_edit_diff(path, current, new_content)

    header = f"[Diff for {path}]\n"
    short_diff = "\n".join(diff.split("\n")[:30])

    try:
        if sys.stdin.isatty():
            print(f"\n{header}{short_diff}")
            if len(diff.split("\n")) > 30:
                print(f"  ... ({len(diff.split('\n'))} total lines)")
            resp = input("Apply this change? (Y/n): ").strip().lower()
            if resp in ("", "y", "yes"):
                return await edit_file(path, old_string, new_string, project_dir=project_dir)
            return "Edit skipped by user."
    except Exception:
        pass

    return await edit_file(path, old_string, new_string, project_dir=project_dir)
