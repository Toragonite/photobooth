"""Unit tests for PrintJob entity."""

from datetime import datetime

import pytest

from app.domain.entities import PrintJob
from app.domain.exceptions import PrintJobError
from app.domain.value_objects import ErrorCode, PrintStatus


class TestPrintJobCreation:
    """Tests for PrintJob creation."""

    def test_create_job_with_defaults(self, session_id):
        """Job is created with default values."""
        job = PrintJob.create(session_id=session_id, copies=1)

        assert job.id is not None
        assert job.session_id == session_id
        assert job.status == PrintStatus.PENDING
        assert job.copies == 1
        assert job.retry_count == 0
        assert job.cups_job_id is None
        assert job.error_code is None
        assert job.error_message is None

    def test_create_job_with_multiple_copies(self, session_id):
        """Job can be created with multiple copies."""
        job = PrintJob.create(session_id=session_id, copies=3)

        assert job.copies == 3

    def test_invalid_copies_raises_error(self, session_id):
        """Copies must be between 1 and 3."""
        with pytest.raises(PrintJobError):
            PrintJob.create(session_id=session_id, copies=0)

        with pytest.raises(PrintJobError):
            PrintJob.create(session_id=session_id, copies=5)

    def test_create_generates_unique_ids(self, session_id):
        """Each job gets a unique ID."""
        job1 = PrintJob.create(session_id=session_id, copies=1)
        job2 = PrintJob.create(session_id=session_id, copies=1)

        assert job1.id != job2.id


class TestPrintJobLifecycle:
    """Tests for print job lifecycle transitions."""

    def test_start_processing(self, sample_print_job):
        """Starting processing changes status."""
        sample_print_job.start_processing()

        assert sample_print_job.status == PrintStatus.PROCESSING
        assert sample_print_job.started_at is not None

    def test_cannot_start_non_pending_job(self, processing_print_job):
        """Cannot start a job that's already started."""
        with pytest.raises(PrintJobError, match="PROCESSING"):
            processing_print_job.start_processing()

    def test_mark_printing_with_cups_id(self, processing_print_job):
        """Marking as printing sets CUPS job ID."""
        processing_print_job.mark_printing(cups_job_id=12345)

        assert processing_print_job.status == PrintStatus.PRINTING
        assert processing_print_job.cups_job_id == 12345

    def test_cannot_mark_printing_from_pending(self, sample_print_job):
        """Cannot mark as printing without processing first."""
        with pytest.raises(PrintJobError, match="PENDING"):
            sample_print_job.mark_printing(cups_job_id=12345)

    def test_mark_completed(self, printing_print_job):
        """Completing a job sets status and timestamp."""
        printing_print_job.mark_completed()

        assert printing_print_job.status == PrintStatus.COMPLETED
        assert printing_print_job.completed_at is not None

    def test_cannot_complete_non_printing_job(self, processing_print_job):
        """Cannot complete a job that's not printing."""
        with pytest.raises(PrintJobError, match="PROCESSING"):
            processing_print_job.mark_completed()


class TestPrintJobRetry:
    """Tests for print job retry logic."""

    def test_retryable_error_sets_retry_pending(self, printing_print_job):
        """Retryable error puts job in RETRY_PENDING state."""
        printing_print_job.mark_error(
            ErrorCode.PRINTER_OFFLINE,
            "Printer disconnected",
        )

        assert printing_print_job.status == PrintStatus.RETRY_PENDING
        assert printing_print_job.retry_count == 1
        assert printing_print_job.error_code == ErrorCode.PRINTER_OFFLINE
        assert printing_print_job.error_message == "Printer disconnected"

    def test_non_retryable_error_fails_job(self, printing_print_job):
        """Non-retryable error fails the job."""
        printing_print_job.mark_error(
            ErrorCode.PRINTER_PAPER_JAM,
            "Paper jam",
        )

        assert printing_print_job.status == PrintStatus.FAILED
        assert printing_print_job.error_code == ErrorCode.PRINTER_PAPER_JAM

    def test_max_retries_exhausted(self, printing_print_job):
        """Job fails when max retries exhausted."""
        # Simulate being at max retries
        printing_print_job.retry_count = PrintJob.MAX_RETRIES

        printing_print_job.mark_error(
            ErrorCode.PRINTER_OFFLINE,
            "Offline",
        )

        assert printing_print_job.status == PrintStatus.FAILED

    def test_schedule_retry(self, session_id):
        """Can schedule retry time."""
        job = PrintJob.create(session_id=session_id, copies=1)
        job.start_processing()
        job.mark_printing(cups_job_id=123)
        job.mark_error(ErrorCode.PRINTER_OFFLINE, "Offline")

        retry_time = datetime.now()
        job.schedule_retry(retry_time)

        assert job.next_retry_at == retry_time

    def test_cannot_schedule_retry_for_non_retry_pending(self, sample_print_job):
        """Can only schedule retry for RETRY_PENDING jobs."""
        with pytest.raises(PrintJobError, match="RETRY_PENDING"):
            sample_print_job.schedule_retry(datetime.now())

    def test_start_retry(self, session_id):
        """Starting retry clears error and changes status."""
        job = PrintJob.create(session_id=session_id, copies=1)
        job.start_processing()
        job.mark_printing(cups_job_id=123)
        job.mark_error(ErrorCode.PRINTER_OFFLINE, "Offline")

        job.start_retry()

        assert job.status == PrintStatus.PROCESSING
        assert job.next_retry_at is None
        assert job.error_code is None
        assert job.error_message is None

    def test_user_retry_resets_counter(self, session_id):
        """User-initiated retry resets retry counter."""
        job = PrintJob.create(session_id=session_id, copies=1)
        job.start_processing()
        job.mark_printing(cups_job_id=123)
        job.retry_count = PrintJob.MAX_RETRIES
        job.mark_error(ErrorCode.PRINTER_PAPER_JAM, "Jam")  # Non-retryable

        assert job.status == PrintStatus.FAILED

        job.user_retry()

        assert job.status == PrintStatus.PENDING
        assert job.retry_count == 0
        assert job.error_code is None

    def test_cannot_user_retry_non_failed(self, sample_print_job):
        """User retry only works for failed jobs."""
        with pytest.raises(PrintJobError, match="failed"):
            sample_print_job.user_retry()


class TestPrintJobCancel:
    """Tests for cancelling print jobs."""

    def test_cancel_pending_job(self, sample_print_job):
        """Can cancel a pending job."""
        sample_print_job.cancel()

        assert sample_print_job.status == PrintStatus.CANCELLED
        assert sample_print_job.cancelled_at is not None

    def test_cancel_processing_job(self, processing_print_job):
        """Can cancel a processing job."""
        processing_print_job.cancel()

        assert processing_print_job.status == PrintStatus.CANCELLED

    def test_cancel_printing_job(self, printing_print_job):
        """Can cancel a printing job."""
        printing_print_job.cancel()

        assert printing_print_job.status == PrintStatus.CANCELLED

    def test_cannot_cancel_completed_job(self, printing_print_job):
        """Cannot cancel a completed job."""
        printing_print_job.mark_completed()

        with pytest.raises(PrintJobError, match="COMPLETED"):
            printing_print_job.cancel()

    def test_cannot_cancel_already_cancelled(self, sample_print_job):
        """Cannot cancel an already cancelled job."""
        sample_print_job.cancel()

        with pytest.raises(PrintJobError, match="CANCELLED"):
            sample_print_job.cancel()


class TestPrintJobProperties:
    """Tests for print job properties."""

    def test_can_auto_retry_with_retryable_error(self, session_id):
        """can_auto_retry is True for retryable errors with retries left."""
        job = PrintJob.create(session_id=session_id, copies=1)
        job.error_code = ErrorCode.PRINTER_OFFLINE

        assert job.can_auto_retry is True

    def test_can_auto_retry_false_for_non_retryable(self, session_id):
        """can_auto_retry is False for non-retryable errors."""
        job = PrintJob.create(session_id=session_id, copies=1)
        job.error_code = ErrorCode.PRINTER_PAPER_JAM

        assert job.can_auto_retry is False

    def test_can_auto_retry_false_when_exhausted(self, session_id):
        """can_auto_retry is False when retries exhausted."""
        job = PrintJob.create(session_id=session_id, copies=1)
        job.error_code = ErrorCode.PRINTER_OFFLINE
        job.retry_count = PrintJob.MAX_RETRIES

        assert job.can_auto_retry is False

    def test_needs_user_action(self, session_id):
        """needs_user_action is True for failed jobs."""
        job = PrintJob.create(session_id=session_id, copies=1)
        job.start_processing()
        job.mark_printing(cups_job_id=123)
        job.mark_error(ErrorCode.PRINTER_PAPER_JAM, "Jam")

        assert job.needs_user_action is True

    def test_is_terminal_states(self, session_id):
        """is_terminal is True for terminal states."""
        job = PrintJob.create(session_id=session_id, copies=1)
        assert job.is_terminal is False

        job.start_processing()
        assert job.is_terminal is False

        job.mark_printing(cups_job_id=123)
        assert job.is_terminal is False

        job.mark_completed()
        assert job.is_terminal is True

    def test_progress_percent(self, session_id):
        """progress_percent returns correct values."""
        job = PrintJob.create(session_id=session_id, copies=1)
        assert job.progress_percent == 0

        job.start_processing()
        assert job.progress_percent == 25

        job.mark_printing(cups_job_id=123)
        assert job.progress_percent == 75

        job.mark_completed()
        assert job.progress_percent == 100


class TestErrorCodeProperties:
    """Tests for ErrorCode value object."""

    def test_retryable_errors(self):
        """Check which errors are retryable."""
        retryable = [
            ErrorCode.PRINTER_OFFLINE,
            ErrorCode.PRINTER_BUSY,
            ErrorCode.PRINTER_PAPER_EMPTY,
            ErrorCode.PRINTER_INK_EMPTY,
            ErrorCode.CUPS_UNAVAILABLE,
            ErrorCode.CUPS_REJECTED,
        ]

        for code in retryable:
            assert code.is_retryable is True, f"{code} should be retryable"

    def test_non_retryable_errors(self):
        """Check which errors are not retryable."""
        non_retryable = [
            ErrorCode.PRINTER_PAPER_JAM,
            ErrorCode.PRINTER_DOOR_OPEN,
            ErrorCode.PROCESSING_ERROR,
            ErrorCode.INVALID_IMAGE,
            ErrorCode.STORAGE_FULL,
            ErrorCode.TIMEOUT,
        ]

        for code in non_retryable:
            assert code.is_retryable is False, f"{code} should not be retryable"

    def test_user_messages(self):
        """Error codes have user messages."""
        assert ErrorCode.PRINTER_OFFLINE.user_message is not None
        assert ErrorCode.PRINTER_OFFLINE.user_message_ko is not None
