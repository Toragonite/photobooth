"""Printer service with CUPS integration and mock mode for development."""

import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from ...config import get_settings
from ...domain.value_objects import ErrorCode

settings = get_settings()
logger = logging.getLogger(__name__)


class PrinterState(str, Enum):
    """Printer state."""

    IDLE = "idle"
    PROCESSING = "processing"
    PRINTING = "printing"
    ERROR = "error"
    OFFLINE = "offline"


@dataclass
class PrinterInfo:
    """Printer information."""

    name: str
    model: str
    state: PrinterState
    state_message: str
    is_default: bool
    is_shared: bool


@dataclass
class PrintResult:
    """Result of a print operation."""

    success: bool
    job_id: Optional[int] = None
    error_code: Optional[ErrorCode] = None
    error_message: Optional[str] = None


class PrinterService:
    """Service for printer operations with CUPS or mock mode."""

    def __init__(self):
        self.mock_mode = settings.printer_mock_mode
        self.printer_name = settings.printer_name
        self._cups = None
        self._mock_job_counter = 1000

        if not self.mock_mode:
            try:
                import cups

                self._cups = cups.Connection()
                logger.info("CUPS connection established")
            except ImportError:
                logger.warning("pycups not installed, using mock mode")
                self.mock_mode = True
            except Exception as e:
                logger.error(f"Failed to connect to CUPS: {e}")
                self.mock_mode = True

        if self.mock_mode:
            logger.info("Printer service running in MOCK mode")

    def is_available(self) -> bool:
        """Check if printer is available."""
        if self.mock_mode:
            return True

        try:
            printers = self._cups.getPrinters()
            return self.printer_name in printers
        except Exception as e:
            logger.error(f"Failed to check printer availability: {e}")
            return False

    def get_printers(self) -> List[PrinterInfo]:
        """Get list of available printers."""
        if self.mock_mode:
            return [
                PrinterInfo(
                    name=self.printer_name,
                    model="Canon Selphy CP1500 (Mock)",
                    state=PrinterState.IDLE,
                    state_message="Ready",
                    is_default=True,
                    is_shared=False,
                )
            ]

        try:
            printers = self._cups.getPrinters()
            default = self._cups.getDefault()

            return [
                PrinterInfo(
                    name=name,
                    model=info.get("printer-make-and-model", "Unknown"),
                    state=self._map_cups_state(info.get("printer-state", 3)),
                    state_message=info.get("printer-state-message", ""),
                    is_default=name == default,
                    is_shared=info.get("printer-is-shared", False),
                )
                for name, info in printers.items()
            ]
        except Exception as e:
            logger.error(f"Failed to get printers: {e}")
            return []

    def get_printer_status(self, name: Optional[str] = None) -> Optional[PrinterInfo]:
        """Get status of a specific printer."""
        name = name or self.printer_name
        printers = self.get_printers()

        for printer in printers:
            if printer.name == name:
                return printer

        return None

    async def print_file(self, file_path: str, copies: int = 1) -> PrintResult:
        """Submit a print job."""
        if self.mock_mode:
            return await self._mock_print(file_path, copies)

        try:
            # Check printer is available
            status = self.get_printer_status()
            if not status:
                return PrintResult(
                    success=False,
                    error_code=ErrorCode.PRINTER_OFFLINE,
                    error_message="Printer not found",
                )

            if status.state == PrinterState.OFFLINE:
                return PrintResult(
                    success=False,
                    error_code=ErrorCode.PRINTER_OFFLINE,
                    error_message="Printer is offline",
                )

            # Submit job to CUPS
            options = {
                "copies": str(copies),
                "media": "Postcard.Fullbleed",  # Canon Selphy 4x6
                "print-quality": "5",  # High quality
            }

            job_id = self._cups.printFile(
                self.printer_name,
                file_path,
                "PhotoBooth Print",
                options,
            )

            logger.info(f"Print job submitted: {job_id}")
            return PrintResult(success=True, job_id=job_id)

        except Exception as e:
            logger.error(f"Print failed: {e}")
            return PrintResult(
                success=False,
                error_code=ErrorCode.CUPS_REJECTED,
                error_message=str(e),
            )

    async def get_job_status(self, job_id: int) -> Optional[dict]:
        """Get status of a print job."""
        if self.mock_mode:
            return await self._mock_job_status(job_id)

        try:
            jobs = self._cups.getJobs()
            if job_id in jobs:
                job = jobs[job_id]
                return {
                    "id": job_id,
                    "state": self._map_job_state(job.get("job-state", 0)),
                    "state_message": job.get("job-state-message", ""),
                    "completed": job.get("job-state", 0) >= 9,
                }

            # Job not in active jobs, check completed
            jobs = self._cups.getJobs(which_jobs="completed")
            if job_id in jobs:
                return {
                    "id": job_id,
                    "state": "completed",
                    "state_message": "Job completed",
                    "completed": True,
                }

            return None
        except Exception as e:
            logger.error(f"Failed to get job status: {e}")
            return None

    async def cancel_job(self, job_id: int) -> bool:
        """Cancel a print job."""
        if self.mock_mode:
            logger.info(f"Mock: Cancelled job {job_id}")
            return True

        try:
            self._cups.cancelJob(job_id)
            logger.info(f"Cancelled job {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel job: {e}")
            return False

    # Mock mode implementations
    async def _mock_print(self, file_path: str, copies: int) -> PrintResult:
        """Simulate a print job."""
        self._mock_job_counter += 1
        job_id = self._mock_job_counter

        logger.info(f"Mock print job {job_id}: {file_path} x{copies}")

        # Simulate processing time
        await asyncio.sleep(0.5)

        return PrintResult(success=True, job_id=job_id)

    async def _mock_job_status(self, job_id: int) -> dict:
        """Simulate job status progression."""
        # In mock mode, jobs complete quickly
        return {
            "id": job_id,
            "state": "completed",
            "state_message": "Mock job completed",
            "completed": True,
        }

    def _map_cups_state(self, state: int) -> PrinterState:
        """Map CUPS printer state to PrinterState."""
        # CUPS states: 3=idle, 4=processing, 5=stopped
        mapping = {
            3: PrinterState.IDLE,
            4: PrinterState.PROCESSING,
            5: PrinterState.ERROR,
        }
        return mapping.get(state, PrinterState.OFFLINE)

    def _map_job_state(self, state: int) -> str:
        """Map CUPS job state to string.

        CUPS job states: 3=pending, 4=held, 5=processing,
        6=stopped, 7=canceled, 8=aborted, 9=completed
        """
        mapping = {
            3: "pending",
            4: "held",
            5: "processing",
            6: "stopped",
            7: "cancelled",
            8: "failed",
            9: "completed",
        }
        return mapping.get(state, "unknown")
