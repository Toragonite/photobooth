"""Print job repository port."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from app.domain.entities import PrintJob
from app.domain.value_objects import JobId, PrintStatus, SessionId


class PrintJobRepository(ABC):
    """Abstract repository for PrintJob persistence."""

    @abstractmethod
    async def save(self, job: PrintJob) -> None:
        """Save or update a print job."""
        ...

    @abstractmethod
    async def get_by_id(self, job_id: JobId) -> Optional[PrintJob]:
        """Retrieve a print job by its ID."""
        ...

    @abstractmethod
    async def get_by_session(self, session_id: SessionId) -> List[PrintJob]:
        """Retrieve all print jobs for a session."""
        ...

    @abstractmethod
    async def get_pending_jobs(self) -> List[PrintJob]:
        """Retrieve all pending print jobs."""
        ...

    @abstractmethod
    async def get_retry_jobs(self, before: datetime) -> List[PrintJob]:
        """Retrieve jobs scheduled for retry before the given time."""
        ...

    @abstractmethod
    async def get_history(
        self, limit: int, offset: int, status_filter: Optional[PrintStatus] = None
    ) -> List[PrintJob]:
        """Retrieve print job history with pagination."""
        ...

    @abstractmethod
    async def count_by_status(self, status: PrintStatus) -> int:
        """Count jobs with a specific status."""
        ...

    @abstractmethod
    async def get_active_jobs(self) -> List[PrintJob]:
        """Retrieve all active (non-terminal) print jobs."""
        ...
