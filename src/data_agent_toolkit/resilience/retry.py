"""Resilience patterns for production agent execution.

Exponential backoff, circuit breaker, and fallback model routing
for LLM calls that can fail transiently.
"""

from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RetryExhaustedError(Exception):
    """All retry attempts failed."""


class CircuitOpenError(Exception):
    """Circuit breaker is open — calls are blocked."""


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable:
    """Decorator: retry with exponential backoff + jitter.

    Usage:
        @retry_with_backoff(max_retries=3)
        def call_llm(prompt: str) -> str:
            return llm.invoke(prompt)
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        logger.error(
                            "All %d retries exhausted for %s: %s",
                            max_retries,
                            func.__name__,
                            str(e),
                        )
                        raise RetryExhaustedError(
                            f"{func.__name__} failed after {max_retries} retries: {e}"
                        ) from e

                    delay = min(base_delay * (2**attempt) + random.uniform(0, 1), max_delay)
                    logger.warning(
                        "Attempt %d/%d for %s failed: %s. Retrying in %.1fs",
                        attempt + 1,
                        max_retries,
                        func.__name__,
                        str(e),
                        delay,
                    )
                    time.sleep(delay)

            raise RetryExhaustedError(f"Unexpected: {last_exception}")

        return wrapper

    return decorator


@dataclass
class CircuitBreaker:
    """Circuit breaker for model serving endpoints.

    Prevents hammering a failing endpoint. After `failure_threshold`
    consecutive failures, the circuit opens and blocks calls for
    `recovery_timeout` seconds.

    States:
        CLOSED: Normal operation, calls pass through
        OPEN: Calls blocked, waiting for recovery
        HALF_OPEN: One test call allowed to check if service recovered
    """

    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    _failure_count: int = field(default=0, init=False)
    _last_failure_time: datetime | None = field(default=None, init=False)
    _state: str = field(default="CLOSED", init=False)

    @property
    def state(self) -> str:
        if self._state == "OPEN" and self._last_failure_time:
            if datetime.utcnow() - self._last_failure_time > timedelta(seconds=self.recovery_timeout):
                self._state = "HALF_OPEN"
        return self._state

    def record_success(self) -> None:
        self._failure_count = 0
        self._state = "CLOSED"

    def record_failure(self) -> None:
        self._failure_count += 1
        self._last_failure_time = datetime.utcnow()
        if self._failure_count >= self.failure_threshold:
            self._state = "OPEN"
            logger.error("Circuit breaker OPEN after %d failures", self._failure_count)

    def allow_request(self) -> bool:
        current_state = self.state
        if current_state == "CLOSED":
            return True
        if current_state == "HALF_OPEN":
            return True
        return False
