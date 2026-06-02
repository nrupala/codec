import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Config:
    api_key: str = field(default_factory=lambda: os.getenv("CODECK_API_KEY", ""))
    model: str = os.getenv("CODECK_MODEL", "gpt-4o")
    api_base: str = os.getenv("CODECK_API_BASE", "https://api.openai.com/v1")
    max_tokens: int = int(os.getenv("CODECK_MAX_TOKENS", "4096"))
    log_level: str = os.getenv("CODECK_LOG_LEVEL", "INFO")
    project_dir: str = os.getenv("CODECK_PROJECT_DIR", ".")
    allow_shell: bool = os.getenv("CODECK_ALLOW_SHELL", "true").lower() == "true"
    allow_web: bool = os.getenv("CODECK_ALLOW_WEB", "true").lower() == "true"
    max_concurrency: int = int(os.getenv("CODECK_MAX_CONCURRENCY", "3"))
    session_dir: str = field(default_factory=lambda: str(
        Path(os.getenv("CODECK_PROJECT_DIR", ".")) / ".codec"
    ))

    @property
    def resolved_project_dir(self) -> str:
        return str(Path(self.project_dir).resolve())

    def validate(self) -> list[str]:
        errors = []
        if not self.api_key:
            errors.append("CODECK_API_KEY is not set")
        return errors
