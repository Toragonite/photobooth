"""Photo export service for downloading session photos."""

import asyncio
import logging
import os
import uuid
import zipfile
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...config import get_settings
from ...infrastructure.database import PhotoModel, SessionModel

settings = get_settings()
logger = logging.getLogger(__name__)


class ExportType(str, Enum):
    """Types of photo export."""

    ALL = "all"  # All photos + composite
    PHOTOS_ONLY = "photos"  # Individual photos only
    COMPOSITE_ONLY = "composite"  # Composite only


class ExportStatus(str, Enum):
    """Export job status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ExportJob:
    """Export job information."""

    id: str
    status: ExportStatus
    sessions_count: int
    files_count: int
    total_size: int
    progress: float
    created_at: datetime
    completed_at: Optional[datetime] = None
    download_path: Optional[str] = None
    error: Optional[str] = None


class PhotoExportService:
    """Service for exporting photos from sessions."""

    # In-memory export jobs tracking
    _export_jobs: Dict[str, ExportJob] = {}

    def __init__(self):
        self.storage_path = Path(settings.storage_path)
        self.exports_dir = self.storage_path / "exports"
        self.exports_dir.mkdir(parents=True, exist_ok=True)

    async def export_session(
        self,
        db: AsyncSession,
        session_id: str,
        export_type: ExportType = ExportType.ALL,
    ) -> Optional[str]:
        """Export a single session's photos.

        Args:
            db: Database session
            session_id: Session ID to export
            export_type: Type of export (all, photos, composite)

        Returns:
            Path to ZIP file or None if failed
        """
        # Get session
        result = await db.execute(
            select(SessionModel).where(SessionModel.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            logger.error(f"Session not found: {session_id}")
            return None

        # Get photos
        result = await db.execute(
            select(PhotoModel)
            .where(PhotoModel.session_id == session_id)
            .order_by(PhotoModel.index)
        )
        photos = result.scalars().all()

        # Create ZIP file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"session_{session_id[:8]}_{timestamp}.zip"
        zip_path = self.exports_dir / zip_filename

        try:
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                # Add photos
                if export_type in (ExportType.ALL, ExportType.PHOTOS_ONLY):
                    for photo in photos:
                        if os.path.exists(photo.file_path):
                            arcname = f"photos/photo_{photo.index + 1}.jpg"
                            zf.write(photo.file_path, arcname)

                # Add composite
                if export_type in (ExportType.ALL, ExportType.COMPOSITE_ONLY):
                    if session.composite_path and os.path.exists(
                        session.composite_path
                    ):
                        zf.write(session.composite_path, "composite.jpg")

                # Add session info
                info_content = (
                    f"Session ID: {session.id}\n"
                    f"Created: {session.created_at.isoformat()}\n"
                    f"Language: {session.language}\n"
                    f"Status: {session.status}\n"
                    f"Photos: {len(photos)}\n"
                )
                zf.writestr("session_info.txt", info_content)

            logger.info(f"Exported session {session_id} to {zip_path}")
            return str(zip_path)

        except Exception as e:
            logger.error(f"Failed to export session {session_id}: {e}")
            if zip_path.exists():
                zip_path.unlink()
            return None

    async def create_bulk_export(
        self,
        db: AsyncSession,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status_filter: Optional[str] = None,
    ) -> str:
        """Create a bulk export job.

        Args:
            db: Database session
            start_date: Start date filter
            end_date: End date filter
            status_filter: Session status filter

        Returns:
            Export job ID
        """
        job_id = str(uuid.uuid4())[:8]

        # Count sessions to export
        query = select(SessionModel)
        conditions = []

        if start_date:
            conditions.append(SessionModel.created_at >= start_date)
        if end_date:
            conditions.append(SessionModel.created_at <= end_date)
        if status_filter and status_filter != "all":
            conditions.append(SessionModel.status == status_filter)
        # Only export sessions with files
        conditions.append(SessionModel.files_cleaned == 0)

        if conditions:
            query = query.where(and_(*conditions))

        result = await db.execute(query)
        sessions = result.scalars().all()

        # Create job record
        job = ExportJob(
            id=job_id,
            status=ExportStatus.PENDING,
            sessions_count=len(sessions),
            files_count=0,
            total_size=0,
            progress=0.0,
            created_at=datetime.now(),
        )
        PhotoExportService._export_jobs[job_id] = job

        # Start export in background
        asyncio.create_task(self._process_bulk_export(db, job_id, sessions))

        return job_id

    async def _process_bulk_export(
        self,
        db: AsyncSession,
        job_id: str,
        sessions: List[SessionModel],
    ):
        """Process bulk export in background.

        Args:
            db: Database session
            job_id: Export job ID
            sessions: List of sessions to export
        """
        job = PhotoExportService._export_jobs.get(job_id)
        if not job:
            return

        job.status = ExportStatus.PROCESSING

        # Create ZIP file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"bulk_export_{job_id}_{timestamp}.zip"
        zip_path = self.exports_dir / zip_filename

        try:
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                total_files = 0
                total_size = 0

                for i, session in enumerate(sessions):
                    # Get photos for this session
                    result = await db.execute(
                        select(PhotoModel)
                        .where(PhotoModel.session_id == session.id)
                        .order_by(PhotoModel.index)
                    )
                    photos = result.scalars().all()

                    date_str = session.created_at.strftime("%Y%m%d")
                    session_dir = f"session_{session.id[:8]}_{date_str}"

                    # Add photos
                    for photo in photos:
                        if os.path.exists(photo.file_path):
                            arcname = f"{session_dir}/photo_{photo.index + 1}.jpg"
                            zf.write(photo.file_path, arcname)
                            total_files += 1
                            total_size += os.path.getsize(photo.file_path)

                    # Add composite
                    if session.composite_path and os.path.exists(
                        session.composite_path
                    ):
                        zf.write(session.composite_path, f"{session_dir}/composite.jpg")
                        total_files += 1
                        total_size += os.path.getsize(session.composite_path)

                    # Update progress
                    job.progress = (i + 1) / len(sessions) * 100
                    job.files_count = total_files
                    job.total_size = total_size

                # Add index file
                index_content = "PhotoBooth Bulk Export\n"
                index_content += f"Generated: {datetime.now().isoformat()}\n"
                index_content += f"Sessions: {len(sessions)}\n"
                index_content += f"Total Files: {total_files}\n\n"

                for session in sessions:
                    ts = session.created_at.strftime("%Y-%m-%d %H:%M")
                    index_content += f"- {session.id[:8]}: {ts} ({session.status})\n"

                zf.writestr("index.txt", index_content)

            job.status = ExportStatus.COMPLETED
            job.completed_at = datetime.now()
            job.download_path = str(zip_path)
            job.progress = 100.0

            logger.info(f"Bulk export completed: {job_id} ({total_files} files)")

        except Exception as e:
            logger.error(f"Bulk export failed: {job_id}: {e}")
            job.status = ExportStatus.FAILED
            job.error = str(e)
            if zip_path.exists():
                zip_path.unlink()

    def get_export_status(self, job_id: str) -> Optional[ExportJob]:
        """Get status of an export job.

        Args:
            job_id: Export job ID

        Returns:
            ExportJob or None if not found
        """
        return PhotoExportService._export_jobs.get(job_id)

    async def get_session_photos(
        self,
        db: AsyncSession,
        session_id: str,
    ) -> Dict:
        """Get photos info for a session.

        Args:
            db: Database session
            session_id: Session ID

        Returns:
            Dict with session and photos info
        """
        # Get session
        result = await db.execute(
            select(SessionModel).where(SessionModel.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            return {"error": "Session not found"}

        # Get photos
        result = await db.execute(
            select(PhotoModel)
            .where(PhotoModel.session_id == session_id)
            .order_by(PhotoModel.index)
        )
        photos = result.scalars().all()

        return {
            "session": {
                "id": session.id,
                "created_at": session.created_at.isoformat(),
                "status": session.status,
                "language": session.language,
                "has_composite": bool(
                    session.composite_path and os.path.exists(session.composite_path)
                ),
                "files_cleaned": session.files_cleaned > 0,
            },
            "photos": [
                {
                    "id": photo.id,
                    "index": photo.index,
                    "file_exists": os.path.exists(photo.file_path),
                    "file_size": (
                        os.path.getsize(photo.file_path)
                        if os.path.exists(photo.file_path)
                        else 0
                    ),
                    "thumbnail_path": photo.thumbnail_path,
                    "captured_at": photo.captured_at.isoformat(),
                }
                for photo in photos
            ],
        }

    async def list_exportable_sessions(
        self,
        db: AsyncSession,
        page: int = 1,
        limit: int = 20,
        status_filter: Optional[str] = None,
    ) -> Dict:
        """List sessions that can be exported.

        Args:
            db: Database session
            page: Page number
            limit: Items per page
            status_filter: Optional status filter

        Returns:
            Dict with sessions and pagination info
        """
        offset = (page - 1) * limit

        # Build query - only sessions with files (not cleaned)
        query = select(SessionModel).where(SessionModel.files_cleaned == 0)

        if status_filter and status_filter != "all":
            query = query.where(SessionModel.status == status_filter)

        query = query.order_by(SessionModel.created_at.desc())

        # Get count
        from sqlalchemy import func

        count_query = select(func.count(SessionModel.id)).where(
            SessionModel.files_cleaned == 0
        )
        if status_filter and status_filter != "all":
            count_query = count_query.where(SessionModel.status == status_filter)

        result = await db.execute(count_query)
        total = result.scalar() or 0

        # Get sessions
        result = await db.execute(query.offset(offset).limit(limit))
        sessions = result.scalars().all()

        return {
            "sessions": [
                {
                    "id": s.id,
                    "created_at": s.created_at.isoformat(),
                    "status": s.status,
                    "language": s.language,
                    "has_composite": bool(s.composite_path),
                }
                for s in sessions
            ],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit,
            },
        }

    def cleanup_old_exports(self, max_age_hours: int = 24) -> int:
        """Clean up old export files.

        Args:
            max_age_hours: Maximum age of export files to keep

        Returns:
            Number of files deleted
        """
        deleted = 0
        cutoff = datetime.now().timestamp() - (max_age_hours * 3600)

        for filepath in self.exports_dir.glob("*.zip"):
            if filepath.stat().st_mtime < cutoff:
                try:
                    filepath.unlink()
                    deleted += 1
                except Exception as e:
                    logger.warning(f"Failed to delete {filepath}: {e}")

        # Clean up completed job records
        for job_id in list(PhotoExportService._export_jobs.keys()):
            job = PhotoExportService._export_jobs[job_id]
            if job.completed_at:
                age = (datetime.now() - job.completed_at).total_seconds()
                if age > max_age_hours * 3600:
                    del PhotoExportService._export_jobs[job_id]

        if deleted > 0:
            logger.info(f"Cleaned up {deleted} old export files")

        return deleted
