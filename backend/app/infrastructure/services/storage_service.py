"""Storage service for file operations."""

import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiofiles

from ...config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class StorageService:
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
