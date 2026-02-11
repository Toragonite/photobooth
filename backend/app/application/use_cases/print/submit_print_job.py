"""Submit print job use case."""

import asyncio
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
    """Use case for submitting a new print job."""

    def __init__(
        self,
        session_repository: SessionRepository,
        print_job_repository: PrintJobRepository,
        printer: PrinterPort,
    ):
        self._session_repo = session_repository
        self._print_job_repo = print_job_repository
        self._printer = printer

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

        # Select printer: use explicitly requested printer, or auto-select
        target_printer = input_data.printer_name
        if not target_printer:
            target_printer = await self._printer.select_printer()

        if not target_printer:
            return UseCaseResult.fail("PRINTER_OFFLINE", "No printer available")

        # Check selected printer is ready
        if not await self._printer.is_ready(target_printer):
            return UseCaseResult.fail(
                "PRINTER_OFFLINE", f"Printer '{target_printer}' is not available"
            )

        job = PrintJob.create(
            session_id=sid,
            copies=input_data.copies,
            printer_name=target_printer,
        )
        await self._print_job_repo.save(job)

        # Start print job in background
        asyncio.create_task(
            self._process_print_job_background(
                str(job.id), session.composite_path, input_data.copies, target_printer
            )
        )

        return UseCaseResult.ok(
            PrintJobDTO(
                job_id=str(job.id),
                session_id=str(job.session_id),
                status=job.status.value,
                copies=job.copies,
                progress=job.progress_percent,
                printer_name=job.printer_name,
                error_code=job.error_code.value if job.error_code else None,
                error_message=job.error_message,
                retry_count=job.retry_count,
                created_at=job.created_at,
                completed_at=job.completed_at,
            )
        )

    async def _process_print_job_background(
        self, job_id: str, composite_path: str, copies: int, printer_name: str
    ) -> None:
        """Process the print job in background with its own database session."""
        from app.infrastructure.database import async_session
        from app.infrastructure.repositories import SQLAlchemyPrintJobRepository

        try:
            async with async_session() as db:
                repo = SQLAlchemyPrintJobRepository(db)

                # Load job from database
                job = await repo.get_by_id(JobId(job_id))
                if not job:
                    logger.error(f"Print job {job_id} not found in background task")
                    return

                file_path = composite_path
                logger.info(
                    f"Starting print job {job_id} for file: {file_path} "
                    f"on printer '{printer_name}'"
                )

                # Start processing
                job.start_processing()
                await repo.save(job)
                await db.commit()

                # Submit to selected printer
                result = await self._printer.print_image(file_path, copies, printer_name)

                if result.success and result.cups_job_id:
                    job.mark_printing(result.cups_job_id)
                    # Update printer_name from actual result (in case of fallback)
                    if result.printer_name:
                        job.printer_name = result.printer_name
                    await repo.save(job)
                    await db.commit()
                    logger.info(
                        f"Print job {job_id} submitted to CUPS: {result.cups_job_id} "
                        f"on printer '{result.printer_name}'"
                    )

                    # Monitor print job completion
                    await self._monitor_print_job_background(job_id, result.cups_job_id)
                else:
                    error_code = ErrorCode(result.error_code) if result.error_code else ErrorCode.CUPS_REJECTED
                    job.mark_error(error_code, result.error_message or "Print submission failed")
                    await repo.save(job)
                    await db.commit()
                    logger.error(f"Print job {job_id} failed: {result.error_message}")

        except Exception as e:
            logger.exception(f"Error processing print job {job_id}: {e}")
            # Try to update job status in a new session
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

    async def _monitor_print_job_background(self, job_id: str, cups_job_id: int) -> None:
        """Monitor CUPS job until completion with its own database session."""
        from app.infrastructure.database import async_session
        from app.infrastructure.repositories import SQLAlchemyPrintJobRepository

        max_wait = 120  # 2 minutes max
        poll_interval = 2  # Check every 2 seconds
        elapsed = 0

        while elapsed < max_wait:
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

            status = await self._printer.get_job_status(cups_job_id)
            logger.debug(f"Print job {job_id} CUPS status: {status}")

            if status == "completed":
                # Wait for actual printing to finish (CUPS completes when data is sent, not printed)
                # Estimate: ~20 seconds per copy for Canon Selphy CP1500
                async with async_session() as db:
                    repo = SQLAlchemyPrintJobRepository(db)
                    job = await repo.get_by_id(JobId(job_id))
                    if job:
                        extra_wait = job.copies * 20  # 20 seconds per copy
                        logger.info(f"Print job {job_id} CUPS done, waiting {extra_wait}s for {job.copies} copies to print")
                        await asyncio.sleep(extra_wait)
                        job.mark_completed()
                        await repo.save(job)
                        await db.commit()
                logger.info(f"Print job {job_id} completed successfully")
                return
            elif status in ("cancelled", "failed", "aborted"):
                async with async_session() as db:
                    repo = SQLAlchemyPrintJobRepository(db)
                    job = await repo.get_by_id(JobId(job_id))
                    if job:
                        job.mark_error(ErrorCode.CUPS_REJECTED, f"CUPS job {status}")
                        await repo.save(job)
                        await db.commit()
                logger.error(f"Print job {job_id} failed with status: {status}")
                return
            elif status == "unknown":
                # Job might have completed and been removed from queue
                async with async_session() as db:
                    repo = SQLAlchemyPrintJobRepository(db)
                    job = await repo.get_by_id(JobId(job_id))
                    if job:
                        extra_wait = job.copies * 20  # 20 seconds per copy
                        logger.info(f"Print job {job_id} assumed done, waiting {extra_wait}s for {job.copies} copies to print")
                        await asyncio.sleep(extra_wait)
                        job.mark_completed()
                        await repo.save(job)
                        await db.commit()
                logger.info(f"Print job {job_id} assumed completed (not in queue)")
                return

        # Timeout
        logger.warning(f"Print job {job_id} timed out after {max_wait}s")
        async with async_session() as db:
            repo = SQLAlchemyPrintJobRepository(db)
            job = await repo.get_by_id(JobId(job_id))
            if job:
                job.mark_error(ErrorCode.CUPS_REJECTED, "Print job timed out")
                await repo.save(job)
                await db.commit()
