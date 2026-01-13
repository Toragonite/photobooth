"""
Circuit Breaker Pattern for PhotoBooth Print System

Prevents cascading failures when CUPS/printer is unavailable.
Automatically opens circuit after repeated failures and closes
after successful recovery.

States:
- CLOSED: Normal operation, requests flow through
- OPEN: Blocking requests, waiting for recovery timeout
- HALF_OPEN: Testing with limited requests
"""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, TypeVar, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""

    # Number of failures before opening circuit
    failure_threshold: int = 5

    # Seconds to wait before attempting recovery
    recovery_timeout: int = 30

    # Successful calls needed to close circuit from half-open
    success_threshold: int = 2

    # Maximum concurrent requests in half-open state
    half_open_max_calls: int = 3

    # Errors that should NOT trip the circuit
    excluded_errors: tuple = ()


@dataclass
class CircuitBreakerMetrics:
    """Metrics for monitoring circuit breaker health."""

    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rejected_calls: int = 0
    state_changes: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    circuit_opened_count: int = 0


class CircuitBreakerError(Exception):
    """Raised when circuit is open and rejecting requests."""

    def __init__(self, circuit_name: str, retry_after: int):
        self.circuit_name = circuit_name
        self.retry_after = retry_after
        super().__init__(
            f"Circuit breaker '{circuit_name}' is OPEN. "
            f"Retry after {retry_after} seconds."
        )


class CircuitBreaker:
    """
    Circuit breaker for protecting external service calls.

    Usage:
        breaker = CircuitBreaker("cups_printer")

        @breaker
        async def print_job(job_id: str):
            # Call CUPS API
            pass

        # Or manual usage:
        async with breaker:
            await cups_client.submit_job(...)
    """

    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
        state_coordinator: Optional[Any] = None
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state_coordinator = state_coordinator

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._half_open_calls = 0
        self._lock = asyncio.Lock()

        self.metrics = CircuitBreakerMetrics()

    @property
    def state(self) -> CircuitState:
        """Current circuit state."""
        return self._state

    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)."""
        return self._state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        """Check if circuit is open (blocking requests)."""
        return self._state == CircuitState.OPEN

    @property
    def seconds_until_retry(self) -> int:
        """Seconds until circuit breaker allows retry."""
        if not self._last_failure_time or not self.is_open:
            return 0

        elapsed = (datetime.now() - self._last_failure_time).total_seconds()
        remaining = self.config.recovery_timeout - elapsed
        return max(0, int(remaining))

    async def __aenter__(self):
        """Context manager entry - check if call is allowed."""
        await self._before_call()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - record result."""
        if exc_type is None:
            await self._on_success()
        else:
            await self._on_failure(exc_val)
        return False

    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        """Decorator for wrapping async functions."""
        async def wrapper(*args, **kwargs) -> T:
            await self._before_call()
            try:
                result = await func(*args, **kwargs)
                await self._on_success()
                return result
            except Exception as e:
                await self._on_failure(e)
                raise

        return wrapper

    async def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with circuit breaker protection."""
        await self._before_call()
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure(e)
            raise

    async def _before_call(self):
        """Check circuit state before allowing call."""
        async with self._lock:
            self.metrics.total_calls += 1

            if self._state == CircuitState.CLOSED:
                return

            if self._state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._transition_to(CircuitState.HALF_OPEN)
                    self._half_open_calls = 1
                    return
                else:
                    self.metrics.rejected_calls += 1
                    raise CircuitBreakerError(
                        self.name,
                        self.seconds_until_retry
                    )

            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.config.half_open_max_calls:
                    self.metrics.rejected_calls += 1
                    raise CircuitBreakerError(
                        self.name,
                        self.config.recovery_timeout
                    )
                self._half_open_calls += 1

    async def _on_success(self):
        """Record successful call."""
        async with self._lock:
            self.metrics.successful_calls += 1
            self.metrics.last_success_time = datetime.now()

            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.config.success_threshold:
                    self._transition_to(CircuitState.CLOSED)
                    self._reset_counters()
            else:
                self._failure_count = 0

    async def _on_failure(self, error: Exception):
        """Record failed call."""
        # Check if this error should trip the circuit
        if isinstance(error, self.config.excluded_errors):
            logger.debug(f"Error excluded from circuit breaker: {error}")
            return

        async with self._lock:
            self.metrics.failed_calls += 1
            self.metrics.last_failure_time = datetime.now()
            self._last_failure_time = datetime.now()

            if self._state == CircuitState.HALF_OPEN:
                # Any failure in half-open state opens circuit again
                self._transition_to(CircuitState.OPEN)
                self._reset_counters()
            else:
                self._failure_count += 1
                if self._failure_count >= self.config.failure_threshold:
                    self._transition_to(CircuitState.OPEN)
                    self.metrics.circuit_opened_count += 1

    def _should_attempt_reset(self) -> bool:
        """Check if recovery timeout has elapsed."""
        if not self._last_failure_time:
            return True

        elapsed = datetime.now() - self._last_failure_time
        return elapsed >= timedelta(seconds=self.config.recovery_timeout)

    def _transition_to(self, new_state: CircuitState):
        """Transition to new state with logging."""
        old_state = self._state
        self._state = new_state
        self.metrics.state_changes += 1

        logger.info(
            f"Circuit breaker '{self.name}' state change: "
            f"{old_state.value} -> {new_state.value}"
        )

        # Sync to state coordinator if available
        if self.state_coordinator:
            try:
                self.state_coordinator.update_circuit_breaker(
                    state=new_state.value,
                    failure_count=self._failure_count,
                    next_retry_at=(
                        (datetime.now() + timedelta(
                            seconds=self.config.recovery_timeout
                        )).isoformat() + "Z"
                        if new_state == CircuitState.OPEN else None
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to sync circuit breaker state: {e}")

    def _reset_counters(self):
        """Reset all counters."""
        self._failure_count = 0
        self._success_count = 0
        self._half_open_calls = 0

    def force_open(self):
        """Manually open the circuit (for testing/maintenance)."""
        self._transition_to(CircuitState.OPEN)
        self._last_failure_time = datetime.now()

    def force_close(self):
        """Manually close the circuit (for recovery)."""
        self._transition_to(CircuitState.CLOSED)
        self._reset_counters()

    def get_status(self) -> dict:
        """Get current circuit breaker status."""
        return {
            "name": self.name,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "seconds_until_retry": self.seconds_until_retry,
            "metrics": {
                "total_calls": self.metrics.total_calls,
                "successful_calls": self.metrics.successful_calls,
                "failed_calls": self.metrics.failed_calls,
                "rejected_calls": self.metrics.rejected_calls,
                "state_changes": self.metrics.state_changes,
                "circuit_opened_count": self.metrics.circuit_opened_count
            }
        }


# Pre-configured circuit breakers for PhotoBooth

def create_cups_circuit_breaker(
    state_coordinator: Optional[Any] = None
) -> CircuitBreaker:
    """Create circuit breaker for CUPS print service."""
    return CircuitBreaker(
        name="cups_printer",
        config=CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=30,
            success_threshold=2,
            half_open_max_calls=2
        ),
        state_coordinator=state_coordinator
    )


def create_camera_circuit_breaker(
    state_coordinator: Optional[Any] = None
) -> CircuitBreaker:
    """Create circuit breaker for camera service."""
    return CircuitBreaker(
        name="camera",
        config=CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=10,
            success_threshold=1,
            half_open_max_calls=1
        ),
        state_coordinator=state_coordinator
    )
