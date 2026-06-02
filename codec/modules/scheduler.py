import asyncio
from typing import Any, Callable, Coroutine


class Scheduler:
    def __init__(self, max_concurrency: int = 3):
        self.max_concurrency = max_concurrency
        self._semaphore = asyncio.Semaphore(max_concurrency)

    async def execute(self, tasks: list[dict[str, Any]],
                      executor: Callable[[dict[str, Any]], Coroutine[Any, Any, Any]],
                      progress_callback: Callable[[str, str], None] | None = None) -> list[dict[str, Any]]:
        ordered = sorted(tasks, key=lambda t: t.get("sequence", 0))
        results = []
        running = set()

        async def run_one(task: dict[str, Any]):
            async with self._semaphore:
                if progress_callback:
                    progress_callback(task["id"], "running")
                result = await executor(task)
                if progress_callback:
                    progress_callback(task["id"], "completed")
                return result

        pending = {asyncio.create_task(run_one(t)): t for t in ordered}
        while pending:
            done, _ = await asyncio.wait(pending.keys(), return_when=asyncio.FIRST_COMPLETED)
            for fut in done:
                task_info = pending[fut]
                try:
                    result = fut.result()
                    results.append(result)
                except Exception as e:
                    results.append({"id": task_info["id"], "error": str(e), "status": "failed"})
                del pending[fut]

        return results
