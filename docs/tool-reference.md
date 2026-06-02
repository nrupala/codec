# CodeC Tool Reference

## File Operations

### `read_file(path: str) -> str`
Read a file's contents. Returns error if file not found.
- `path`: Path relative to project directory

### `write_file(path: str, content: str) -> str`
Write content to a file (overwrites existing).
- `path`: File path
- `content`: File content

### `edit_file(path: str, old_string: str, new_string: str) -> str`
Replace text in a file. Fails if old_string not found or has multiple matches.
- `path`: File path
- `old_string`: Text to replace
- `new_string`: Replacement text

### `edit_file_with_diff(path, old_string, new_string) -> str`
Same as edit_file but shows diff first and prompts for confirmation.

### `diff_file(file_path: str, new_content: str) -> str`
Preview changes as a unified diff without applying them.

### `list_files(pattern: str = "*") -> str`
List files matching a glob pattern.

### `glob_files(pattern: str) -> str`
Find files by glob pattern from project root.

## Search

### `grep_search(pattern: str, include: str = "*") -> str`
Search file contents using regex. Returns file:line matches.
- `pattern`: Regex pattern
- `include`: File glob filter (e.g. "*.py")

### `web_search(query: str, num_results: int = 5) -> str`
Search the web using DuckDuckGo. Top results with titles and URLs.

### `web_fetch(url: str, timeout: int = 30) -> str`
Fetch a URL and return text content (max 10KB).

## Shell

### `run_shell(command: str, timeout: int = 60) -> str`
Execute a shell command. Returns stdout/stderr (max 10KB).
- Commands are sandboxed via SessionGuardian (blocks dangerous operations)
- 60 second default timeout

## Testing

### `run_tests(command: str = "") -> str`
Auto-detect and run tests. Detects pytest, cargo test, npm test, gradle, make.
Specify `command` to override detection.

### `detect_test_command() -> str`
Show what test command would be used for the current project.

## Git

### `git_status() -> str`
Show working tree status.

### `git_diff(staged: bool = False) -> str`
Show uncommitted changes as a diff.

### `git_log(count: int = 10) -> str`
Show recent commit history.

### `git_commit(message: str) -> str`
Stage all changes and commit with message.

### `git_branch() -> str`
Show current branch name.

## Planning

### `create_plan(goal: str, steps: list[str]) -> str`
Create a structured plan with steps. Plan is persisted and shown in system prompt.

### `update_plan_step(step_index: int, status: str, result: str = "") -> str`
Mark a plan step as completed/failed. Status: completed, failed, running, pending.

### `get_plan() -> str`
Show current active plan and progress.

## Project Analysis

### `project_summary() -> str`
File count, language breakdown, total lines.

### `detect_language(file_path: str) -> str`
Detect programming language of a file.

### `find_functions(file_path: str) -> str`
List all functions and classes with line numbers.

### `count_lines(file_path: str) -> str`
Total, code, blank, and comment line counts.

### `find_imports(file_path: str) -> str`
List all import statements in a file.
