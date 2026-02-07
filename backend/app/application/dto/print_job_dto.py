"""Print job-related Data Transfer Objects."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class PrintJobDTO:
    """Data transfer object for a print job."""
    id: str
    session_id: str
    status: str
    copies: int
    progress: int
    printer_name: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class CreatePrintJobRequest:
    """Request to create a new print job."""
    session_id: str
    copies: int = 1


@dataclass
class PrintJobStatusResponse:
    """Response for print job status queries."""
    job_id: str
    status: str
    progress: int
    error_code: Optional[str] = None
    error_message: Optional[str] = None
