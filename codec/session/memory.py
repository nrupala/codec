from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


class SessionMemory:
    def __init__(self, session_dir: str):
        self._dir = Path(session_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._file = self._dir / "memory.json"
        self._store: dict[str, Any] = {}
        self._episodes: list[dict[str, Any]] = []
        self._load()

    def _load(self):
        if self._file.exists():
            try:
                data = json.loads(self._file.read_text())
                self._store = data.get("store", {})
                self._episodes = data.get("episodes", [])
            except (json.JSONDecodeError, OSError):
                pass

    def _save(self):
        self._file.write_text(json.dumps({
            "store": self._store,
            "episodes": self._episodes[-100:],
        }, indent=2))

    def remember(self, key: str, value: Any, ttl: int | None = None):
        entry = {"value": value, "created_at": time.time()}
        if ttl:
            entry["expires_at"] = time.time() + ttl
        self._store[key] = entry
        self._save()

    def recall(self, key: str, default: Any = None) -> Any:
        entry = self._store.get(key)
        if not entry:
            return default
        expires = entry.get("expires_at")
        if expires and time.time() > expires:
            del self._store[key]
            self._save()
            return default
        return entry["value"]

    def forget(self, key: str):
        self._store.pop(key, None)
        self._save()

    def clear(self):
        self._store.clear()
        self._episodes.clear()
        self._save()

    def recall_all(self) -> dict[str, Any]:
        now = time.time()
        expired = [k for k, v in self._store.items()
                   if v.get("expires_at") and now > v["expires_at"]]
        for k in expired:
            del self._store[k]
        if expired:
            self._save()
        return {k: v["value"] for k, v in self._store.items()}

    def record_episode(self, role: str, content: str, metadata: dict[str, Any] | None = None):
        self._episodes.append({
            "role": role,
            "content": content[:500],
            "metadata": metadata or {},
            "timestamp": time.time(),
        })
        self._save()

    def recent_episodes(self, n: int = 10) -> list[dict[str, Any]]:
        return self._episodes[-n:]

    def search_episodes(self, query: str) -> list[dict[str, Any]]:
        q = query.lower()
        return [
            e for e in self._episodes
            if q in e["content"].lower() or
               any(q in str(v).lower() for v in e["metadata"].values())
        ][-20:]
