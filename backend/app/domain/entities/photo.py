"""Photo entity."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ..exceptions import InvalidPhotoError
from ..value_objects import PhotoId, SessionId


@dataclass
class Photo:
    """A captured photograph."""

    id: PhotoId
    session_id: SessionId
    index: int
    file_path: str
    thumbnail_path: str
    width: int
    height: int
    size_bytes: int
    captured_at: datetime

    MAX_SIZE_BYTES = 5 * 1024 * 1024  # 5MB
    MIN_WIDTH = 640
    MIN_HEIGHT = 480
    VALID_INDICES = (0, 1, 2, 3)

    def __post_init__(self):
        self._validate()

    def _validate(self):
        if self.index not in self.VALID_INDICES:
            raise InvalidPhotoError(f"Index must be 0-3, got {self.index}")

        if self.size_bytes > self.MAX_SIZE_BYTES:
            raise InvalidPhotoError(
                f"Photo exceeds max size of {self.MAX_SIZE_BYTES} bytes"
            )

        if self.width < self.MIN_WIDTH or self.height < self.MIN_HEIGHT:
            raise InvalidPhotoError(
                f"Photo dimensions {self.width}x{self.height} below minimum "
                f"{self.MIN_WIDTH}x{self.MIN_HEIGHT}"
            )

    @classmethod
    def create(
        cls,
        session_id: SessionId,
        index: int,
        file_path: str,
        thumbnail_path: str,
        width: int,
        height: int,
        size_bytes: int,
        captured_at: Optional[datetime] = None,
    ) -> "Photo":
        """Factory method to create a Photo with validation."""
        return cls(
            id=PhotoId.generate(),
            session_id=session_id,
            index=index,
            file_path=file_path,
            thumbnail_path=thumbnail_path,
            width=width,
            height=height,
            size_bytes=size_bytes,
            captured_at=captured_at or datetime.now(),
        )
