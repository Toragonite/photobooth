"""SQLAlchemy implementation of PrintJobRepository."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.repositories import PrintJobRepository
from app.domain.entities import PrintJob
from app.domain.value_objects import ErrorCode, JobId, PrintStatus, SessionId
from app.infrastructure.database import PrintJobModel


class SQLAlchemyPrintJobRepository(PrintJobRepository):
    """SQLAlchemy implementation of print job repository."""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def save(self, job: PrintJob) -> None:
        """Save or update a print job."""
        existing = await self._db.get(PrintJobModel, job.id.value)

        if existing:
            # Update existing job
            existing.status = job.status.value
            existing.copies = job.copies
            existing.cups_job_id = job.cups_job_id
            existing.started_at = job.started_at
            existing.completed_at = job.completed_at
            existing.cancelled_at = job.cancelled_at
            existing.error_code = job.error_code.value if job.error_code else None
            existing.error_message = job.error_message
            existing.retry_count = job.retry_count
            existing.next_retry_at = job.next_retry_at
        else:
            # Create new job
            model = self._job_to_model(job)
            self._db.add(model)

        await self._db.commit()

    async def get_by_id(self, job_id: JobId) -> Optional[PrintJob]:
        """Retrieve a print job by its ID."""
        model = await self._db.get(PrintJobModel, job_id.value)

        if model is None:
            return None

        return self._model_to_job(model)

    async def get_by_session(self, session_id: SessionId) -> List[PrintJob]:
        """Retrieve all print jobs for a session."""
        stmt = (
            select(PrintJobModel)
            .where(PrintJobModel.session_id == session_id.value)
            .order_by(PrintJobModel.created_at.desc())
        )
        result = await self._db.execute(stmt)
        models = result.scalars().all()

        return [self._model_to_job(m) for m in models]

    async def get_pending_jobs(self) -> List[PrintJob]:
        """Retrieve all pending print jobs."""
        stmt = (
            select(PrintJobModel)
            .where(PrintJobModel.status == PrintStatus.PENDING.value)
            .order_by(PrintJobModel.created_at)
        )
        result = await self._db.execute(stmt)
        models = result.scalars().all()

        return [self._model_to_job(m) for m in models]

    async def get_retry_jobs(self, before: datetime) -> List[PrintJob]:
        """Retrieve jobs scheduled for retry before the given time."""
        stmt = (
            select(PrintJobModel)
            .where(
                PrintJobModel.status == PrintStatus.RETRY_PENDING.value,
                PrintJobModel.next_retry_at <= before,
            )
            .order_by(PrintJobModel.next_retry_at)
        )
        result = await self._db.execute(stmt)
        models = result.scalars().all()

        return [self._model_to_job(m) for m in models]

    async def get_history(
        self, limit: int, offset: int, status_filter: Optional[PrintStatus] = None
    ) -> List[PrintJob]:
        """Retrieve print job history with pagination."""
        stmt = select(PrintJobModel).order_by(PrintJobModel.created_at.desc())

        if status_filter is not None:
            stmt = stmt.where(PrintJobModel.status == status_filter.value)

        stmt = stmt.offset(offset).limit(limit)

        result = await self._db.execute(stmt)
        models = result.scalars().all()

        return [self._model_to_job(m) for m in models]

    async def count_by_status(self, status: PrintStatus) -> int:
        """Count jobs with a specific status."""
        stmt = select(func.count(PrintJobModel.id)).where(
            PrintJobModel.status == status.value
        )
        result = await self._db.execute(stmt)
        return result.scalar_one()

    async def get_active_jobs(self) -> List[PrintJob]:
        """Retrieve all active (non-terminal) print jobs."""
        terminal_statuses = [
            PrintStatus.COMPLETED.value,
            PrintStatus.CANCELLED.value,
            PrintStatus.FAILED.value,
        ]
        stmt = (
            select(PrintJobModel)
            .where(PrintJobModel.status.not_in(terminal_statuses))
            .order_by(PrintJobModel.created_at)
        )
        result = await self._db.execute(stmt)
        models = result.scalars().all()

        return [self._model_to_job(m) for m in models]

    # ─────────────────────────────────────────────────────────────────
    # Mappers
    # ─────────────────────────────────────────────────────────────────

    def _job_to_model(self, job: PrintJob) -> PrintJobModel:
        """Convert domain entity to database model."""
        return PrintJobModel(
            id=job.id.value,
            session_id=job.session_id.value,
            status=job.status.value,
            copies=job.copies,
            cups_job_id=job.cups_job_id,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            cancelled_at=job.cancelled_at,
            error_code=job.error_code.value if job.error_code else None,
            error_message=job.error_message,
            retry_count=job.retry_count,
            next_retry_at=job.next_retry_at,
        )

    def _model_to_job(self, model: PrintJobModel) -> PrintJob:
        """Convert database model to domain entity."""
        error_code = None
        if model.error_code:
            try:
                error_code = ErrorCode(model.error_code)
            except ValueError:
                # Unknown error code, leave as None
                pass

        return PrintJob(
            id=JobId.from_string(model.id),
            session_id=SessionId.from_string(model.session_id),
            status=PrintStatus(model.status),
            copies=model.copies,
            cups_job_id=model.cups_job_id,
            created_at=model.created_at,
            started_at=model.started_at,
            completed_at=model.completed_at,
            cancelled_at=model.cancelled_at,
            error_code=error_code,
            error_message=model.error_message,
            retry_count=model.retry_count,
            next_retry_at=model.next_retry_at,
        )
