"""Storage service port."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class StorageInfo:
    """Information about storage capacity and usage."""
    total_bytes: int
    used_bytes: int
    free_bytes: int
    percent_used: float

    @property
    def is_critical(self) -> bool:
        return self.percent_used > 90.0


class StoragePort(ABC):
    """Abstract port for file storage operations."""

    @abstractmethod
    async def save_photo(self, session_id: str, index: int, data: bytes) -> str:
        """Save a photo to storage. Returns the file path."""
        ...

    @abstractmethod
    async def get_photo_path(self, session_id: str, index: int) -> Optional[str]:
        """Get the path to a stored photo."""
        ...

    @abstractmethod
    async def delete_session_photos(self, session_id: str) -> None:
        """Delete all photos for a session."""
        ...

    @abstractmethod
    async def save_composite(self, session_id: str, data: bytes) -> str:
        """Save a composite image. Returns the file path."""
        ...

    @abstractmethod
    async def get_composite_path(self, session_id: str) -> Optional[str]:
        """Get the path to a stored composite image."""
        ...

    @abstractmethod
    async def get_storage_info(self) -> StorageInfo:
        """Get current storage capacity and usage information."""
        ...

    @abstractmethod
    async def cleanup_old_sessions(self, days: int) -> int:
        """Delete session data older than the specified days. Returns count."""
        ...
