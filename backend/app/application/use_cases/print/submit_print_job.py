"""Submit print job use case with queue-based copy processing."""

import logging
from dataclasses import dataclass
from typing import Optional

from app.application.dto.print_job_dto import PrintJobDTO
from app.application.ports.repositories import (PrintJobRepository,
                                                SessionRepository)
from app.application.ports.services import PrinterPort
from app.application.use_cases.base import UseCase, UseCaseResult
from app.domain.entities import PrintJob
from app.domain.value_objects import ErrorCode, JobId, SessionId, SessionStatus

logger = logging.getLogger(__name__)


@dataclass
class SubmitPrintJobInput:
    """Input for submitting a print job."""
    session_id: str
    copies: int = 1
    printer_name: Optional[str] = None


class SubmitPrintJobUseCase(UseCase[PrintJobDTO]):
    """Use case for submitting a new print job.

    This use case validates the session, creates a PrintJob entity,
    and submits copies to the PrintQueueManager for processing.
    """

    def __init__(
        self,
        session_repository: SessionRepository,
        print_job_repository: PrintJobRepository,
        printer: PrinterPort,
        queue_manager=None,  # Optional: PrintQueueManager
    ):
        self._session_repo = session_repository
        self._print_job_repo = print_job_repository
        self._printer = printer
        self._queue_manager = queue_manager
        # Debug logging
        logger.info(
            f"SubmitPrintJobUseCase __init__: queue_manager={queue_manager}, "
            f"id={id(queue_manager) if queue_manager else None}, "
            f"is_running={queue_manager.is_running if queue_manager else None}"
        )

    async def execute(
        self, input_data: SubmitPrintJobInput
    ) -> UseCaseResult[PrintJobDTO]:
        try:
            sid = SessionId(input_data.session_id)
        except ValueError:
            return UseCaseResult.fail("INVALID_SESSION_ID", "Invalid session ID format")

        session = await self._session_repo.get_by_id(sid)
        if not session:
            return UseCaseResult.fail("SESSION_NOT_FOUND", "Session not found")

        if session.status not in (SessionStatus.COMPLETE, SessionStatus.PRINTED):
            return UseCaseResult.fail(
                "SESSION_NOT_COMPLETE", "Session must be complete to print"
            )

        if not session.composite_path:
            return UseCaseResult.fail("NO_COMPOSITE", "Generate composite first")

        if input_data.copies < 1 or input_data.copies > 10:
            return UseCaseResult.fail(
                "INVALID_COPIES", "Copies must be between 1 and 10"
            )

        # Create print job entity
        job = PrintJob.create(
            session_id=sid,
            copies=input_data.copies,
            printer_name=input_data.printer_name,  # May be None for auto-selection
        )
        await self._print_job_repo.save(job)

        # Submit to queue manager if available
        if self._queue_manager and self._queue_manager.is_running:
            # Submit copies to queue (callbacks are set once at startup in main.py)
            await self._queue_manager.submit_job(
                job_id=str(job.id),
                file_path=session.composite_path,
                copies=input_data.copies,
            )

            logger.info(
                f"Print job {job.id} submitted to queue: "
                f"{input_data.copies} copies"
            )
        else:
            # Fallback to legacy direct processing (for backwards compatibility)
            logger.warning(
                f"Queue manager not available, using legacy processing for job {job.id}"
            )
            import asyncio
            asyncio.create_task(
                self._process_print_job_legacy(
                    str(job.id),
                    session.composite_path,
                    input_data.copies,
                    input_data.printer_name,
                )
            )

        return UseCaseResult.ok(
            PrintJobDTO(
                job_id=str(job.id),
                session_id=str(job.session_id),
                status=job.status.value,
                copies=job.copies,
                progress=job.progress_percent,
                completed_copies=job.completed_copies,
                current_copy=job.current_copy,
                copy_progress=job.copy_progress_str,
                printer_name=job.printer_name,
                error_code=job.error_code.value if job.error_code else None,
                error_message=job.error_message,
                retry_count=job.retry_count,
                created_at=job.created_at,
                completed_at=job.completed_at,
            )
        )

    # ─────────────────────────────────────────────────────────────────
    # Legacy Processing (fallback if queue manager not available)
    # ─────────────────────────────────────────────────────────────────

    async def _process_print_job_legacy(
        self, job_id: str, composite_path: str, copies: int, printer_name: Optional[str]
    ) -> None:
        """Legacy processing method for backwards compatibility."""
        from app.infrastructure.database import async_session
        from app.infrastructure.repositories import SQLAlchemyPrintJobRepository

        try:
            async with async_session() as db:
                repo = SQLAlchemyPrintJobRepository(db)

                job = await repo.get_by_id(JobId(job_id))
                if not job:
                    logger.error(f"Print job {job_id} not found in legacy processing")
                    return

                # Select printer if not specified
                target_printer = printer_name
                if not target_printer:
                    target_printer = await self._printer.select_printer()

                if not target_printer:
                    job.mark_error(ErrorCode.PRINTER_OFFLINE, "No printer available")
                    await repo.save(job)
                    await db.commit()
                    return

                job.printer_name = target_printer
                job.start_processing()
                await repo.save(job)
                await db.commit()

                # Process each copy sequentially
                for copy_num in range(1, copies + 1):
                    job.start_copy(copy_num)
                    await repo.save(job)
                    await db.commit()

                    logger.info(f"Job {job_id}: Starting copy {copy_num}/{copies}")

                    # Submit single copy
                    result = await self._printer.print_image(
                        composite_path, copies=1, printer_name=target_printer
                    )

                    if not result.success:
                        error_code = (
                            ErrorCode(result.error_code)
                            if result.error_code
                            else ErrorCode.CUPS_REJECTED
                        )
                        job.mark_error(
                            error_code, result.error_message or "Print failed"
                        )
                        await repo.save(job)
                        await db.commit()
                        return

                    # Update CUPS job ID
                    if result.cups_job_id:
                        job.update_cups_job_id(result.cups_job_id)
                        await repo.save(job)
                        await db.commit()

                    # Wait for completion
                    success, status_msg = await self._printer.wait_for_job_completion(
                        result.cups_job_id, timeout_seconds=120
                    )

                    if not success:
                        job.mark_error(ErrorCode.CUPS_REJECTED, f"Print failed: {status_msg}")
                        await repo.save(job)
                        await db.commit()
                        return

                    # Mark copy as completed
                    job.complete_copy(result.cups_job_id)
                    await repo.save(job)
                    await db.commit()

                    logger.info(f"Job {job_id}: Copy {copy_num}/{copies} completed")

                logger.info(f"Job {job_id} completed: {copies}/{copies} copies")

        except Exception as e:
            logger.exception(f"Error in legacy processing for job {job_id}: {e}")
            try:
                async with async_session() as db:
                    repo = SQLAlchemyPrintJobRepository(db)
                    job = await repo.get_by_id(JobId(job_id))
                    if job:
                        job.mark_error(ErrorCode.CUPS_REJECTED, str(e))
                        await repo.save(job)
                        await db.commit()
            except Exception as inner_e:
                logger.exception(f"Failed to update error status for job {job_id}: {inner_e}")
