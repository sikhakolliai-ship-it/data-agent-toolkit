"""Unit tests for resilience patterns."""

import pytest

from data_agent_toolkit.resilience.retry import CircuitBreaker, RetryExhaustedError, retry_with_backoff


class TestRetryWithBackoff:
    def test_succeeds_on_first_try(self):
        @retry_with_backoff(max_retries=3, base_delay=0.01)
        def always_works():
            return "success"

        assert always_works() == "success"

    def test_retries_and_succeeds(self):
        call_count = 0

        @retry_with_backoff(max_retries=3, base_delay=0.01)
        def fails_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("transient error")
            return "success"

        assert fails_twice() == "success"
        assert call_count == 3

    def test_exhausts_retries(self):
        @retry_with_backoff(max_retries=2, base_delay=0.01)
        def always_fails():
            raise ValueError("permanent error")

        with pytest.raises(RetryExhaustedError):
            always_fails()


class TestCircuitBreaker:
    def test_starts_closed(self):
        cb = CircuitBreaker(failure_threshold=3)
        assert cb.state == "CLOSED"
        assert cb.allow_request() is True

    def test_opens_after_threshold(self):
        cb = CircuitBreaker(failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        cb.record_failure()
        assert cb.state == "OPEN"
        assert cb.allow_request() is False

    def test_resets_on_success(self):
        cb = CircuitBreaker(failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()  # Reset
        assert cb.state == "CLOSED"
        assert cb.allow_request() is True

    def test_half_open_after_timeout(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.01)
        cb.record_failure()
        assert cb.state == "OPEN"

        import time

        time.sleep(0.02)  # Wait for recovery timeout
        assert cb.state == "HALF_OPEN"
        assert cb.allow_request() is True
