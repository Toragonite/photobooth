"""Central Print Queue Manager for multi-copy and multi-printer support.

This service manages a central queue of copy tasks that are dynamically
assigned to available printers. Each printer has a worker that pulls tasks
from the queue when it becomes idle.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Dict, List, Optional

if TYPE_CHECKING:
    from .printer_service import PrinterService

logger = logging.getLogger(__name__)


class CopyStatus(str, Enum):
    """Status of an individual copy task."""

    QUEUED = "queued"
    PRINTING = "printing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class CopyTask:
    """Represents a single copy to be printed."""

    job_id: str
    copy_number: int
    total_copies: int
    file_path: str
    status: CopyStatus = CopyStatus.QUEUED
    printer_name: Optional[str] = None
    cups_job_id: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class PrinterWorker:
    """Tracks the state of a printer worker."""

    name: str
    is_busy: bool = False
    current_task: Optional[CopyTask] = None
    completed_count: int = 0
    failed_count: int = 0
    last_activity: Optional[datetime] = None


@dataclass
class QueueEvent:
    """An event in the print queue for logging."""

    timestamp: datetime
    job_id: str
    event_type: str  # copy_queued, copy_started, copy_completed, copy_failed, job_completed
    message: str
    printer_name: Optional[str] = None
    copy_number: Optional[int] = None
    total_copies: Optional[int] = None


class PrintQueueManager:
    """Central print queue manager (singleton).

    Manages a FIFO queue of copy tasks that are dynamically assigned to
    available printers. Each printer runs a worker loop that pulls tasks
    from the shared queue when idle.

    Features:
    - Dynamic printer assignment (no pre-allocation)
    - FIFO ordering across all jobs
    - Real-time status tracking
    - Event logging for admin dashboard
    """

    _instance: Optional["PrintQueueManager"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self._queue: asyncio.Queue[CopyTask] = asyncio.Queue()
        self._workers: Dict[str, PrinterWorker] = {}
        self._active_tasks: Dict[str, CopyTask] = {}  # task_id -> CopyTask
        self._job_copies: Dict[str, List[CopyTask]] = {}  # job_id -> [CopyTask]
        self._running = False
        self._worker_tasks: List[asyncio.Task] = []
        self._printer_service: Optional["PrinterService"] = None
        self._lock = asyncio.Lock()
        self._events: List[QueueEvent] = []  # Recent events for logging
        self._max_events = 100  # Keep last 100 events

    async def start(
        self, printer_service: "PrinterService", printer_names: List[str]
    ) -> None:
        """Start the queue manager with printer workers.

        Args:
            printer_service: The printer service instance
            printer_names: List of printer names to create workers for
        """
        if self._running:
            logger.warning("PrintQueueManager already running")
            return

        self._printer_service = printer_service
        self._running = True

        # Create a worker for each printer
        for name in printer_names:
            self._workers[name] = PrinterWorker(name=name)
            task = asyncio.create_task(self._worker_loop(name))
            self._worker_tasks.append(task)
            logger.info(f"Created worker for printer: {name}")

        logger.info(
            f"PrintQueueManager started with {len(printer_names)} printer workers"
        )

    async def stop(self) -> None:
        """Stop the queue manager and all workers."""
        self._running = False

        # Cancel all worker tasks
        for task in self._worker_tasks:
            task.cancel()

        # Wait for cancellation
        if self._worker_tasks:
            await asyncio.gather(*self._worker_tasks, return_exceptions=True)

        self._worker_tasks.clear()
        logger.info("PrintQueueManager stopped")

    async def refresh_workers(self, printer_names: List[str]) -> None:
        """Refresh workers when printer list changes.

        Args:
            printer_names: New list of printer names
        """
        async with self._lock:
            current_names = set(self._workers.keys())
            new_names = set(printer_names)

            # Remove workers for removed printers
            for name in current_names - new_names:
                logger.info(f"Removing worker for printer: {name}")
                del self._workers[name]

            # Add workers for new printers
            for name in new_names - current_names:
                self._workers[name] = PrinterWorker(name=name)
                task = asyncio.create_task(self._worker_loop(name))
                self._worker_tasks.append(task)
                logger.info(f"Added worker for printer: {name}")

    async def submit_job(
        self, job_id: str, file_path: str, copies: int
    ) -> List[str]:
        """Submit a print job to the queue.

        Creates CopyTask entries for each copy and adds them to the queue.

        Args:
            job_id: The print job ID
            file_path: Path to the composite image file
            copies: Number of copies to print

        Returns:
            List of task IDs (job_id_copyN)
        """
        copy_tasks = []
        task_ids = []

        for i in range(1, copies + 1):
            task = CopyTask(
                job_id=job_id,
                copy_number=i,
                total_copies=copies,
                file_path=file_path,
            )
            task_id = f"{job_id}_copy{i}"
            self._active_tasks[task_id] = task
            copy_tasks.append(task)
            task_ids.append(task_id)
            await self._queue.put(task)

            self._add_event(
                job_id=job_id,
                event_type="copy_queued",
                message=f"Copy {i}/{copies} queued",
                copy_number=i,
                total_copies=copies,
            )

        self._job_copies[job_id] = copy_tasks

        logger.info(f"Job {job_id} submitted: {copies} copies queued")
        return task_ids

    async def cancel_job(self, job_id: str) -> int:
        """Cancel all pending copies for a job.

        Args:
            job_id: The print job ID to cancel

        Returns:
            Number of copies cancelled
        """
        cancelled = 0

        if job_id not in self._job_copies:
            return 0

        for task in self._job_copies[job_id]:
            if task.status == CopyStatus.QUEUED:
                task.status = CopyStatus.FAILED
                task.error_message = "Cancelled by user"
                cancelled += 1

        if cancelled > 0:
            self._add_event(
                job_id=job_id,
                event_type="job_cancelled",
                message=f"Job cancelled ({cancelled} copies pending)",
            )
            logger.info(f"Job {job_id} cancelled: {cancelled} copies")

        return cancelled

    async def _worker_loop(self, printer_name: str) -> None:
        """Worker loop for a printer - pulls tasks from queue and processes them.

        Args:
            printer_name: The name of the printer this worker manages
        """
        worker = self._workers.get(printer_name)
        if not worker:
            return

        logger.info(f"[{printer_name}] Worker started")

        while self._running:
            try:
                # Wait for a task from the queue
                task = await asyncio.wait_for(self._queue.get(), timeout=1.0)

                # Check if task was already cancelled
                if task.status == CopyStatus.FAILED:
                    self._queue.task_done()
                    continue

                # Mark worker as busy
                worker.is_busy = True
                worker.current_task = task
                worker.last_activity = datetime.now()

                # Update task status
                task.status = CopyStatus.PRINTING
                task.printer_name = printer_name
                task.started_at = datetime.now()

                logger.info(
                    f"[{printer_name}] Starting {task.job_id} "
                    f"copy {task.copy_number}/{task.total_copies}"
                )

                self._add_event(
                    job_id=task.job_id,
                    event_type="copy_started",
                    message=f"Copy {task.copy_number}/{task.total_copies} started",
                    printer_name=printer_name,
                    copy_number=task.copy_number,
                    total_copies=task.total_copies,
                )

                # Execute the print
                success = await self._execute_print(task, printer_name)

                if success:
                    task.status = CopyStatus.COMPLETED
                    task.completed_at = datetime.now()
                    worker.completed_count += 1

                    logger.info(
                        f"[{printer_name}] Completed {task.job_id} "
                        f"copy {task.copy_number}/{task.total_copies}"
                    )

                    self._add_event(
                        job_id=task.job_id,
                        event_type="copy_completed",
                        message=f"Copy {task.copy_number}/{task.total_copies} completed",
                        printer_name=printer_name,
                        copy_number=task.copy_number,
                        total_copies=task.total_copies,
                    )
                else:
                    task.status = CopyStatus.FAILED
                    worker.failed_count += 1

                    logger.error(
                        f"[{printer_name}] Failed {task.job_id} "
                        f"copy {task.copy_number}/{task.total_copies}: {task.error_message}"
                    )

                    self._add_event(
                        job_id=task.job_id,
                        event_type="copy_failed",
                        message=f"Copy {task.copy_number}/{task.total_copies} failed: {task.error_message}",
                        printer_name=printer_name,
                        copy_number=task.copy_number,
                        total_copies=task.total_copies,
                    )

                # Clear worker state
                worker.is_busy = False
                worker.current_task = None
                self._queue.task_done()

                # Check job completion
                await self._check_job_completion(task.job_id)

            except asyncio.TimeoutError:
                # No task available, continue waiting
                continue
            except asyncio.CancelledError:
                logger.info(f"[{printer_name}] Worker cancelled")
                break
            except Exception as e:
                logger.exception(f"[{printer_name}] Worker error: {e}")
                if worker:
                    worker.is_busy = False
                    worker.current_task = None

        logger.info(f"[{printer_name}] Worker stopped")

    async def _execute_print(self, task: CopyTask, printer_name: str) -> bool:
        """Execute a single copy print.

        Args:
            task: The copy task to execute
            printer_name: The printer to use

        Returns:
            True if successful, False otherwise
        """
        if not self._printer_service:
            task.error_message = "Printer service not available"
            return False

        try:
            # Submit single copy to printer
            result = await self._printer_service.print_single_copy(
                task.file_path, printer_name
            )

            if not result.success:
                task.error_message = result.error_message or "Print submission failed"
                return False

            task.cups_job_id = result.job_id

            # Wait for CUPS job to complete
            success, status_msg = await self._printer_service.wait_for_job_completion(
                result.job_id, timeout_seconds=120
            )

            if not success:
                task.error_message = f"Print failed: {status_msg}"
                return False

            return True

        except Exception as e:
            task.error_message = str(e)
            logger.exception(f"Error executing print for {task.job_id}: {e}")
            return False

    async def _check_job_completion(self, job_id: str) -> None:
        """Check if all copies of a job are complete and update status.

        Args:
            job_id: The job ID to check
        """
        if job_id not in self._job_copies:
            return

        copies = self._job_copies[job_id]
        completed = sum(1 for c in copies if c.status == CopyStatus.COMPLETED)
        failed = sum(1 for c in copies if c.status == CopyStatus.FAILED)
        total = len(copies)

        # Get CUPS job IDs for this job
        cups_job_ids = [c.cups_job_id for c in copies if c.cups_job_id]

        # Update job progress in database
        await self._update_job_progress(
            job_id=job_id,
            completed_copies=completed,
            current_copy=completed + 1 if completed < total else total,
            cups_job_ids=cups_job_ids,
        )

        # Check if all copies are processed
        if completed + failed == total:
            if failed == 0:
                # All copies successful
                self._add_event(
                    job_id=job_id,
                    event_type="job_completed",
                    message=f"Job completed: {completed}/{total} copies printed",
                )
                await self._mark_job_completed(job_id)
                logger.info(f"Job {job_id} completed: {completed}/{total} copies")
            else:
                # Some copies failed
                self._add_event(
                    job_id=job_id,
                    event_type="job_failed",
                    message=f"Job failed: {completed}/{total} copies printed, {failed} failed",
                )
                await self._mark_job_failed(
                    job_id=job_id,
                    error_message=f"{failed}/{total} copies failed",
                    completed_copies=completed,
                )
                logger.error(
                    f"Job {job_id} failed: {completed}/{total} printed, {failed} failed"
                )

            # Clean up job tracking (keep for a while for status queries)
            # Don't remove immediately to allow status queries
            # self._job_copies.pop(job_id, None)

    # ─────────────────────────────────────────────────────────────────
    # Database update methods (direct DB access to avoid callback issues)
    # ─────────────────────────────────────────────────────────────────

    async def _update_job_progress(
        self,
        job_id: str,
        completed_copies: int,
        current_copy: int,
        cups_job_ids: List[int],
    ) -> None:
        """Update job progress in database."""
        from app.domain.value_objects import JobId, PrintStatus
        from app.infrastructure.database import async_session
        from app.infrastructure.repositories import SQLAlchemyPrintJobRepository

        try:
            async with async_session() as db:
                repo = SQLAlchemyPrintJobRepository(db)
                job = await repo.get_by_id(JobId(job_id))
                if job:
                    job.completed_copies = completed_copies
                    job.current_copy = current_copy
                    job.cups_job_ids = cups_job_ids
                    if cups_job_ids:
                        job.cups_job_id = cups_job_ids[-1]  # Latest CUPS job ID
                    if job.status == PrintStatus.PENDING:
                        job.status = PrintStatus.PRINTING
                    await repo.save(job)
                    await db.commit()
                    logger.debug(
                        f"Job {job_id} progress updated: {completed_copies}/{job.copies}"
                    )
        except Exception as e:
            logger.error(f"Error updating job progress for {job_id}: {e}")

    async def _mark_job_completed(self, job_id: str) -> None:
        """Mark job as completed in database."""
        from app.domain.value_objects import JobId, PrintStatus
        from app.infrastructure.database import async_session
        from app.infrastructure.repositories import SQLAlchemyPrintJobRepository

        try:
            async with async_session() as db:
                repo = SQLAlchemyPrintJobRepository(db)
                job = await repo.get_by_id(JobId(job_id))
                if job:
                    job.status = PrintStatus.COMPLETED
                    job.completed_copies = job.copies
                    job.completed_at = datetime.now()
                    await repo.save(job)
                    await db.commit()
                    logger.info(f"Job {job_id} marked as completed")
        except Exception as e:
            logger.error(f"Error marking job {job_id} as completed: {e}")

    async def _mark_job_failed(
        self,
        job_id: str,
        error_message: str,
        completed_copies: int,
    ) -> None:
        """Mark job as failed in database."""
        from app.domain.value_objects import ErrorCode, JobId, PrintStatus
        from app.infrastructure.database import async_session
        from app.infrastructure.repositories import SQLAlchemyPrintJobRepository

        try:
            async with async_session() as db:
                repo = SQLAlchemyPrintJobRepository(db)
                job = await repo.get_by_id(JobId(job_id))
                if job:
                    job.status = PrintStatus.FAILED
                    job.completed_copies = completed_copies
                    job.error_code = ErrorCode.CUPS_REJECTED
                    job.error_message = error_message
                    await repo.save(job)
                    await db.commit()
                    logger.error(f"Job {job_id} marked as failed: {error_message}")
        except Exception as e:
            logger.error(f"Error marking job {job_id} as failed: {e}")

    # ─────────────────────────────────────────────────────────────────
    # Event logging
    # ─────────────────────────────────────────────────────────────────

    def _add_event(
        self,
        job_id: str,
        event_type: str,
        message: str,
        printer_name: Optional[str] = None,
        copy_number: Optional[int] = None,
        total_copies: Optional[int] = None,
    ) -> None:
        """Add an event to the event log."""
        event = QueueEvent(
            timestamp=datetime.now(),
            job_id=job_id,
            event_type=event_type,
            message=message,
            printer_name=printer_name,
            copy_number=copy_number,
            total_copies=total_copies,
        )
        self._events.append(event)

        # Keep only the last N events
        if len(self._events) > self._max_events:
            self._events = self._events[-self._max_events:]

    # ─────────────────────────────────────────────────────────────────
    # Status query methods (for Admin API)
    # ─────────────────────────────────────────────────────────────────

    def get_queue_status(self) -> dict:
        """Get current queue status for admin dashboard."""
        queued_tasks = []
        try:
            # Get queued tasks (not yet assigned to a worker)
            # Note: accessing internal queue for display purposes
            for task in list(self._queue._queue)[:20]:
                queued_tasks.append({
                    "job_id": task.job_id,
                    "copy": f"{task.copy_number}/{task.total_copies}",
                    "queued_at": task.created_at.isoformat(),
                })
        except Exception:
            pass

        workers_status = []
        for worker in self._workers.values():
            worker_info = {
                "printer": worker.name,
                "is_busy": worker.is_busy,
                "current_task": None,
                "completed_today": worker.completed_count,
                "failed_today": worker.failed_count,
            }
            if worker.current_task:
                task = worker.current_task
                worker_info["current_task"] = {
                    "job_id": task.job_id,
                    "copy": f"{task.copy_number}/{task.total_copies}",
                    "started_at": task.started_at.isoformat() if task.started_at else None,
                }
            workers_status.append(worker_info)

        return {
            "queue_length": self._queue.qsize(),
            "active_jobs": len(self._job_copies),
            "workers": workers_status,
            "queued_tasks": queued_tasks,
        }

    def get_job_status(self, job_id: str) -> Optional[dict]:
        """Get status of a specific job."""
        if job_id not in self._job_copies:
            return None

        copies = self._job_copies[job_id]
        return {
            "job_id": job_id,
            "copies": [
                {
                    "copy_number": c.copy_number,
                    "status": c.status.value,
                    "printer": c.printer_name,
                    "cups_job_id": c.cups_job_id,
                    "started_at": c.started_at.isoformat() if c.started_at else None,
                    "completed_at": c.completed_at.isoformat() if c.completed_at else None,
                    "error_message": c.error_message,
                }
                for c in copies
            ],
            "completed": sum(1 for c in copies if c.status == CopyStatus.COMPLETED),
            "failed": sum(1 for c in copies if c.status == CopyStatus.FAILED),
            "total": len(copies),
        }

    def get_recent_events(self, limit: int = 50) -> List[dict]:
        """Get recent queue events for logging."""
        events = self._events[-limit:] if limit else self._events
        return [
            {
                "timestamp": e.timestamp.isoformat(),
                "job_id": e.job_id,
                "event_type": e.event_type,
                "message": e.message,
                "printer": e.printer_name,
                "copy_number": e.copy_number,
                "total_copies": e.total_copies,
            }
            for e in reversed(events)  # Most recent first
        ]

    def get_metrics(self) -> dict:
        """Get queue metrics for dashboard."""
        total_completed = sum(w.completed_count for w in self._workers.values())
        total_failed = sum(w.failed_count for w in self._workers.values())

        by_printer = [
            {
                "name": w.name,
                "completed": w.completed_count,
                "failed": w.failed_count,
                "is_busy": w.is_busy,
            }
            for w in self._workers.values()
        ]

        return {
            "today": {
                "total_copies": total_completed + total_failed,
                "completed_copies": total_completed,
                "failed_copies": total_failed,
                "queue_length": self._queue.qsize(),
            },
            "by_printer": by_printer,
        }

    @property
    def is_running(self) -> bool:
        """Check if the queue manager is running."""
        return self._running

    @property
    def printer_count(self) -> int:
        """Get the number of active printer workers."""
        return len(self._workers)


# Global singleton instance
_queue_manager: Optional[PrintQueueManager] = None


def get_queue_manager() -> PrintQueueManager:
    """Get the global queue manager instance."""
    global _queue_manager
    if _queue_manager is None:
        _queue_manager = PrintQueueManager()
    return _queue_manager
