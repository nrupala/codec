import asyncio
import sys

from codec.tools.registry import register_tool


@register_tool("run_shell", "Run a shell command and return its output")
async def run_shell(command: str, timeout: int = 60) -> str:
    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            shell=True,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return f"Error: command timed out after {timeout}s"

        output = ""
        if stdout:
            decoded = stdout.decode("utf-8", errors="replace")
            output += decoded
        if stderr:
            decoded = stderr.decode("utf-8", errors="replace")
            if output:
                output += "\n--- stderr ---\n"
            output += decoded

        exit_code = proc.returncode
        if exit_code != 0:
            output += f"\n(exit code: {exit_code})"

        max_output = 10000
        if len(output) > max_output:
            output = output[:max_output] + f"\n... (truncated, {len(output)} total chars)"

        return output.strip() or "(no output)"
    except FileNotFoundError:
        return f"Error: command not found: {command.split()[0]}"
    except Exception as e:
        return f"Error running command: {e}"
