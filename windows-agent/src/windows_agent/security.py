from __future__ import annotations

import time
from collections import deque


class NonceTracker:
    def __init__(self, max_nonces: int = 200) -> None:
        self.max_nonces = max_nonces
        self._recent: dict[str, deque[str]] = {}

    def is_fresh(self, *, device_id: str, nonce: str) -> bool:
        if not nonce:
            return False
        device_nonces = self._recent.setdefault(device_id, deque(maxlen=self.max_nonces))
        if nonce in device_nonces:
            return False
        device_nonces.append(nonce)
        return True


class RateLimiter:
    def __init__(self, limit_per_sec: int) -> None:
        self.limit_per_sec = limit_per_sec
        self._events: dict[str, deque[float]] = {}

    def allow(self, device_id: str) -> bool:
        now = time.monotonic()
        q = self._events.setdefault(device_id, deque())
        while q and (now - q[0]) > 1.0:
            q.popleft()
        if len(q) >= self.limit_per_sec:
            return False
        q.append(now)
        return True
