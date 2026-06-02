from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def execute(self, task: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        ...
