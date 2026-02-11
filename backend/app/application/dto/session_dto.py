"""Session-related Data Transfer Objects."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class PhotoDTO:
    """Data transfer object for a single photo."""
    index: int
    path: str
    thumbnail_path: Optional[str] = None
    captured_at: Optional[datetime] = None


@dataclass
class SessionDTO:
    """Data transfer object for a photo session."""
    id: str
    language: str
    status: str
    photo_count: int
    layout_type: str = "2x2"
    required_photos: int = 4
    photos: List[PhotoDTO] = field(default_factory=list)
    composite_path: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class CreateSessionRequest:
    """Request to create a new photo session."""
    language: str = "ko"
    layout_type: str = "2x2"


@dataclass
class CreateSessionResponse:
    """Response after creating a new session."""
    session_id: str
    language: str
    status: str = "active"
    layout_type: str = "2x2"
    required_photos: int = 4
