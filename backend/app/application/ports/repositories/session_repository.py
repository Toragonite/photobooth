"""Session repository port."""

from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entities import PhotoSession
from app.domain.value_objects import SessionId


class SessionRepository(ABC):
    """Abstract repository for PhotoSession persistence."""

    @abstractmethod
    async def save(self, session: PhotoSession) -> None:
        """Save or update a photo session."""
        ...

    @abstractmethod
    async def get_by_id(self, session_id: SessionId) -> Optional[PhotoSession]:
        """Retrieve a photo session by its ID."""
        ...

    @abstractmethod
    async def get_active_sessions(self) -> List[PhotoSession]:
        """Retrieve all active sessions."""
        ...

    @abstractmethod
    async def delete(self, session_id: SessionId) -> None:
        """Delete a photo session."""
        ...

    @abstractmethod
    async def get_expired_sessions(self, expiry_minutes: int) -> List[PhotoSession]:
        """Retrieve sessions that have expired."""
        ...
