from abc import ABC, abstractmethod
from typing import Any


class BaseLLMBackend(ABC):
    @abstractmethod
    async def generate(self, messages: list[dict[str, str]], **kwargs) -> str:
        ...

    @abstractmethod
    async def generate_with_metadata(self, messages: list[dict[str, str]], **kwargs) -> dict[str, Any]:
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def supports_streaming(self) -> bool:
        ...
