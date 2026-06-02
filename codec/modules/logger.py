import logging
import sys
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime


class ModuleLogger:
    def __init__(self, session_dir: str | None = None):
        self.logger = logging.getLogger("codec")
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers.clear()

        console = logging.StreamHandler(sys.stdout)
        console.setLevel(logging.INFO)
        console.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%H:%M:%S"
        ))
        self.logger.addHandler(console)

        if session_dir:
            log_dir = Path(session_dir) / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            file_handler = TimedRotatingFileHandler(
                str(log_dir / "codec.log"),
                when="midnight",
                backupCount=7,
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            ))
            self.logger.addHandler(file_handler)

    def debug(self, msg: str, **extra):
        self.logger.debug(msg, extra=extra)

    def info(self, msg: str, **extra):
        self.logger.info(msg, extra=extra)

    def warn(self, msg: str, **extra):
        self.logger.warning(msg, extra=extra)

    def error(self, msg: str, **extra):
        self.logger.error(msg, extra=extra)

    def log_llm_call(self, model: str, prompt_len: int, response_len: int, latency_ms: int, tag: str = ""):
        t = f" [{tag}]" if tag else ""
        self.info(f"LLM call:{t} model={model} prompt_tokens={prompt_len} "
                  f"response_tokens={response_len} latency={latency_ms}ms")

    def log_tool_call(self, tool: str, args: dict, result_len: int, latency_ms: int):
        self.info(f"Tool call: {tool} args={args} result_len={result_len} latency={latency_ms}ms")

    def get_recent(self, n: int = 20) -> list[str]:
        if not self.logger.handlers:
            return []
        for h in self.logger.handlers:
            if isinstance(h, TimedRotatingFileHandler):
                lines = []
                with open(h.baseFilename, "r") as f:
                    all_lines = f.readlines()
                    return [l.strip() for l in all_lines[-n:]]
        return []
