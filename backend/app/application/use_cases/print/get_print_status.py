"""Get print status use case."""

from app.application.dto.print_job_dto import PrintJobStatusResponse
from app.application.ports.repositories import PrintJobRepository
from app.application.ports.services import PrinterPort
from app.application.use_cases.base import UseCase, UseCaseResult
from app.domain.value_objects import JobId


class GetPrintStatusUseCase(UseCase[PrintJobStatusResponse]):
    """Use case for retrieving print job status."""

    def __init__(
        self,
        print_job_repository: PrintJobRepository,
        printer: PrinterPort,
    ):
        self._print_job_repo = print_job_repository
        self._printer = printer

    async def execute(self, job_id: str) -> UseCaseResult[PrintJobStatusResponse]:
        try:
            jid = JobId(job_id)
        except ValueError:
            return UseCaseResult.fail("INVALID_JOB_ID", "Invalid job ID format")

        job = await self._print_job_repo.get_by_id(jid)
        if not job:
            return UseCaseResult.fail("JOB_NOT_FOUND", "Print job not found")

        return UseCaseResult.ok(
            PrintJobStatusResponse(
                job_id=str(job.id),
                status=job.status.value,
                progress=job.progress_percent,
                error_code=job.error_code.value if job.error_code else None,
                error_message=job.error_message,
            )
        )
