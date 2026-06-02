from typing import Any, Callable, Coroutine

ToolFunc = Callable[..., Coroutine[Any, Any, str]]


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, tuple[ToolFunc, str]] = {}

    def register(self, name: str, description: str = ""):
        def decorator(func: ToolFunc):
            self._tools[name] = (func, description or func.__doc__ or "")
            return func
        return decorator

    def get(self, name: str) -> ToolFunc | None:
        if name in self._tools:
            return self._tools[name][0]
        return None

    def list_tools(self) -> dict[str, str]:
        return {name: desc for name, (_, desc) in self._tools.items()}

    def call(self, name: str, **kwargs) -> Coroutine[Any, Any, str]:
        tool = self.get(name)
        if not tool:
            raise ValueError(f"Unknown tool: {name}")
        return tool(**kwargs)


registry = ToolRegistry()
register_tool = registry.register
