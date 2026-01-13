"""
PhotoBooth Agent Infrastructure

Multi-agent coordination, state management, and resilience patterns
for the PhotoBooth system running on Raspberry Pi 5.

Components:
- StateCoordinator: Thread-safe state management with file locking
- CircuitBreaker: Protects against cascading failures
- RetryPolicy: Exponential backoff with jitter
- BackgroundTaskManager: Parallel task execution and tracking
"""

from .state_coordinator import StateCoordinator
from .circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerError,
    CircuitState,
    create_cups_circuit_breaker,
    create_camera_circuit_breaker,
)
from .retry_policy import (
    RetryPolicy,
    RetryConfig,
    RetryResult,
    RetryableError,
    NonRetryableError,
    ErrorCode,
    RETRYABLE_ERRORS,
    NON_RETRYABLE_ERRORS,
    create_print_retry_policy,
    create_api_retry_policy,
    raise_if_non_retryable,
)
from .background_task_manager import (
    BackgroundTaskManager,
    BackgroundTask,
    TaskStatus,
)

__all__ = [
    # State Management
    "StateCoordinator",

    # Circuit Breaker
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitBreakerError",
    "CircuitState",
    "create_cups_circuit_breaker",
    "create_camera_circuit_breaker",

    # Retry Policy
    "RetryPolicy",
    "RetryConfig",
    "RetryResult",
    "RetryableError",
    "NonRetryableError",
    "ErrorCode",
    "RETRYABLE_ERRORS",
    "NON_RETRYABLE_ERRORS",
    "create_print_retry_policy",
    "create_api_retry_policy",
    "raise_if_non_retryable",

    # Background Tasks
    "BackgroundTaskManager",
    "BackgroundTask",
    "TaskStatus",
]


def create_agent_infrastructure(
    state_dir: str = ".claude/state",
    task_dir: str = ".claude/tasks",
    db_path: str = "data/agent_state.db"
):
    """
    Create and wire up all agent infrastructure components.

    Returns:
        Tuple of (state_coordinator, task_manager, cups_circuit_breaker, print_retry_policy)
    """
    # State coordinator
    state_coordinator = StateCoordinator(
        state_dir=state_dir,
        db_path=db_path
    )

    # Background task manager
    task_manager = BackgroundTaskManager(
        task_dir=task_dir,
        max_concurrent=10,
        default_timeout=300,
        state_coordinator=state_coordinator
    )

    # Circuit breaker for CUPS
    cups_breaker = create_cups_circuit_breaker(state_coordinator)

    # Retry policy for print operations
    print_retry = create_print_retry_policy()

    return state_coordinator, task_manager, cups_breaker, print_retry
