"""Identifier value objects."""

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class SessionId:
    """Unique identifier for photo sessions."""

    value: str

    def __post_init__(self):
        try:
            uuid.UUID(self.value)
        except ValueError:
            raise ValueError("SessionId must be a valid UUID")

    @classmethod
    def generate(cls) -> "SessionId":
        """Generate a new SessionId."""
        return cls(str(uuid.uuid4()))

    @classmethod
    def from_string(cls, value: str) -> "SessionId":
        """Create from string."""
        return cls(value)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class PhotoId:
    """Unique identifier for photos."""

    value: str

    def __post_init__(self):
        try:
            uuid.UUID(self.value)
        except ValueError:
            raise ValueError("PhotoId must be a valid UUID")

    @classmethod
    def generate(cls) -> "PhotoId":
        """Generate a new PhotoId."""
        return cls(str(uuid.uuid4()))

    @classmethod
    def from_string(cls, value: str) -> "PhotoId":
        """Create from string."""
        return cls(value)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class JobId:
    """Unique identifier for print jobs."""

    value: str

    def __post_init__(self):
        if not self.value or len(self.value) < 8:
            raise ValueError("JobId must be at least 8 characters")

    @classmethod
    def generate(cls) -> "JobId":
        """Generate a new JobId."""
        return cls(uuid.uuid4().hex[:8])

    @classmethod
    def from_string(cls, value: str) -> "JobId":
        """Create from string."""
        return cls(value)

    def __str__(self) -> str:
        return self.value
