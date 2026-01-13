"""Storage cleanup service for automatic and manual cleanup."""

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable, List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import PrintJobModel, SessionModel
from .storage_service import StorageService

logger = logging.getLogger(__name__)


@dataclass
class CleanupPreviewResult:
    """Result of cleanup preview (dry run)."""

    sessions_count: int
    files_count: int
    total_size_bytes: int
    estimated_new_usage_percent: float


@dataclass
class CleanupResult:
    """Result of cleanup execution."""

    success: bool
    sessions_cleaned: int
    files_deleted: int
    bytes_freed: int
    duration_seconds: float
    errors: List[str]


class CleanupService:
    """Service for managing storage cleanup operations."""

    # Terminal session statuses that can be cleaned
    CLEANABLE_STATUSES = ("complete", "printed", "abandoned")

    # Pending print job statuses that block cleanup
    PENDING_PRINT_STATUSES = ("pending", "processing", "printing", "retry_pending")

    # Storage thresholds
    WARNING_THRESHOLD = 80
    CRITICAL_THRESHOLD = 95

    def __init__(self):
        self.storage_service = StorageService()

    async def preview_cleanup(
        self,
        db: AsyncSession,
        retention_days: int = 30,
    ) -> CleanupPreviewResult:
        """Preview cleanup without deleting anything.

        Args:
            db: Database session
            retention_days: Days to retain sessions

        Returns:
            CleanupPreviewResult with statistics
        """
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        sessions = await self._get_cleanable_sessions(db, cutoff_date)

        # Calculate total size
        total_size = 0
        files_count = 0

        for session in sessions:
            # Count photos
            files_count += len(session.photos)
            for photo in session.photos:
                total_size += photo.file_size

            # Count composite if exists
            if session.composite_path:
                files_count += 1
                # Estimate composite size (usually similar to sum of photos)
                total_size += sum(p.file_size for p in session.photos) // 2

        # Calculate estimated usage after cleanup
        storage_stats = self.storage_service.get_storage_stats()
        estimated_used = storage_stats["used_bytes"] - total_size
        estimated_percent = (
            (estimated_used / storage_stats["total_bytes"]) * 100
            if storage_stats["total_bytes"] > 0
            else 0
        )

        return CleanupPreviewResult(
            sessions_count=len(sessions),
            files_count=files_count,
            total_size_bytes=total_size,
            estimated_new_usage_percent=round(estimated_percent, 1),
        )

    async def execute_cleanup(
        self,
        db: AsyncSession,
        retention_days: int = 30,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> CleanupResult:
        """Execute storage cleanup.

        Args:
            db: Database session
            retention_days: Days to retain sessions
            progress_callback: Optional callback(current, total)

        Returns:
            CleanupResult with statistics
        """
        start_time = time.time()
        errors: List[str] = []

        cutoff_date = datetime.now() - timedelta(days=retention_days)
        sessions = await self._get_cleanable_sessions(db, cutoff_date)

        total_sessions = len(sessions)
        sessions_cleaned = 0
        files_deleted = 0
        bytes_freed = 0

        logger.info(
            f"Starting cleanup of {total_sessions} sessions (retention: {retention_days} days)"
        )

        for i, session in enumerate(sessions):
            try:
                result = await self._clean_session(db, session)
                sessions_cleaned += 1
                files_deleted += result["files_deleted"]
                bytes_freed += result["bytes_freed"]
            except Exception as e:
                error_msg = f"Failed to clean session {session.id}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)

            if progress_callback:
                progress_callback(i + 1, total_sessions)

        await db.commit()

        duration = time.time() - start_time
        logger.info(
            f"Cleanup completed: {sessions_cleaned} sessions, "
            f"{files_deleted} files, {bytes_freed} bytes freed in {duration:.2f}s"
        )

        return CleanupResult(
            success=len(errors) == 0,
            sessions_cleaned=sessions_cleaned,
            files_deleted=files_deleted,
            bytes_freed=bytes_freed,
            duration_seconds=round(duration, 2),
            errors=errors,
        )

    async def emergency_cleanup(
        self,
        db: AsyncSession,
    ) -> CleanupResult:
        """Emergency cleanup when storage is critical.

        Progressively cleans more aggressively:
        1. First try 7-day retention
        2. If still critical, try 3-day retention
        """
        storage_stats = self.storage_service.get_storage_stats()

        if storage_stats["percent_used"] < self.CRITICAL_THRESHOLD:
            logger.info("Emergency cleanup called but storage not critical")
            return CleanupResult(
                success=True,
                sessions_cleaned=0,
                files_deleted=0,
                bytes_freed=0,
                duration_seconds=0,
                errors=[],
            )

        logger.warning(
            f"Emergency cleanup triggered: {storage_stats['percent_used']:.1f}% used"
        )

        # First pass: 7-day retention
        result = await self.execute_cleanup(db, retention_days=7)

        # Check if still critical
        storage_stats = self.storage_service.get_storage_stats()
        if storage_stats["percent_used"] >= self.CRITICAL_THRESHOLD:
            logger.warning("Storage still critical, applying 3-day retention")
            result2 = await self.execute_cleanup(db, retention_days=3)

            # Combine results
            result = CleanupResult(
                success=result.success and result2.success,
                sessions_cleaned=result.sessions_cleaned + result2.sessions_cleaned,
                files_deleted=result.files_deleted + result2.files_deleted,
                bytes_freed=result.bytes_freed + result2.bytes_freed,
                duration_seconds=result.duration_seconds + result2.duration_seconds,
                errors=result.errors + result2.errors,
            )

        return result

    async def _get_cleanable_sessions(
        self,
        db: AsyncSession,
        cutoff_date: datetime,
    ) -> List[SessionModel]:
        """Get sessions eligible for cleanup.

        Criteria:
        - Status is terminal (complete, printed, abandoned)
        - Created before cutoff date
        - Not already cleaned (files_cleaned = 0)
        - No pending print jobs
        """
        # Subquery for sessions with pending print jobs
        pending_jobs_subquery = (
            select(PrintJobModel.session_id)
            .where(PrintJobModel.status.in_(self.PENDING_PRINT_STATUSES))
            .distinct()
        )

        # Main query
        query = (
            select(SessionModel)
            .where(
                and_(
                    SessionModel.status.in_(self.CLEANABLE_STATUSES),
                    SessionModel.created_at < cutoff_date,
                    SessionModel.files_cleaned == 0,
                    ~SessionModel.id.in_(pending_jobs_subquery),
                )
            )
            .order_by(SessionModel.created_at.asc())
        )

        result = await db.execute(query)
        return list(result.scalars().all())

    async def _clean_session(
        self,
        db: AsyncSession,
        session: SessionModel,
    ) -> dict:
        """Clean files for a single session.

        Returns:
            dict with files_deleted and bytes_freed
        """
        files_deleted = 0
        bytes_freed = 0

        # Calculate size before deletion
        for photo in session.photos:
            bytes_freed += photo.file_size
            files_deleted += 1

        if session.composite_path:
            files_deleted += 1
            # Add estimated composite size
            bytes_freed += sum(p.file_size for p in session.photos) // 2

        # Delete files using storage service
        await self.storage_service.delete_session_files(str(session.id))

        # Mark session as cleaned
        session.files_cleaned = 1
        session.cleaned_at = datetime.now()

        # Clear file paths in database (keep metadata)
        session.composite_path = None

        logger.debug(
            f"Cleaned session {session.id}: {files_deleted} files, {bytes_freed} bytes"
        )

        return {
            "files_deleted": files_deleted,
            "bytes_freed": bytes_freed,
        }

    def get_storage_status(self) -> dict:
        """Get current storage status with health assessment."""
        stats = self.storage_service.get_storage_stats()

        if stats["percent_used"] >= self.CRITICAL_THRESHOLD:
            health = "critical"
        elif stats["percent_used"] >= self.WARNING_THRESHOLD:
            health = "warning"
        else:
            health = "healthy"

        return {
            **stats,
            "health": health,
            "warning_threshold": self.WARNING_THRESHOLD,
            "critical_threshold": self.CRITICAL_THRESHOLD,
        }
