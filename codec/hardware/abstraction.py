from abc import ABC, abstractmethod
from typing import Any
from dataclasses import dataclass, field


@dataclass
class HardwareCapabilities:
    has_fpga: bool = False
    has_gpu: bool = False
    has_neural_engine: bool = False
    memory_gb: float = 0.0
    compute_units: int = 0
    platform: str = "unknown"


@dataclass
class InferenceResult:
    success: bool
    output: Any = None
    latency_ms: int = 0
    error: str | None = None


class BaseAccelerator(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    async def initialize(self) -> bool:
        ...

    @abstractmethod
    async def infer(self, model_input: Any, **kwargs) -> InferenceResult:
        ...

    @abstractmethod
    async def shutdown(self):
        ...


class SoftwareAccelerator(BaseAccelerator):
    def __init__(self):
        self._initialized = False

    @property
    def name(self) -> str:
        return "software/fallback"

    async def initialize(self) -> bool:
        self._initialized = True
        return True

    async def infer(self, model_input: Any, **kwargs) -> InferenceResult:
        return InferenceResult(success=True, output=model_input)

    async def shutdown(self):
        self._initialized = False


class HardwareAbstractionLayer:
    def __init__(self):
        self._accelerators: dict[str, BaseAccelerator] = {}
        self._active: str | None = None
        self._fallback = SoftwareAccelerator()

    def register(self, name: str, accelerator: BaseAccelerator):
        self._accelerators[name] = accelerator

    def activate(self, name: str) -> bool:
        if name in self._accelerators:
            self._active = name
            return True
        return False

    def get_active(self) -> BaseAccelerator:
        if self._active and self._active in self._accelerators:
            return self._accelerators[self._active]
        return self._fallback

    def detect_capabilities(self) -> HardwareCapabilities:
        import platform
        caps = HardwareCapabilities(platform=platform.system().lower())
        try:
            import torch
            caps.has_gpu = torch.cuda.is_available()
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                caps.has_neural_engine = True
        except ImportError:
            pass
        return caps

    def list_accelerators(self) -> list[str]:
        return list(self._accelerators.keys()) + ["software/fallback"]


hal = HardwareAbstractionLayer()
