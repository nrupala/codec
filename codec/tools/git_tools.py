import asyncio
import os
from pathlib import Path

from codec.tools.registry import register_tool


async def _shell(cmd: str, project_dir: str) -> str:
    from codec.tools.shell import run_shell
    cwd = os.getcwd()
    try:
        os.chdir(project_dir)
        return await run_shell(cmd)
    finally:
        os.chdir(cwd)


@register_tool("git_status", "Show the current git status of the repository")
async def git_status(project_dir: str = "."):
    return await _shell("git status", project_dir)


@register_tool("git_diff", "Show uncommitted changes as a diff")
async def git_diff(staged: bool = False, project_dir: str = "."):
    cmd = "git diff --cached" if staged else "git diff"
    return await _shell(cmd, project_dir)


@register_tool("git_log", "Show recent git log")
async def git_log(count: int = 10, project_dir: str = "."):
    return await _shell(f"git log --oneline -{count}", project_dir)


@register_tool("git_commit", "Create a git commit with a message. Stages all changed files first.")
async def git_commit(message: str, project_dir: str = "."):
    add = await _shell("git add -A", project_dir)
    result = await _shell(f'git commit -m "{message}"', project_dir)
    return result


@register_tool("git_branch", "Show current git branch")
async def git_branch(project_dir: str = "."):
    return await _shell("git branch --show-current", project_dir)
