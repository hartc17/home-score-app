from __future__ import annotations

import threading
from collections import deque

# In-process sliding-window limiter. Deployment runs a single uvicorn worker,
# so process-local state is the whole picture; a multi-worker deployment would
# move this to the database or a shared store, like the per-email limit.

_PRUNE_ABOVE = 10_000


class SlidingWindowLimiter:
    def __init__(self, max_events: int, window_seconds: float) -> None:
        self.max_events = max_events
        self.window_seconds = window_seconds
        self._events: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def allow(self, key: str, now: float) -> bool:
        cutoff = now - self.window_seconds
        with self._lock:
            events = self._events.setdefault(key, deque())
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= self.max_events:
                return False
            events.append(now)
            if len(self._events) > _PRUNE_ABOVE:
                self._prune(cutoff)
            return True

    def _prune(self, cutoff: float) -> None:
        stale = [key for key, events in self._events.items() if not events or events[-1] <= cutoff]
        for key in stale:
            del self._events[key]

    def reset(self) -> None:
        with self._lock:
            self._events.clear()
