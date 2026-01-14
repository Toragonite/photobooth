"""Retry print job use case."""

from app.application.dto.print_job_dto import PrintJobStatusResponse
from app.application.ports.repositories import PrintJobRepository
from app.application.use_cases.base import UseCase, UseCaseResult
from app.domain.value_objects import JobId, PrintStatus


class RetryPrintJobUseCase(UseCase[PrintJobStatusResponse]):
    """Use case for retrying a failed print job."""

    def __init__(self, print_job_repo: PrintJobRepository):
        self._print_job_repo = print_job_repo

    async def execute(self, job_id: str) -> UseCaseResult[PrintJobStatusResponse]:
        try:
            jid = JobId(job_id)
        except ValueError:
            return UseCaseResult.fail("INVALID_JOB_ID", "Invalid job ID format")

        job = await self._print_job_repo.get_by_id(jid)
        if not job:
            return UseCaseResult.fail("JOB_NOT_FOUND", "Print job not found")

        if job.status != PrintStatus.FAILED:
            return UseCaseResult.fail(
                "INVALID_STATE", f"Cannot retry job in {job.status.value} status"
            )

        try:
            job.user_retry()
            await self._print_job_repo.save(job)

            return UseCaseResult.ok(
                PrintJobStatusResponse(
                    job_id=str(job.id),
                    status=job.status.value,
                    progress=job.progress_percent,
                )
            )
        except Exception as e:
            return UseCaseResult.fail("RETRY_FAILED", str(e))
