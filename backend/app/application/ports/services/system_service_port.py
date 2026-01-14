"""System service port."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class SystemHealth:
    """Overall system health information."""
    overall: str  # "healthy", "degraded", "critical"
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    temperature: Optional[float] = None

    @property
    def is_healthy(self) -> bool:
        return self.overall == "healthy"


@dataclass
class LogEntry:
    """A single log entry."""
    timestamp: str
    level: str
    source: str
    message: str


class SystemServicePort(ABC):
    """Abstract port for system-level operations."""

    @abstractmethod
    async def get_health(self) -> SystemHealth:
        """Get current system health metrics."""
        ...

    @abstractmethod
    async def restart_service(self, service_name: str) -> bool:
        """Restart a system service."""
        ...

    @abstractmethod
    async def reboot_system(self, delay_seconds: int = 0) -> bool:
        """Reboot the system."""
        ...

    @abstractmethod
    async def get_logs(
        self,
        source: str,
        limit: int = 100,
        level: Optional[str] = None,
        since: Optional[datetime] = None,
    ) -> List[LogEntry]:
        """Retrieve system logs."""
        ...

    @abstractmethod
    async def cancel_scheduled_reboot(self) -> bool:
        """Cancel a scheduled reboot."""
        ...
