"""Session API endpoints."""

import logging
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

from app.adapters.api.response_utils import handle_result
from app.application.use_cases.session import (CapturePhotoInput,
                                               CreateSessionInput,
                                               GenerateCompositeInput)
from app.infrastructure.dependencies import (AbandonSessionUseCaseDep,
                                             CapturePhotoUseCaseDep,
                                             CreateSessionUseCaseDep,
                                             GenerateCompositeUseCaseDep,
                                             GetSessionUseCaseDep,
                                             SessionRepositoryDep,
                                             StorageServiceDep)

router = APIRouter()
logger = logging.getLogger(__name__)


# Request/Response models
class CreateSessionRequest(BaseModel):
    """Request to create a new session."""

    language: Optional[str] = "ko"
    layout_type: Optional[str] = "2x2"


class SessionResponse(BaseModel):
    """Session response model."""

    success: bool
    data: dict


class PhotoResponse(BaseModel):
    """Photo response model."""

    success: bool
    data: dict


class CompositeRequest(BaseModel):
    """Request to generate composite."""

    include_logo: bool = True
    include_date: bool = True
    include_custom_text: bool = True
    custom_text: str = "2026 Somang Youth\nRwanda missionary"
    frame_type: str = "classic"  # classic, film_strip, polaroid, minimal, rounded, rwanda_*
    layout_type: str = "2x2"  # 2x2 (grid) or 1x4 (vertical strip duplicated)


class UpdateLanguageRequest(BaseModel):
    """Request to update session language."""

    language: str


# Session endpoints
@router.post("/session", response_model=SessionResponse, status_code=201)
async def create_session(
    request: CreateSessionRequest,
    use_case: CreateSessionUseCaseDep,
):
    """Create a new photo session."""
    result = await use_case.execute(
        CreateSessionInput(
            language=request.language or "ko",
            layout_type=request.layout_type or "2x2"
        )
    )

    def transform(data):
        return {
            "session_id": data.session_id,
            "language": data.language,
            "status": data.status,
            "layout_type": data.layout_type,
            "photos": [],
            "photo_count": 0,
            "max_photos": data.required_photos,
        }

    return handle_result(result, transform=transform)


@router.get("/session/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    use_case: GetSessionUseCaseDep,
):
    """Get session details."""
    result = await use_case.execute(session_id)

    def transform(data):
        photos = [
            {
                "index": p.index,
                "thumbnail_url": f"/api/photos/{session_id}/{p.index}/thumbnail",
                "captured_at": p.captured_at.isoformat() if p.captured_at else None,
            }
            for p in sorted(data.photos, key=lambda x: x.index)
        ]

        completed_at = (
            data.completed_at.isoformat() if data.completed_at else None
        )
        composite_url = (
            f"/api/composite/{data.id}" if data.composite_path else None
        )
        return {
            "session_id": data.id,
            "language": data.language,
            "status": data.status,
            "created_at": data.created_at.isoformat() if data.created_at else None,
            "completed_at": completed_at,
            "photos": photos,
            "photo_count": data.photo_count,
            "max_photos": 4,
            "composite_url": composite_url,
        }

    return handle_result(result, transform=transform)


@router.delete("/session/{session_id}", response_model=SessionResponse)
async def abandon_session(
    session_id: str,
    use_case: AbandonSessionUseCaseDep,
):
    """Abandon/delete a session."""
    result = await use_case.execute(session_id)

    def transform(data):
        return {
            "session_id": session_id,
            "status": "abandoned",
            "abandoned": data,
        }

    return handle_result(result, transform=transform)


@router.patch("/session/{session_id}/language", response_model=SessionResponse)
async def update_session_language(
    session_id: str,
    request: UpdateLanguageRequest,
    session_repo: SessionRepositoryDep,
):
    """Update session language.

    Args:
        session_id: Session ID
        request: JSON body with language field
    """
    from app.domain.value_objects import SessionId

    try:
        sid = SessionId(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID")

    session = await session_repo.get_by_id(sid)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Validate language
    valid_languages = ["ko", "en"]
    if request.language not in valid_languages:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid language. Must be one of: {valid_languages}"
        )

    # Update language
    session.language = request.language
    await session_repo.save(session)

    return SessionResponse(
        success=True,
        data={
            "session_id": session_id,
            "language": session.language,
            "updated": True,
        },
    )


# Photo endpoints
@router.post(
    "/session/{session_id}/photos", response_model=PhotoResponse, status_code=201
)
async def upload_photo(
    session_id: str,
    photo: UploadFile = File(...),
    index: int = Form(...),
    use_case: CapturePhotoUseCaseDep = None,
):
    """Upload a captured photo."""
    image_data = await photo.read()

    result = await use_case.execute(
        CapturePhotoInput(
            session_id=session_id,
            photo_index=index,
            image_data=image_data,
        )
    )

    def transform(data):
        return {
            "photo_id": f"{session_id}_{data.index}",
            "index": data.index,
            "thumbnail_url": f"/api/photos/{session_id}/{data.index}/thumbnail",
            "captured_at": data.captured_at.isoformat() if data.captured_at else None,
        }

    return handle_result(result, transform=transform)


@router.put("/session/{session_id}/photos/{index}", response_model=PhotoResponse)
async def replace_photo(
    session_id: str,
    index: int,
    photo: UploadFile = File(...),
    use_case: CapturePhotoUseCaseDep = None,
):
    """Replace/retake a photo at specific index."""
    image_data = await photo.read()

    result = await use_case.execute(
        CapturePhotoInput(
            session_id=session_id,
            photo_index=index,
            image_data=image_data,
        )
    )

    def transform(data):
        return {
            "photo_id": f"{session_id}_{data.index}",
            "index": data.index,
            "thumbnail_url": f"/api/photos/{session_id}/{data.index}/thumbnail",
            "captured_at": data.captured_at.isoformat() if data.captured_at else None,
            "replaced": True,
        }

    return handle_result(result, transform=transform)


@router.get("/photos/{session_id}/{index}/thumbnail")
async def get_photo_thumbnail(
    session_id: str,
    index: int,
    session_repo: SessionRepositoryDep,
    storage: StorageServiceDep,
):
    """Get photo thumbnail."""
    from app.domain.value_objects import SessionId

    try:
        sid = SessionId(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID")

    session = await session_repo.get_by_id(sid)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    photo = session.get_photo(index)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    if not photo.thumbnail_path:
        raise HTTPException(status_code=404, detail="Thumbnail not found")

    data = await storage.read_file(photo.thumbnail_path)
    if not data:
        raise HTTPException(status_code=404, detail="Thumbnail file not found")

    return Response(content=data, media_type="image/jpeg")


@router.get("/photos/{session_id}/{index}/full")
async def get_photo_full(
    session_id: str,
    index: int,
    session_repo: SessionRepositoryDep,
    storage: StorageServiceDep,
):
    """Get full resolution photo."""
    from app.domain.value_objects import SessionId

    try:
        sid = SessionId(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID")

    session = await session_repo.get_by_id(sid)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    photo = session.get_photo(index)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    data = await storage.read_file(photo.file_path)
    if not data:
        raise HTTPException(status_code=404, detail="Photo file not found")

    return Response(content=data, media_type="image/jpeg")


# Composite endpoints
@router.post(
    "/session/{session_id}/composite", response_model=PhotoResponse, status_code=201
)
async def generate_composite(
    session_id: str,
    request: CompositeRequest,
    use_case: GenerateCompositeUseCaseDep,
):
    """Generate composite image from 4 photos."""
    result = await use_case.execute(
        GenerateCompositeInput(
            session_id=session_id,
            include_date=request.include_date,
            include_logo=request.include_logo,
            include_custom_text=request.include_custom_text,
            custom_text=request.custom_text,
            frame_type=request.frame_type,
            layout_type=request.layout_type,
        )
    )

    def transform(data):
        return {
            "composite_id": session_id,
            "composite_url": f"/api/composite/{session_id}",
            "thumbnail_url": f"/api/composite/{session_id}/thumbnail",
        }

    return handle_result(result, transform=transform)


@router.get("/composite/{session_id}")
async def get_composite(
    session_id: str,
    session_repo: SessionRepositoryDep,
    storage: StorageServiceDep,
):
    """Get composite image."""
    from app.domain.value_objects import SessionId

    try:
        sid = SessionId(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID")

    session = await session_repo.get_by_id(sid)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.composite_path:
        raise HTTPException(status_code=404, detail="Composite not generated")

    # Read the composite file
    data = await storage.read_file(session.composite_path)
    if not data:
        raise HTTPException(status_code=404, detail="Composite file not found")

    return Response(content=data, media_type="image/jpeg")


@router.get("/composite/{session_id}/thumbnail")
async def get_composite_thumbnail(
    session_id: str,
    session_repo: SessionRepositoryDep,
    storage: StorageServiceDep,
):
    """Get composite thumbnail."""
    from app.domain.value_objects import SessionId

    try:
        sid = SessionId(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID")

    session = await session_repo.get_by_id(sid)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.composite_path:
        raise HTTPException(status_code=404, detail="Composite not generated")

    # For thumbnail, we could generate on-the-fly or use a cached version
    # For now, return the full composite (frontend can scale)
    data = await storage.read_file(session.composite_path)
    if not data:
        raise HTTPException(status_code=404, detail="Composite file not found")

    return Response(content=data, media_type="image/jpeg")
