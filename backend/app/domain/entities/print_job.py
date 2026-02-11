"""PrintJob entity."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Tuple

from ..exceptions import PrintJobError
from ..value_objects import ErrorCode, JobId, PrintStatus, SessionId


@dataclass
class PrintJob:
    """A print job with full lifecycle and multi-copy tracking."""

    id: JobId
    session_id: SessionId
    status: PrintStatus
    copies: int
    cups_job_id: Optional[int] = None
    printer_name: Optional[str] = None
    error_code: Optional[ErrorCode] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    next_retry_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None

    # Multi-copy tracking fields
    completed_copies: int = 0  # Number of successfully printed copies
    current_copy: int = 0  # Currently processing copy (1-indexed for display)
    cups_job_ids: List[int] = field(default_factory=list)  # History of all CUPS job IDs

    MAX_RETRIES = 3
    MAX_COPIES = 10
    TIMEOUT_SECONDS = 120

    def __post_init__(self):
        if not 1 <= self.copies <= self.MAX_COPIES:
            raise PrintJobError(f"Copies must be between 1 and {self.MAX_COPIES}")

    @classmethod
    def create(
        cls,
        session_id: SessionId,
        copies: int = 1,
        printer_name: Optional[str] = None,
    ) -> "PrintJob":
        """Create a new print job."""
        return cls(
            id=JobId.generate(),
            session_id=session_id,
            status=PrintStatus.PENDING,
            copies=copies,
            printer_name=printer_name,
        )

    def start_processing(self) -> None:
        """Start processing the print job."""
        if self.status != PrintStatus.PENDING:
            raise PrintJobError(f"Cannot start job in {self.status} state")
        self.status = PrintStatus.PROCESSING
        self.started_at = datetime.now()

    def mark_printing(self, cups_job_id: int) -> None:
        """Mark job as printing with CUPS job ID."""
        if self.status != PrintStatus.PROCESSING:
            raise PrintJobError(f"Cannot mark as printing from {self.status} state")
        self.status = PrintStatus.PRINTING
        self.cups_job_id = cups_job_id

    def mark_completed(self) -> None:
        """Mark job as completed."""
        if self.status != PrintStatus.PRINTING:
            raise PrintJobError(f"Cannot complete job from {self.status} state")
        self.status = PrintStatus.COMPLETED
        self.completed_at = datetime.now()

    def mark_error(
        self,
        error_code: ErrorCode,
        error_message: str,
    ) -> None:
        """Mark job as error with details."""
        self.error_code = error_code
        self.error_message = error_message

        if self.can_auto_retry:
            self.status = PrintStatus.RETRY_PENDING
            self.retry_count += 1
        else:
            self.status = PrintStatus.FAILED

    def schedule_retry(self, retry_at: datetime) -> None:
        """Schedule a retry attempt."""
        if self.status != PrintStatus.RETRY_PENDING:
            raise PrintJobError("Can only schedule retry for RETRY_PENDING jobs")
        self.next_retry_at = retry_at

    def start_retry(self) -> None:
        """Start a retry attempt."""
        if self.status != PrintStatus.RETRY_PENDING:
            raise PrintJobError("Can only retry RETRY_PENDING jobs")
        self.status = PrintStatus.PROCESSING
        self.next_retry_at = None
        self.error_code = None
        self.error_message = None

    def user_retry(self) -> None:
        """User-initiated retry (resets counter)."""
        if self.status != PrintStatus.FAILED:
            raise PrintJobError("Can only retry failed jobs")

        self.retry_count = 0
        self.error_code = None
        self.error_message = None
        self.status = PrintStatus.PENDING

    def cancel(self) -> None:
        """Cancel the job."""
        if self.status in (PrintStatus.COMPLETED, PrintStatus.CANCELLED):
            raise PrintJobError(f"Cannot cancel job in {self.status} state")

        self.status = PrintStatus.CANCELLED
        self.cancelled_at = datetime.now()

    @property
    def can_auto_retry(self) -> bool:
        """Check if auto-retry is possible."""
        return (
            self.error_code is not None
            and self.error_code.is_retryable
            and self.retry_count < self.MAX_RETRIES
        )

    @property
    def needs_user_action(self) -> bool:
        """Check if user action is needed."""
        return self.status == PrintStatus.FAILED

    @property
    def is_terminal(self) -> bool:
        """Check if job is in terminal state."""
        return self.status in (
            PrintStatus.COMPLETED,
            PrintStatus.CANCELLED,
            PrintStatus.FAILED,
        )

    @property
    def progress_percent(self) -> int:
        """Calculate progress percentage based on completed copies."""
        if self.status == PrintStatus.COMPLETED:
            return 100
        if self.status in (PrintStatus.FAILED, PrintStatus.CANCELLED):
            return 0
        if self.copies == 0:
            return 0

        # Base progress on completed copies
        copy_progress = (self.completed_copies / self.copies) * 100

        # Add partial progress for current copy being printed
        if self.status == PrintStatus.PRINTING and self.current_copy > 0:
            copy_progress += (1 / self.copies) * 50  # 50% of current copy

        return min(int(copy_progress), 99)

    @property
    def copy_progress(self) -> Tuple[int, int]:
        """Return (completed, total) copies."""
        return (self.completed_copies, self.copies)

    @property
    def copy_progress_str(self) -> str:
        """Return copy progress as string, e.g., '1/3'."""
        return f"{self.completed_copies}/{self.copies}"

    def start_copy(self, copy_number: int) -> None:
        """Start processing a specific copy."""
        self.current_copy = copy_number
        if self.status == PrintStatus.PENDING:
            self.status = PrintStatus.PROCESSING
            self.started_at = datetime.now()
        elif self.status not in (PrintStatus.PROCESSING, PrintStatus.PRINTING):
            raise PrintJobError(f"Cannot start copy in {self.status} state")

    def complete_copy(self, cups_job_id: Optional[int] = None) -> None:
        """Mark current copy as complete."""
        self.completed_copies += 1
        if cups_job_id and cups_job_id not in self.cups_job_ids:
            self.cups_job_ids.append(cups_job_id)

        # Check if all copies are done
        if self.completed_copies >= self.copies:
            self.status = PrintStatus.COMPLETED
            self.completed_at = datetime.now()
        else:
            # Ready for next copy
            self.status = PrintStatus.PROCESSING

    def update_cups_job_id(self, cups_job_id: int) -> None:
        """Update the current CUPS job ID."""
        self.cups_job_id = cups_job_id
        if cups_job_id not in self.cups_job_ids:
            self.cups_job_ids.append(cups_job_id)
        self.status = PrintStatus.PRINTING

    def user_retry_remaining(self) -> None:
        """User-initiated retry for remaining copies only (doesn't reset completed_copies)."""
        if self.status != PrintStatus.FAILED:
            raise PrintJobError("Can only retry failed jobs")

        # Don't reset completed_copies - continue from where we left off
        self.retry_count = 0
        self.error_code = None
        self.error_message = None
        self.status = PrintStatus.PENDING
