"""
Tests for retry logic and circuit breaker.
"""

import pytest
import time
from jobhunter.retry import (
    exponential_backoff,
    CircuitBreaker,
    is_transient_error,
    should_retry_http_status,
    RetryError,
)


class TestExponentialBackoff:
    """Test exponential backoff decorator."""

    def test_success_on_first_try(self):
        """Function that succeeds immediately should not retry."""
        call_count = [0]

        @exponential_backoff(max_retries=3, base_delay=0.1)
        def succeeds():
            call_count[0] += 1
            return "success"

        result = succeeds()
        assert result == "success"
        assert call_count[0] == 1

    def test_retry_then_succeed(self):
        """Function that fails then succeeds should retry."""
        call_count = [0]

        @exponential_backoff(max_retries=3, base_delay=0.01)
        def fails_twice():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ConnectionError("Temporary failure")
            return "success"

        result = fails_twice()
        assert result == "success"
        assert call_count[0] == 3

    def test_all_retries_exhausted(self):
        """Should raise RetryError after all attempts fail."""
        call_count = [0]

        @exponential_backoff(max_retries=2, base_delay=0.01)
        def always_fails():
            call_count[0] += 1
            raise ValueError("Always fails")

        with pytest.raises(RetryError):
            always_fails()

        assert call_count[0] == 3  # Initial + 2 retries

    def test_only_catches_specified_exceptions(self):
        """Should only retry on specified exception types."""
        call_count = [0]

        @exponential_backoff(
            max_retries=3,
            base_delay=0.01,
            exceptions=(ConnectionError,)
        )
        def raises_value_error():
            call_count[0] += 1
            raise ValueError("Not retryable")

        # Should not retry, raises original exception
        with pytest.raises(ValueError):
            raises_value_error()

        assert call_count[0] == 1  # No retries

    def test_exponential_delay(self):
        """Delay should increase exponentially."""
        delays = []

        def on_retry_callback(attempt, exception, delay):
            delays.append(delay)

        @exponential_backoff(
            max_retries=3,
            base_delay=0.01,
            exponential_base=2.0,
            on_retry=on_retry_callback
        )
        def always_fails():
            raise ConnectionError("Test")

        with pytest.raises(RetryError):
            always_fails()

        # Check delays are increasing
        assert len(delays) == 3
        assert delays[0] == 0.01
        assert delays[1] == 0.02
        assert delays[2] == 0.04

    def test_max_delay_cap(self):
        """Delay should not exceed max_delay."""
        delays = []

        def on_retry_callback(attempt, exception, delay):
            delays.append(delay)

        @exponential_backoff(
            max_retries=5,
            base_delay=1.0,
            max_delay=2.0,
            exponential_base=3.0,
            on_retry=on_retry_callback
        )
        def always_fails():
            raise ConnectionError("Test")

        with pytest.raises(RetryError):
            always_fails()

        # All delays should be capped at max_delay
        assert all(d <= 2.0 for d in delays)


class TestCircuitBreaker:
    """Test circuit breaker pattern."""

    def test_closed_state_allows_calls(self):
        """Circuit starts closed and allows calls."""
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=1)

        def successful_func():
            return "success"

        result = breaker.call(successful_func)
        assert result == "success"
        assert breaker.state == CircuitBreaker.CLOSED

    def test_opens_after_threshold(self):
        """Circuit opens after failure threshold."""
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=1)

        def failing_func():
            raise ConnectionError("Test failure")

        # Fail 3 times to reach threshold
        for i in range(3):
            with pytest.raises(ConnectionError):
                breaker.call(failing_func)

        assert breaker.state == CircuitBreaker.OPEN

        # Next call should be blocked
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            breaker.call(failing_func)

    def test_half_open_after_timeout(self):
        """Circuit transitions to half-open after recovery timeout."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)

        def failing_func():
            raise ConnectionError("Test")

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ConnectionError):
                breaker.call(failing_func)

        assert breaker.state == CircuitBreaker.OPEN

        # Wait for recovery timeout
        time.sleep(0.15)

        # Next call should attempt (half-open)
        with pytest.raises(ConnectionError):
            breaker.call(failing_func)

        # Should have attempted the call (not blocked)

    def test_closes_on_success_in_half_open(self):
        """Successful call in half-open state closes circuit."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)

        call_count = [0]

        def sometimes_fails():
            call_count[0] += 1
            if call_count[0] <= 2:
                raise ConnectionError("Fail")
            return "success"

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ConnectionError):
                breaker.call(sometimes_fails)

        assert breaker.state == CircuitBreaker.OPEN

        # Wait and try again
        time.sleep(0.15)
        result = breaker.call(sometimes_fails)

        assert result == "success"
        assert breaker.state == CircuitBreaker.CLOSED

    def test_manual_reset(self):
        """Manual reset should close the circuit."""
        breaker = CircuitBreaker(failure_threshold=2)

        def failing_func():
            raise ConnectionError("Test")

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ConnectionError):
                breaker.call(failing_func)

        assert breaker.state == CircuitBreaker.OPEN

        breaker.reset()
        assert breaker.state == CircuitBreaker.CLOSED
        assert breaker.failure_count == 0


class TestTransientErrorDetection:
    """Test transient error detection utilities."""

    def test_detects_timeout_errors(self):
        """Should detect timeout errors as transient."""
        error = ConnectionError("Connection timeout")
        assert is_transient_error(error)

    def test_detects_connection_errors(self):
        """Should detect connection errors as transient."""
        error = Exception("Connection reset by peer")
        assert is_transient_error(error)

    def test_detects_server_errors(self):
        """Should detect 5xx errors as transient."""
        errors = [
            Exception("503 Service Unavailable"),
            Exception("502 Bad Gateway"),
            Exception("500 Internal Server Error"),
        ]
        for error in errors:
            assert is_transient_error(error)

    def test_non_transient_errors(self):
        """Should not detect permanent errors as transient."""
        errors = [
            Exception("404 Not Found"),
            ValueError("Invalid data"),
            Exception("401 Unauthorized"),
        ]
        for error in errors:
            assert not is_transient_error(error)

    def test_http_status_retry_logic(self):
        """Should correctly identify retryable HTTP status codes."""
        # Retryable
        assert should_retry_http_status(408)  # Timeout
        assert should_retry_http_status(429)  # Rate limit
        assert should_retry_http_status(500)  # Server error
        assert should_retry_http_status(502)  # Bad gateway
        assert should_retry_http_status(503)  # Service unavailable

        # Not retryable
        assert not should_retry_http_status(200)  # Success
        assert not should_retry_http_status(404)  # Not found
        assert not should_retry_http_status(403)  # Forbidden
        assert not should_retry_http_status(401)  # Unauthorized
