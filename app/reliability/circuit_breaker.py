"""Circuit breaker for external dependencies (LLM provider, etc.).

States: CLOSED (normal) → OPEN (failing, fast-fail) → after cooldown →
HALF-OPEN (trial call) → CLOSED on success / OPEN on failure.
"""

import threading
import time
from collections.abc import Callable
from enum import StrEnum
from typing import TypeVar

T = TypeVar("T")



class BreakerState(StrEnum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitOpenError(Exception):
    """Raised when the breaker is OPEN — callers should fall back gracefully."""


class CircuitBreaker:
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout_seconds: float = 30.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self._clock = clock
        self._lock = threading.Lock()
        self._state = BreakerState.CLOSED
        self._failure_count = 0
        self._opened_at: float | None = None
        self.trip_count = 0  # observable metric (Milestone 11)

    @property
    def state(self) -> BreakerState:
        with self._lock:
            if self._state == BreakerState.OPEN:
                elapsed = self._clock() - (self._opened_at or 0)
                if elapsed >= self.recovery_timeout_seconds:
                    self._state = BreakerState.HALF_OPEN
            return self._state

    def call(self, fn: Callable[[], T]) -> T:
        if self.state == BreakerState.OPEN:
            raise CircuitOpenError(f"Circuit '{self.name}' is OPEN")
        try:
            result = fn()
        except Exception:
            self._on_failure()
            raise
        self._on_success()
        return result

    def _on_success(self) -> None:
        with self._lock:
            self._failure_count = 0
            self._state = BreakerState.CLOSED

    def _on_failure(self) -> None:
        with self._lock:
            self._failure_count += 1
            if self._state == BreakerState.HALF_OPEN or self._failure_count >= self.failure_threshold:
                if self._state != BreakerState.OPEN:
                    self.trip_count += 1
                self._state = BreakerState.OPEN
                self._opened_at = self._clock()