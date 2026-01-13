"""
Retry Policy for PhotoBooth Print Operations

Implements exponential backoff with jitter for handling transient failures.
Distinguishes between retryable and non-retryable errors per requirements.

Retry delays: 3s, 5s, 8s (as specified in DESIGN.md)
Max retries: 3 attempts
"""

import asyncio
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Callable, TypeVar, Any, Optional, Set, List
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ErrorCode(str, Enum):
    """Error codes for PhotoBooth operations."""

    # Retryable printer errors
    PRINTER_OFFLINE = "PRINTER_OFFLINE"
    PRINTER_BUSY = "PRINTER_BUSY"
    PRINTER_PAPER_EMPTY = "PRINTER_PAPER_EMPTY"
    PRINTER_INK_EMPTY = "PRINTER_INK_EMPTY"
    PRINTER_DOOR_OPEN = "PRINTER_DOOR_OPEN"

    # Retryable CUPS errors
    CUPS_UNAVAILABLE = "CUPS_UNAVAILABLE"
    CUPS_REJECTED = "CUPS_REJECTED"

    # Non-retryable errors
    PRINTER_PAPER_JAM = "PRINTER_PAPER_JAM"
    STORAGE_FULL = "STORAGE_FULL"

    # Session errors (non-retryable)
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"
    SESSION_EXPIRED = "SESSION_EXPIRED"
    PHOTO_INVALID = "PHOTO_INVALID"

    # System errors
    SYSTEM_ERROR = "SYSTEM_ERROR"


# Error classification
RETRYABLE_ERRORS: Set[ErrorCode] = {
    ErrorCode.PRINTER_OFFLINE,
    ErrorCode.PRINTER_BUSY,
    ErrorCode.PRINTER_PAPER_EMPTY,
    ErrorCode.PRINTER_INK_EMPTY,
    ErrorCode.PRINTER_DOOR_OPEN,
    ErrorCode.CUPS_UNAVAILABLE,
    ErrorCode.CUPS_REJECTED,
}

NON_RETRYABLE_ERRORS: Set[ErrorCode] = {
    ErrorCode.PRINTER_PAPER_JAM,
    ErrorCode.STORAGE_FULL,
    ErrorCode.SESSION_NOT_FOUND,
    ErrorCode.SESSION_EXPIRED,
    ErrorCode.PHOTO_INVALID,
}


class RetryableError(Exception):
    """Exception for retryable errors."""

    def __init__(self, code: ErrorCode, message: str, details: Optional[dict] = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(f"{code.value}: {message}")


class NonRetryableError(Exception):
    """Exception for non-retryable errors."""

    def __init__(self, code: ErrorCode, message: str, details: Optional[dict] = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(f"{code.value}: {message}")


@dataclass
class RetryAttempt:
    """Record of a single retry attempt."""
    attempt_number: int
    error_code: str
    error_message: str
    delay_seconds: float
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class RetryResult:
    """Result of retry operation."""
    success: bool
    result: Any = None
    total_attempts: int = 0
    total_delay_seconds: float = 0
    attempts: List[RetryAttempt] = field(default_factory=list)
    final_error: Optional[Exception] = None


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    # Maximum number of retry attempts
    max_retries: int = 3

    # Base delays for each attempt (per requirements: 3s, 5s, 8s)
    retry_delays: tuple = (3.0, 5.0, 8.0)

    # Jitter percentage (±25% randomness)
    jitter_percent: float = 0.25

    # Maximum delay cap
    max_delay: float = 60.0

    # Whether to log each retry attempt
    log_retries: bool = True


class RetryPolicy:
    """
    Retry policy with exponential backoff and jitter.

    Usage:
        policy = RetryPolicy()

        # As decorator
        @policy.retry
        async def submit_print_job(job_id: str):
            # Implementation
            pass

        # Manual usage
        result = await policy.execute(
            submit_print_job,
            job_id="123"
        )
    """

    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()

    def retry(self, func: Callable[..., T]) -> Callable[..., T]:
        """Decorator for adding retry logic to async functions."""

        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            result = await self.execute(func, *args, **kwargs)
            if result.success:
                return result.result
            else:
                raise result.final_error

        return wrapper

    async def execute(
        self,
        func: Callable[..., T],
        *args,
        on_retry: Optional[Callable[[RetryAttempt], None]] = None,
        **kwargs
    ) -> RetryResult:
        """
        Execute function with retry logic.

        Args:
            func: Async function to execute
            *args: Positional arguments
            on_retry: Callback for each retry attempt
            **kwargs: Keyword arguments

        Returns:
            RetryResult with success/failure info
        """
        result = RetryResult()
        last_error: Optional[Exception] = None

        for attempt in range(1, self.config.max_retries + 2):  # +1 for initial try
            result.total_attempts = attempt

            try:
                value = await func(*args, **kwargs)
                result.success = True
                result.result = value

                if attempt > 1:
                    logger.info(
                        f"Retry successful on attempt {attempt}"
                    )

                return result

            except NonRetryableError as e:
                # Non-retryable: fail immediately
                logger.error(f"Non-retryable error: {e.code.value} - {e.message}")
                result.success = False
                result.final_error = e
                return result

            except RetryableError as e:
                last_error = e
                error_code = e.code.value
                error_message = e.message

            except Exception as e:
                # Classify unknown errors as system errors
                last_error = e
                error_code = "SYSTEM_ERROR"
                error_message = str(e)

            # Check if we should retry
            if attempt > self.config.max_retries:
                logger.error(
                    f"All {self.config.max_retries} retries exhausted. "
                    f"Last error: {error_code}"
                )
                result.success = False
                result.final_error = last_error
                return result

            # Calculate delay with jitter
            delay = self._calculate_delay(attempt)
            result.total_delay_seconds += delay

            # Record attempt
            retry_attempt = RetryAttempt(
                attempt_number=attempt,
                error_code=error_code,
                error_message=error_message,
                delay_seconds=delay
            )
            result.attempts.append(retry_attempt)

            if self.config.log_retries:
                logger.warning(
                    f"Retry {attempt}/{self.config.max_retries} for {error_code}. "
                    f"Waiting {delay:.1f}s before next attempt."
                )

            # Call retry callback if provided
            if on_retry:
                try:
                    on_retry(retry_attempt)
                except Exception as callback_error:
                    logger.warning(f"Retry callback error: {callback_error}")

            # Wait before retry
            await asyncio.sleep(delay)

        result.success = False
        result.final_error = last_error
        return result

    def _calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for retry attempt with jitter.

        Uses configured delays: 3s, 5s, 8s with ±25% jitter.
        """
        # Get base delay for this attempt
        delay_index = min(attempt - 1, len(self.config.retry_delays) - 1)
        base_delay = self.config.retry_delays[delay_index]

        # Add jitter: ±25% randomness
        jitter_range = base_delay * self.config.jitter_percent
        jitter = random.uniform(-jitter_range, jitter_range)
        delay = base_delay + jitter

        # Cap at maximum
        return min(delay, self.config.max_delay)

    def is_retryable(self, error_code: ErrorCode) -> bool:
        """Check if an error code is retryable."""
        return error_code in RETRYABLE_ERRORS


# Convenience functions

def create_print_retry_policy() -> RetryPolicy:
    """Create retry policy for print operations."""
    return RetryPolicy(RetryConfig(
        max_retries=3,
        retry_delays=(3.0, 5.0, 8.0),
        jitter_percent=0.25,
        log_retries=True
    ))


def create_api_retry_policy() -> RetryPolicy:
    """Create retry policy for internal API calls."""
    return RetryPolicy(RetryConfig(
        max_retries=2,
        retry_delays=(1.0, 2.0),
        jitter_percent=0.1,
        log_retries=False
    ))


def raise_if_non_retryable(error_code: ErrorCode, message: str, **details):
    """Raise appropriate exception based on error code."""
    if error_code in NON_RETRYABLE_ERRORS:
        raise NonRetryableError(error_code, message, details)
    elif error_code in RETRYABLE_ERRORS:
        raise RetryableError(error_code, message, details)
    else:
        raise RetryableError(error_code, message, details)
