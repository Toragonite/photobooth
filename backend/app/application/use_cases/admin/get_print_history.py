"""Get print history use case."""

from dataclasses import dataclass
from typing import Optional

from app.application.dto.admin_dto import PrintHistoryDTO
from app.application.ports.repositories import PrintJobRepository
from app.application.use_cases.base import UseCase, UseCaseResult
from app.domain.value_objects import PrintStatus


@dataclass
class GetPrintHistoryInput:
    """Input for getting print history."""
    page: int = 1
    per_page: int = 20
    status_filter: Optional[str] = None


class GetPrintHistoryUseCase(UseCase[PrintHistoryDTO]):
    """Use case for retrieving print history."""

    def __init__(self, print_job_repo: PrintJobRepository):
        self._print_job_repo = print_job_repo

    async def execute(self, input_data: GetPrintHistoryInput) -> UseCaseResult[PrintHistoryDTO]:
        try:
            offset = (input_data.page - 1) * input_data.per_page

            status_filter = None
            if input_data.status_filter:
                try:
                    status_filter = PrintStatus(input_data.status_filter)
                except ValueError:
                    pass

            jobs = await self._print_job_repo.get_history(
                limit=input_data.per_page,
                offset=offset,
                status_filter=status_filter,
            )

            job_dicts = [
                {
                    "id": str(job.id),
                    "session_id": str(job.session_id),
                    "status": job.status.value,
                    "copies": job.copies,
                    "retry_count": job.retry_count,
                    "created_at": job.created_at.isoformat() if job.created_at else None,
                    "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                }
                for job in jobs
            ]

            # Get total count for pagination
            total = len(jobs)  # Simplified - in real impl would need count query

            return UseCaseResult.ok(
                PrintHistoryDTO(
                    jobs=job_dicts,
                    total=total,
                    page=input_data.page,
                    per_page=input_data.per_page,
                )
            )
        except Exception as e:
            return UseCaseResult.fail("HISTORY_ERROR", str(e))
