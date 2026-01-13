"""Session API endpoints."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...domain import Language, PhotoId, SessionStatus
from ...domain.entities import PhotoSession
from ...infrastructure.database import PhotoModel, SessionModel, get_db
from ...infrastructure.services import ImageProcessor, StorageService

router = APIRouter()
logger = logging.getLogger(__name__)


# Request/Response models
class CreateSessionRequest(BaseModel):
    """Request to create a new session."""

    language: Optional[str] = "ko"


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


# Endpoints
@router.post("/session", response_model=SessionResponse, status_code=201)
async def create_session(
    request: CreateSessionRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new photo session."""
    try:
        language = Language(request.language)
    except ValueError:
        language = Language.KOREAN

    # Create session
    session = PhotoSession.create(language=language)

    # Save to database
    db_session = SessionModel(
        id=str(session.id),
        language=session.language.value,
        status=session.status.value,
        created_at=session.created_at,
    )
    db.add(db_session)
    await db.commit()

    logger.info(f"Created session: {session.id}")

    return SessionResponse(
        success=True,
        data={
            "session_id": str(session.id),
            "language": session.language.value,
            "status": session.status.value,
            "created_at": session.created_at.isoformat(),
            "photos": [],
            "photo_count": 0,
            "max_photos": 4,
        },
    )


@router.get("/session/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get session details."""
    result = await db.execute(
        select(SessionModel)
        .where(SessionModel.id == session_id)
        .options(selectinload(SessionModel.photos))
    )
    db_session = result.scalar_one_or_none()

    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")

    photos = [
        {
            "id": p.id,
            "index": p.index,
            "thumbnail_url": f"/api/photos/{p.id}/thumbnail",
            "captured_at": p.captured_at.isoformat(),
        }
        for p in sorted(db_session.photos, key=lambda x: x.index)
    ]

    return SessionResponse(
        success=True,
        data={
            "session_id": db_session.id,
            "language": db_session.language,
            "status": db_session.status,
            "created_at": db_session.created_at.isoformat(),
            "completed_at": (
                db_session.completed_at.isoformat() if db_session.completed_at else None
            ),
            "photos": photos,
            "photo_count": len(photos),
            "max_photos": 4,
            "composite_url": (
                f"/api/composite/{db_session.id}" if db_session.composite_path else None
            ),
        },
    )


@router.patch("/session/{session_id}/language", response_model=SessionResponse)
async def update_session_language(
    session_id: str,
    request: CreateSessionRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update session language."""
    result = await db.execute(select(SessionModel).where(SessionModel.id == session_id))
    db_session = result.scalar_one_or_none()

    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        language = Language(request.language)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid language")

    db_session.language = language.value
    await db.commit()

    return SessionResponse(
        success=True,
        data={
            "session_id": db_session.id,
            "language": db_session.language,
        },
    )


@router.delete("/session/{session_id}", response_model=SessionResponse)
async def abandon_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Abandon/delete a session."""
    result = await db.execute(select(SessionModel).where(SessionModel.id == session_id))
    db_session = result.scalar_one_or_none()

    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")

    if db_session.status == SessionStatus.PRINTED.value:
        raise HTTPException(status_code=400, detail="Cannot abandon printed session")

    from datetime import datetime

    db_session.status = SessionStatus.ABANDONED.value
    db_session.abandoned_at = datetime.now()
    await db.commit()

    # Clean up files
    storage_service = StorageService()
    await storage_service.delete_session_files(session_id)

    logger.info(f"Abandoned session: {session_id}")

    return SessionResponse(
        success=True,
        data={
            "session_id": db_session.id,
            "status": db_session.status,
        },
    )


@router.post(
    "/session/{session_id}/photos", response_model=PhotoResponse, status_code=201
)
async def upload_photo(
    session_id: str,
    photo: UploadFile = File(...),
    index: int = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload a captured photo."""
    # Get session
    result = await db.execute(
        select(SessionModel)
        .where(SessionModel.id == session_id)
        .options(selectinload(SessionModel.photos))
    )
    db_session = result.scalar_one_or_none()

    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")

    if db_session.status not in (
        SessionStatus.ACTIVE.value,
        SessionStatus.COMPLETE.value,
    ):
        raise HTTPException(status_code=400, detail="Session is not active")

    if index < 0 or index > 3:
        raise HTTPException(status_code=400, detail="Index must be 0-3")

    # Check if photo at index exists
    existing_photo = None
    for p in db_session.photos:
        if p.index == index:
            existing_photo = p
            break

    if existing_photo:
        raise HTTPException(
            status_code=409,
            detail=f"Photo at index {index} already exists. Use PUT to replace.",
        )

    # Read and validate image
    image_data = await photo.read()
    image_processor = ImageProcessor()

    is_valid, error_msg, dimensions = image_processor.validate_image(image_data)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    # Create thumbnail
    thumbnail_data, width, height = image_processor.create_thumbnail(image_data)

    # Save files
    storage_service = StorageService()
    photo_id = str(PhotoId.generate())

    file_path = await storage_service.save_photo(session_id, photo_id, image_data)
    thumbnail_path = await storage_service.save_thumbnail(
        session_id, photo_id, thumbnail_data
    )

    # Save to database
    from datetime import datetime

    db_photo = PhotoModel(
        id=photo_id,
        session_id=session_id,
        index=index,
        file_path=file_path,
        thumbnail_path=thumbnail_path,
        captured_at=datetime.now(),
        file_size=len(image_data),
        width=width,
        height=height,
    )
    db.add(db_photo)

    # Update session status if 4 photos
    photo_count = len(db_session.photos) + 1
    if photo_count == 4:
        db_session.status = SessionStatus.COMPLETE.value
        db_session.completed_at = datetime.now()

    await db.commit()

    logger.info(f"Uploaded photo {photo_id} to session {session_id} at index {index}")

    return PhotoResponse(
        success=True,
        data={
            "photo_id": photo_id,
            "index": index,
            "thumbnail_url": f"/api/photos/{photo_id}/thumbnail",
            "captured_at": db_photo.captured_at.isoformat(),
            "session_photo_count": photo_count,
        },
    )


@router.put("/session/{session_id}/photos/{index}", response_model=PhotoResponse)
async def replace_photo(
    session_id: str,
    index: int,
    photo: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Replace/retake a photo at specific index."""
    # Get session
    result = await db.execute(
        select(SessionModel)
        .where(SessionModel.id == session_id)
        .options(selectinload(SessionModel.photos))
    )
    db_session = result.scalar_one_or_none()

    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")

    if db_session.status not in (
        SessionStatus.ACTIVE.value,
        SessionStatus.COMPLETE.value,
    ):
        raise HTTPException(status_code=400, detail="Session is not active")

    if index < 0 or index > 3:
        raise HTTPException(status_code=400, detail="Index must be 0-3")

    # Find existing photo
    existing_photo = None
    for p in db_session.photos:
        if p.index == index:
            existing_photo = p
            break

    # Read and validate image
    image_data = await photo.read()
    image_processor = ImageProcessor()

    is_valid, error_msg, dimensions = image_processor.validate_image(image_data)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    # Create thumbnail
    thumbnail_data, width, height = image_processor.create_thumbnail(image_data)

    # Save files
    storage_service = StorageService()
    photo_id = str(PhotoId.generate())

    file_path = await storage_service.save_photo(session_id, photo_id, image_data)
    thumbnail_path = await storage_service.save_thumbnail(
        session_id, photo_id, thumbnail_data
    )

    # Delete old photo if exists
    old_photo_id = None
    if existing_photo:
        old_photo_id = existing_photo.id
        await storage_service.delete_file(existing_photo.file_path)
        await storage_service.delete_file(existing_photo.thumbnail_path)
        await db.delete(existing_photo)

    # Save new photo
    from datetime import datetime

    db_photo = PhotoModel(
        id=photo_id,
        session_id=session_id,
        index=index,
        file_path=file_path,
        thumbnail_path=thumbnail_path,
        captured_at=datetime.now(),
        file_size=len(image_data),
        width=width,
        height=height,
    )
    db.add(db_photo)

    # Reset composite if session was complete
    if db_session.composite_path:
        db_session.composite_path = None
        db_session.status = SessionStatus.ACTIVE.value
        db_session.completed_at = None

    await db.commit()

    logger.info(f"Replaced photo at index {index} in session {session_id}")

    return PhotoResponse(
        success=True,
        data={
            "photo_id": photo_id,
            "index": index,
            "thumbnail_url": f"/api/photos/{photo_id}/thumbnail",
            "captured_at": db_photo.captured_at.isoformat(),
            "replaced_photo_id": old_photo_id,
        },
    )


@router.get("/photos/{photo_id}/thumbnail")
async def get_photo_thumbnail(
    photo_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get photo thumbnail."""
    result = await db.execute(select(PhotoModel).where(PhotoModel.id == photo_id))
    db_photo = result.scalar_one_or_none()

    if not db_photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    storage_service = StorageService()
    data = await storage_service.read_file(db_photo.thumbnail_path)

    if not data:
        raise HTTPException(status_code=404, detail="Thumbnail file not found")

    return Response(content=data, media_type="image/jpeg")


@router.get("/photos/{photo_id}/full")
async def get_photo_full(
    photo_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get full resolution photo."""
    result = await db.execute(select(PhotoModel).where(PhotoModel.id == photo_id))
    db_photo = result.scalar_one_or_none()

    if not db_photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    storage_service = StorageService()
    data = await storage_service.read_file(db_photo.file_path)

    if not data:
        raise HTTPException(status_code=404, detail="Photo file not found")

    return Response(content=data, media_type="image/jpeg")


@router.post(
    "/session/{session_id}/composite", response_model=PhotoResponse, status_code=201
)
async def generate_composite(
    session_id: str,
    request: CompositeRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generate composite image from 4 photos."""
    # Get session with photos
    result = await db.execute(
        select(SessionModel)
        .where(SessionModel.id == session_id)
        .options(selectinload(SessionModel.photos))
    )
    db_session = result.scalar_one_or_none()

    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")

    if len(db_session.photos) != 4:
        raise HTTPException(
            status_code=400,
            detail=f"Session needs 4 photos, has {len(db_session.photos)}",
        )

    # Read photo files
    storage_service = StorageService()
    photos_data = []

    for photo in sorted(db_session.photos, key=lambda x: x.index):
        data = await storage_service.read_file(photo.file_path)
        if not data:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to read photo {photo.index}",
            )
        photos_data.append(data)

    # Generate composite
    image_processor = ImageProcessor()
    try:
        composite_data = image_processor.create_composite(
            photos_data,
            include_date=request.include_date,
            include_logo=request.include_logo,
        )
    except Exception as e:
        logger.error(f"Failed to generate composite: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate composite")

    # Save composite
    composite_path = await storage_service.save_composite(session_id, composite_data)

    # Update session
    db_session.composite_path = composite_path
    db_session.status = SessionStatus.COMPLETE.value
    from datetime import datetime

    db_session.completed_at = datetime.now()
    await db.commit()

    logger.info(f"Generated composite for session {session_id}")

    return PhotoResponse(
        success=True,
        data={
            "composite_id": session_id,
            "composite_url": f"/api/composite/{session_id}",
            "thumbnail_url": f"/api/composite/{session_id}/thumbnail",
            "dimensions": {
                "width": image_processor.COMPOSITE_WIDTH,
                "height": image_processor.COMPOSITE_HEIGHT,
                "dpi": 300,
            },
        },
    )


@router.get("/composite/{session_id}")
async def get_composite(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get composite image."""
    result = await db.execute(select(SessionModel).where(SessionModel.id == session_id))
    db_session = result.scalar_one_or_none()

    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not db_session.composite_path:
        raise HTTPException(status_code=404, detail="Composite not generated")

    storage_service = StorageService()
    data = await storage_service.read_file(db_session.composite_path)

    if not data:
        raise HTTPException(status_code=404, detail="Composite file not found")

    return Response(content=data, media_type="image/jpeg")


@router.get("/composite/{session_id}/thumbnail")
async def get_composite_thumbnail(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get composite thumbnail."""
    result = await db.execute(select(SessionModel).where(SessionModel.id == session_id))
    db_session = result.scalar_one_or_none()

    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not db_session.composite_path:
        raise HTTPException(status_code=404, detail="Composite not generated")

    storage_service = StorageService()
    data = await storage_service.read_file(db_session.composite_path)

    if not data:
        raise HTTPException(status_code=404, detail="Composite file not found")

    # Generate thumbnail
    image_processor = ImageProcessor()
    thumbnail_data, _, _ = image_processor.create_thumbnail(data)

    return Response(content=thumbnail_data, media_type="image/jpeg")
