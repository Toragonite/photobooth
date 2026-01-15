"""Submit print job use case."""

from dataclasses import dataclass

from app.application.dto.print_job_dto import PrintJobDTO
from app.application.ports.repositories import (PrintJobRepository,
                                                SessionRepository)
from app.application.ports.services import PrinterPort
from app.application.use_cases.base import UseCase, UseCaseResult
from app.domain.entities import PrintJob
from app.domain.value_objects import SessionId, SessionStatus


@dataclass
class SubmitPrintJobInput:
    """Input for submitting a print job."""
    session_id: str
    copies: int = 1


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

        # Check printer availability
        if not await self._printer.is_ready():
            return UseCaseResult.fail("PRINTER_OFFLINE", "Printer is not available")

        job = PrintJob.create(session_id=sid, copies=input_data.copies)
        await self._print_job_repo.save(job)

        return UseCaseResult.ok(
            PrintJobDTO(
                id=str(job.id),
                session_id=str(job.session_id),
                status=job.status.value,
                copies=job.copies,
                progress=job.progress_percent,
                error_code=job.error_code.value if job.error_code else None,
                error_message=job.error_message,
                retry_count=job.retry_count,
                created_at=job.created_at,
                completed_at=job.completed_at,
            )
        )
