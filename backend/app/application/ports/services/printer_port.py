"""Printer service port."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class PrintResult:
    """Result of a print operation."""
    success: bool
    cups_job_id: Optional[int] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class PrinterStatus:
    """Current status of the printer."""
    connected: bool
    status: str
    paper_status: str
    ink_status: str
    error_message: Optional[str] = None
    queue_length: int = 0

    @property
    def is_ready(self) -> bool:
        return self.connected and self.status == "ready"


class PrinterPort(ABC):
    """Abstract port for printer operations."""

    @abstractmethod
    async def print_image(self, image_path: str, copies: int = 1) -> PrintResult:
        """Submit an image for printing."""
        ...

    @abstractmethod
    async def get_job_status(self, cups_job_id: int) -> str:
        """Get the current status of a CUPS print job."""
        ...

    @abstractmethod
    async def cancel_job(self, cups_job_id: int) -> bool:
        """Cancel a CUPS print job."""
        ...

    @abstractmethod
    async def get_printer_status(self) -> PrinterStatus:
        """Get the current printer status."""
        ...

    @abstractmethod
    async def is_ready(self) -> bool:
        """Check if the printer is ready to accept jobs."""
        ...
