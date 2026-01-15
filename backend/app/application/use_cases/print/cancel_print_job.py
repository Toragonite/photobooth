"""Cancel print job use case."""

from app.application.ports.repositories import PrintJobRepository
from app.application.ports.services import PrinterPort
from app.application.use_cases.base import UseCase, UseCaseResult
from app.domain.value_objects import JobId, PrintStatus


class CancelPrintJobUseCase(UseCase[bool]):
    """Use case for cancelling a print job."""

    def __init__(
        self,
        print_job_repository: PrintJobRepository,
        printer: PrinterPort,
    ):
        self._print_job_repo = print_job_repository
        self._printer = printer

    async def execute(self, job_id: str) -> UseCaseResult[bool]:
        try:
            jid = JobId(job_id)
        except ValueError:
            return UseCaseResult.fail("INVALID_JOB_ID", "Invalid job ID format")

        job = await self._print_job_repo.get_by_id(jid)
        if not job:
            return UseCaseResult.fail("JOB_NOT_FOUND", "Print job not found")

        if job.status in (PrintStatus.COMPLETED, PrintStatus.CANCELLED):
            return UseCaseResult.fail(
                "INVALID_STATE", f"Cannot cancel job in {job.status.value} status"
            )

        try:
            if job.cups_job_id and job.status == PrintStatus.PRINTING:
                await self._printer.cancel_job(job.cups_job_id)

            job.cancel()
            await self._print_job_repo.save(job)

            return UseCaseResult.ok(True)
        except Exception as e:
            return UseCaseResult.fail("CANCEL_FAILED", str(e))
