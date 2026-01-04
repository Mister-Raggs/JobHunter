"""
Retry logic with exponential backoff for handling transient failures.

Provides decorators and utilities for automatically retrying operations
that may fail due to network issues, rate limiting, or temporary errors.
"""

import time
import functools
from typing import Callable, Type, Tuple, Optional
from datetime import datetime, timedelta


class RetryError(Exception):
    """Raised when all retry attempts are exhausted."""
    pass


def exponential_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable] = None,
):
    """
    Decorator for retrying functions with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts (0 = no retries)
        base_delay: Initial delay in seconds
        max_delay: Maximum delay between retries in seconds
        exponential_base: Base for exponential calculation (delay *= base)
        exceptions: Tuple of exceptions to catch and retry
        on_retry: Optional callback function(attempt, exception, delay)

    Example:
        @exponential_backoff(max_retries=3, base_delay=1.0)
        def fetch_data(url):
            return requests.get(url)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = base_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    # Don't sleep after the last attempt
                    if attempt < max_retries:
                        current_delay = min(delay, max_delay)

                        if on_retry:
                            on_retry(attempt + 1, e, current_delay)

                        time.sleep(current_delay)
                        delay *= exponential_base
                    else:
                        # All retries exhausted
                        raise RetryError(
                            f"Failed after {max_retries + 1} attempts: {str(e)}"
                        ) from e

            # Should not reach here, but just in case
            raise RetryError(
                f"Unexpected retry exhaustion: {str(last_exception)}"
            ) from last_exception

        return wrapper
    return decorator


class CircuitBreaker:
    """
    Circuit breaker pattern to prevent repeated calls to failing services.

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, requests are blocked
    - HALF_OPEN: Testing if service has recovered
    """

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: Type[Exception] = Exception,
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            expected_exception: Exception type that counts as failure
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = self.CLOSED

    def call(self, func: Callable, *args, **kwargs):
        """
        Execute function with circuit breaker protection.

        Raises:
            Exception: If circuit is OPEN
            Original exception: If function fails in CLOSED/HALF_OPEN state
        """
        if self.state == self.OPEN:
            if self._should_attempt_reset():
                self.state = self.HALF_OPEN
            else:
                raise Exception(
                    f"Circuit breaker is OPEN. Service unavailable. "
                    f"Retry after {self._time_until_reset():.0f}s"
                )

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True

        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return elapsed >= self.recovery_timeout

    def _time_until_reset(self) -> float:
        """Calculate seconds until circuit can be tested."""
        if self.last_failure_time is None:
            return 0

        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return max(0, self.recovery_timeout - elapsed)

    def _on_success(self):
        """Reset circuit breaker on successful call."""
        self.failure_count = 0
        self.state = self.CLOSED

    def _on_failure(self):
        """Record failure and potentially open circuit."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self.state = self.OPEN

    def reset(self):
        """Manually reset the circuit breaker."""
        self.failure_count = 0
        self.last_failure_time = None
        self.state = self.CLOSED


def is_transient_error(exception: Exception) -> bool:
    """
    Determine if an exception is likely transient and should be retried.

    Args:
        exception: Exception to check

    Returns:
        True if error is likely transient (timeout, connection, 5xx)
    """
    error_str = str(exception).lower()

    # Network-related errors
    transient_keywords = [
        'timeout',
        'connection',
        'temporary failure',
        'service unavailable',
        '503',
        '502',
        '500',
        '429',  # Rate limit
        'read timed out',
        'connection reset',
    ]

    return any(keyword in error_str for keyword in transient_keywords)


def should_retry_http_status(status_code: int) -> bool:
    """
    Check if HTTP status code indicates a retryable error.

    Args:
        status_code: HTTP status code

    Returns:
        True if should retry
    """
    # Retry on server errors and rate limiting
    retryable_codes = {
        408,  # Request Timeout
        429,  # Too Many Requests
        500,  # Internal Server Error
        502,  # Bad Gateway
        503,  # Service Unavailable
        504,  # Gateway Timeout
    }

    return status_code in retryable_codes
