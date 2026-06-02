import asyncio
import sys
import argparse

from codec.config import Config
from codec.engine import CodeCEngine


def main():
    parser = argparse.ArgumentParser(prog="codec", description="CodeC - AI coding assistant")
    parser.add_argument("-c", "--command", help="Single command (non-interactive)")
    parser.add_argument("--directory", help="Project directory", default=".")
    parser.add_argument("--no-permit", action="store_true", help="Skip permission prompts")
    parser.add_argument("--version", action="store_true", help="Show version")
    parser.add_argument("--web", action="store_true", help="Launch web UI")
    parser.add_argument("--web-host", help="Web UI host", default="127.0.0.1")
    parser.add_argument("--web-port", help="Web UI port", type=int, default=8512)
    parser.add_argument("--gui", action="store_true", help="Launch desktop GUI")
    args = parser.parse_args()

    if args.version:
        print("CodeC v0.2.0")
        return

    if args.web:
        from codec.web.server import run as web_run
        web_run(host=args.web_host, port=args.web_port)
        return

    if args.gui:
        from codec.gui.desktop import run as gui_run
        gui_run()
        return

    config = Config()
    if args.directory:
        config.project_dir = args.directory

    if args.command:
        asyncio.run(_run_single(config, args.command))
    else:
        asyncio.run(_run_interactive(config, args.no_permit))


async def _run_single(config: Config, command: str):
    engine = CodeCEngine(config)
    engine.orchestrator.require_permission = False
    try:
        result = await engine.process(command)
        _safe_print(result)
    finally:
        await engine.cleanup()


async def _run_interactive(config: Config, no_permit: bool = False):
    engine = CodeCEngine(config)
    engine.orchestrator.require_permission = not no_permit

    _print_banner()
    print("Type /help for commands, /exit to quit.\n")

    use_ptk = False
    try:
        from prompt_toolkit import PromptSession
        from prompt_toolkit.history import FileHistory
        from pathlib import Path
        hist_path = Path(engine.session_dir) / "history.txt"
        hist_path.parent.mkdir(parents=True, exist_ok=True)
        session = PromptSession(history=FileHistory(str(hist_path)))
        use_ptk = True
    except ImportError:
        pass

    try:
        while True:
            try:
                if use_ptk:
                    user_input = await session.prompt_async("» ")
                else:
                    user_input = input("» ")
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if not user_input.strip():
                continue

            try:
                result = await engine.process(user_input)
                if result:
                    _safe_print(result)
                    print()
            except SystemExit:
                break
            except Exception as e:
                print(f"Error: {e}")
    finally:
        await engine.cleanup()


def _safe_print(text: str):
    enc = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode(enc, errors="replace").decode(enc, errors="replace"))


def _print_banner():
    try:
        from rich.console import Console
        from rich.panel import Panel
        Console().print(Panel.fit(
            "[bold cyan]CodeC[/bold cyan] v0.2.0 — Agentic AI Coding Assistant  "
            "[dim]tool loop | multi-model | session guardian[/dim]",
            border_style="cyan",
        ))
    except ImportError:
        print("CodeC v0.2.0 — Agentic AI Coding Assistant")


if __name__ == "__main__":
    main()
