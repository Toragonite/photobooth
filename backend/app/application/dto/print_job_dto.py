"""Print job-related Data Transfer Objects."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class PrintJobDTO:
    """Data transfer object for a print job."""
    job_id: str
    session_id: str
    status: str
    copies: int
    progress: int
    # Multi-copy tracking fields
    completed_copies: int = 0
    current_copy: int = 0
    copy_progress: str = "0/0"  # e.g., "1/3", "2/3"
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
