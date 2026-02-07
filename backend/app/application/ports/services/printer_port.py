"""Printer service port."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class PrintResult:
    """Result of a print operation."""
    success: bool
    cups_job_id: Optional[int] = None
    printer_name: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class PrinterStatus:
    """Current status of a single printer."""
    name: str
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
    async def print_image(
        self, image_path: str, copies: int = 1, printer_name: Optional[str] = None
    ) -> PrintResult:
        """Submit an image for printing to a specific printer."""
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
    async def get_printer_status(self, printer_name: Optional[str] = None) -> PrinterStatus:
        """Get status of a specific printer (or primary printer if None)."""
        ...

    @abstractmethod
    async def get_all_printer_statuses(self) -> List[PrinterStatus]:
        """Get statuses of all configured printers."""
        ...

    @abstractmethod
    async def is_ready(self, printer_name: Optional[str] = None) -> bool:
        """Check if a specific printer (or any printer) is ready."""
        ...

    @abstractmethod
    async def select_printer(self) -> Optional[str]:
        """Select the best available printer based on configured strategy."""
        ...
