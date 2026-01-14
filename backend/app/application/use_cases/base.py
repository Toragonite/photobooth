"""Base use case class and result wrapper."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, Optional, TypeVar

T = TypeVar("T")


@dataclass
class UseCaseResult(Generic[T]):
    """Standard result wrapper for use cases."""

    success: bool
    data: Optional[T] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None

    @classmethod
    def ok(cls, data: T) -> "UseCaseResult[T]":
        """Create a successful result."""
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, error_code: str, error_message: str) -> "UseCaseResult[T]":
        """Create a failure result."""
        return cls(success=False, error_code=error_code, error_message=error_message)


class UseCase(ABC, Generic[T]):
    """Base use case interface."""

    @abstractmethod
    async def execute(self, *args, **kwargs) -> UseCaseResult[T]:
        """Execute the use case."""
        pass
