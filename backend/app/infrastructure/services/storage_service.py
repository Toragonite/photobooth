"""Storage service for file operations."""

import logging
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import aiofiles

from ...application.ports.services.storage_port import StorageInfo, StoragePort
from ...config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class StorageService(StoragePort):
    """Service for file storage operations."""

    def __init__(self):
        self.photos_path = settings.photos_path
        self.composites_path = settings.composites_path
        self.thumbnails_path = settings.thumbnails_path

    async def save_photo(
        self,
        session_id: str,
        photo_id: str,
        data: bytes,
    ) -> str:
        """Save a photo file and return the path."""
        # Create session directory
        session_dir = self.photos_path / session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        # Save file
        file_path = session_dir / f"{photo_id}.jpg"
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(data)

        logger.info(f"Saved photo: {file_path}")
        return str(file_path)

    async def save_thumbnail(
        self,
        session_id: str,
        photo_id: str,
        data: bytes,
    ) -> str:
        """Save a thumbnail file and return the path."""
        # Create session directory
        session_dir = self.thumbnails_path / session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        # Save file
        file_path = session_dir / f"{photo_id}_thumb.jpg"
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(data)

        logger.info(f"Saved thumbnail: {file_path}")
        return str(file_path)

    async def save_composite(
        self,
        session_id: str,
        data: bytes,
    ) -> str:
        """Save a composite image and return the path."""
        # Create composites directory
        self.composites_path.mkdir(parents=True, exist_ok=True)

        # Save file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = self.composites_path / f"{session_id}_{timestamp}.jpg"
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(data)

        logger.info(f"Saved composite: {file_path}")
        return str(file_path)

    async def read_file(self, path: str) -> Optional[bytes]:
        """Read a file and return its contents."""
        try:
            async with aiofiles.open(path, "rb") as f:
                return await f.read()
        except FileNotFoundError:
            logger.warning(f"File not found: {path}")
            return None

    async def delete_file(self, path: str) -> bool:
        """Delete a file."""
        try:
            os.remove(path)
            logger.info(f"Deleted file: {path}")
            return True
        except FileNotFoundError:
            logger.warning(f"File not found for deletion: {path}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete file {path}: {e}")
            return False

    async def delete_session_files(self, session_id: str) -> bool:
        """Delete all files for a session."""
        try:
            # Delete photos directory
            photos_dir = self.photos_path / session_id
            if photos_dir.exists():
                shutil.rmtree(photos_dir)

            # Delete thumbnails directory
            thumbs_dir = self.thumbnails_path / session_id
            if thumbs_dir.exists():
                shutil.rmtree(thumbs_dir)

            logger.info(f"Deleted session files: {session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete session files {session_id}: {e}")
            return False

    def get_storage_stats(self) -> dict:
        """Get storage statistics."""
        total, used, free = shutil.disk_usage(settings.storage_path)

        # Calculate size of each directory
        photos_size = self._get_dir_size(self.photos_path)
        composites_size = self._get_dir_size(self.composites_path)
        thumbnails_size = self._get_dir_size(self.thumbnails_path)

        return {
            "total_bytes": total,
            "used_bytes": used,
            "free_bytes": free,
            "percent_used": round((used / total) * 100, 1),
            "breakdown": {
                "photos": photos_size,
                "composites": composites_size,
                "thumbnails": thumbnails_size,
            },
        }

    def _get_dir_size(self, path: Path) -> int:
        """Calculate total size of a directory."""
        total = 0
        if path.exists():
            for entry in path.rglob("*"):
                if entry.is_file():
                    total += entry.stat().st_size
        return total

    # ─────────────────────────────────────────────────────────────────
    # StoragePort interface implementation
    # ─────────────────────────────────────────────────────────────────

    async def get_photo_path(self, session_id: str, index: int) -> Optional[str]:
        """Get the path to a stored photo (StoragePort interface)."""
        session_dir = self.photos_path / session_id
        if not session_dir.exists():
            return None

        # Look for photo by index in filename
        for file_path in session_dir.glob("*.jpg"):
            # Photos are stored with photo_id, we need to look at all files
            # and return the first one (or implement index tracking)
            return str(file_path)

        return None

    async def delete_session_photos(self, session_id: str) -> None:
        """Delete all photos for a session (StoragePort interface)."""
        await self.delete_session_files(session_id)

    async def get_composite_path(self, session_id: str) -> Optional[str]:
        """Get the path to a stored composite image (StoragePort interface)."""
        if not self.composites_path.exists():
            return None

        # Look for composite with session_id prefix
        for file_path in self.composites_path.glob(f"{session_id}_*.jpg"):
            return str(file_path)

        return None

    async def get_storage_info(self) -> StorageInfo:
        """Get current storage capacity and usage information (StoragePort interface)."""
        stats = self.get_storage_stats()
        return StorageInfo(
            total_bytes=stats["total_bytes"],
            used_bytes=stats["used_bytes"],
            free_bytes=stats["free_bytes"],
            percent_used=stats["percent_used"],
        )

    async def cleanup_old_sessions(self, days: int) -> int:
        """Delete session data older than the specified days (StoragePort interface)."""
        cutoff = datetime.now() - timedelta(days=days)
        cleaned_count = 0

        # Clean old photo directories
        if self.photos_path.exists():
            for session_dir in self.photos_path.iterdir():
                if session_dir.is_dir():
                    try:
                        # Use directory modification time
                        mtime = datetime.fromtimestamp(session_dir.stat().st_mtime)
                        if mtime < cutoff:
                            shutil.rmtree(session_dir)
                            cleaned_count += 1
                            logger.info(f"Cleaned old session: {session_dir.name}")
                    except Exception as e:
                        logger.error(f"Failed to clean session {session_dir.name}: {e}")

        # Clean old composites
        if self.composites_path.exists():
            for composite_file in self.composites_path.glob("*.jpg"):
                try:
                    mtime = datetime.fromtimestamp(composite_file.stat().st_mtime)
                    if mtime < cutoff:
                        composite_file.unlink()
                        logger.info(f"Cleaned old composite: {composite_file.name}")
                except Exception as e:
                    logger.error(f"Failed to clean composite {composite_file.name}: {e}")

        # Clean old thumbnails
        if self.thumbnails_path.exists():
            for thumb_dir in self.thumbnails_path.iterdir():
                if thumb_dir.is_dir():
                    try:
                        mtime = datetime.fromtimestamp(thumb_dir.stat().st_mtime)
                        if mtime < cutoff:
                            shutil.rmtree(thumb_dir)
                            logger.info(f"Cleaned old thumbnails: {thumb_dir.name}")
                    except Exception as e:
                        logger.error(f"Failed to clean thumbnails {thumb_dir.name}: {e}")

        return cleaned_count
