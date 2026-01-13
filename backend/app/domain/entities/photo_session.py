"""PhotoSession entity."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from ..exceptions import SessionError
from ..value_objects import Language, SessionId, SessionStatus
from .photo import Photo


@dataclass
class PhotoSession:
    """A photo booth session with up to 4 photos."""

    id: SessionId
    language: Language
    status: SessionStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    abandoned_at: Optional[datetime] = None
    composite_path: Optional[str] = None
    photos: List[Photo] = field(default_factory=list)

    MAX_PHOTOS = 4

    @classmethod
    def create(
        cls,
        language: Language = Language.KOREAN,
    ) -> "PhotoSession":
        """Create a new session."""
        return cls(
            id=SessionId.generate(),
            language=language,
            status=SessionStatus.ACTIVE,
            created_at=datetime.now(),
        )

    def add_photo(self, photo: Photo) -> None:
        """Add a photo to the session."""
        if self.status != SessionStatus.ACTIVE:
            raise SessionError("Cannot add photos to non-active session")

        if len(self.photos) >= self.MAX_PHOTOS:
            raise SessionError("Session already has maximum photos")

        if any(p.index == photo.index for p in self.photos):
            raise SessionError(f"Photo at index {photo.index} already exists")

        self.photos.append(photo)
        self.photos.sort(key=lambda p: p.index)

        if len(self.photos) == self.MAX_PHOTOS:
            self.status = SessionStatus.COMPLETE
            self.completed_at = datetime.now()

    def replace_photo(self, photo: Photo) -> Photo:
        """Replace a photo at the given index. Returns the replaced photo."""
        if self.status not in (SessionStatus.ACTIVE, SessionStatus.COMPLETE):
            raise SessionError("Cannot replace photos in this session state")

        # Find and remove existing photo at this index
        replaced = None
        for i, p in enumerate(self.photos):
            if p.index == photo.index:
                replaced = self.photos.pop(i)
                break

        # If was complete, go back to active
        if self.status == SessionStatus.COMPLETE:
            self.status = SessionStatus.ACTIVE
            self.completed_at = None

        self.add_photo(photo)
        return replaced

    def mark_printed(self) -> None:
        """Mark session as printed."""
        if self.status != SessionStatus.COMPLETE:
            raise SessionError("Can only print complete sessions")
        self.status = SessionStatus.PRINTED

    def abandon(self) -> None:
        """Abandon the session."""
        if self.status == SessionStatus.PRINTED:
            raise SessionError("Cannot abandon printed session")
        self.status = SessionStatus.ABANDONED
        self.abandoned_at = datetime.now()

    def set_composite_path(self, path: str) -> None:
        """Set the composite image path."""
        self.composite_path = path

    @property
    def is_complete(self) -> bool:
        return len(self.photos) == self.MAX_PHOTOS

    @property
    def photo_count(self) -> int:
        return len(self.photos)

    def get_photo(self, index: int) -> Optional[Photo]:
        """Get photo by index."""
        for photo in self.photos:
            if photo.index == index:
                return photo
        return None
