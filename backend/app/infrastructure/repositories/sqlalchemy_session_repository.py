"""SQLAlchemy implementation of SessionRepository."""

from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.application.ports.repositories import SessionRepository
from app.domain.entities import Photo, PhotoSession
from app.domain.value_objects import (Language, PhotoId, SessionId,
                                      SessionStatus)
from app.infrastructure.database import PhotoModel, SessionModel


class SQLAlchemySessionRepository(SessionRepository):
    """SQLAlchemy implementation of session repository."""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def save(self, session: PhotoSession) -> None:
        """Save or update a photo session."""
        # Check if session exists with photos eagerly loaded
        stmt = (
            select(SessionModel)
            .options(selectinload(SessionModel.photos))
            .where(SessionModel.id == session.id.value)
        )
        result = await self._db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            # Update existing session
            existing.language = session.language.value
            existing.status = session.status.value
            existing.completed_at = session.completed_at
            existing.abandoned_at = session.abandoned_at
            existing.composite_path = session.composite_path

            # Sync photos - delete removed, add new, update existing
            existing_photo_ids = {p.id for p in existing.photos}
            new_photo_ids = {p.id.value for p in session.photos}

            # Remove deleted photos
            for photo_model in list(existing.photos):
                if photo_model.id not in new_photo_ids:
                    await self._db.delete(photo_model)

            # Add or update photos
            for photo in session.photos:
                if photo.id.value in existing_photo_ids:
                    # Update existing photo
                    for photo_model in existing.photos:
                        if photo_model.id == photo.id.value:
                            photo_model.index = photo.index
                            photo_model.file_path = photo.file_path
                            photo_model.thumbnail_path = photo.thumbnail_path
                            photo_model.file_size = photo.size_bytes
                            photo_model.width = photo.width
                            photo_model.height = photo.height
                            photo_model.captured_at = photo.captured_at
                            break
                else:
                    # Add new photo
                    photo_model = self._photo_to_model(photo)
                    existing.photos.append(photo_model)
        else:
            # Create new session
            session_model = self._session_to_model(session)
            self._db.add(session_model)

        await self._db.commit()

    async def get_by_id(self, session_id: SessionId) -> Optional[PhotoSession]:
        """Retrieve a photo session by its ID."""
        stmt = (
            select(SessionModel)
            .options(selectinload(SessionModel.photos))
            .where(SessionModel.id == session_id.value)
        )
        result = await self._db.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return self._model_to_session(model)

    async def get_active_sessions(self) -> List[PhotoSession]:
        """Retrieve all active sessions."""
        stmt = (
            select(SessionModel)
            .options(selectinload(SessionModel.photos))
            .where(SessionModel.status == SessionStatus.ACTIVE.value)
            .order_by(SessionModel.created_at.desc())
        )
        result = await self._db.execute(stmt)
        models = result.scalars().all()

        return [self._model_to_session(m) for m in models]

    async def delete(self, session_id: SessionId) -> None:
        """Delete a photo session."""
        model = await self._db.get(SessionModel, session_id.value)
        if model:
            await self._db.delete(model)
            await self._db.commit()

    async def get_expired_sessions(self, expiry_minutes: int) -> List[PhotoSession]:
        """Retrieve sessions that have expired."""
        expiry_time = datetime.now() - timedelta(minutes=expiry_minutes)

        stmt = (
            select(SessionModel)
            .options(selectinload(SessionModel.photos))
            .where(
                SessionModel.status == SessionStatus.ACTIVE.value,
                SessionModel.created_at < expiry_time,
            )
            .order_by(SessionModel.created_at)
        )
        result = await self._db.execute(stmt)
        models = result.scalars().all()

        return [self._model_to_session(m) for m in models]

    # ─────────────────────────────────────────────────────────────────
    # Mappers
    # ─────────────────────────────────────────────────────────────────

    def _session_to_model(self, session: PhotoSession) -> SessionModel:
        """Convert domain entity to database model."""
        model = SessionModel(
            id=session.id.value,
            language=session.language.value,
            status=session.status.value,
            created_at=session.created_at,
            completed_at=session.completed_at,
            abandoned_at=session.abandoned_at,
            composite_path=session.composite_path,
        )

        for photo in session.photos:
            model.photos.append(self._photo_to_model(photo))

        return model

    def _model_to_session(self, model: SessionModel) -> PhotoSession:
        """Convert database model to domain entity."""
        photos = [self._model_to_photo(p) for p in model.photos]
        photos.sort(key=lambda p: p.index)

        return PhotoSession(
            id=SessionId.from_string(model.id),
            language=Language(model.language),
            status=SessionStatus(model.status),
            created_at=model.created_at,
            completed_at=model.completed_at,
            abandoned_at=model.abandoned_at,
            composite_path=model.composite_path,
            photos=photos,
        )

    def _photo_to_model(self, photo: Photo) -> PhotoModel:
        """Convert Photo entity to database model."""
        return PhotoModel(
            id=photo.id.value,
            session_id=photo.session_id.value,
            index=photo.index,
            file_path=photo.file_path,
            thumbnail_path=photo.thumbnail_path,
            captured_at=photo.captured_at,
            file_size=photo.size_bytes,
            width=photo.width,
            height=photo.height,
        )

    def _model_to_photo(self, model: PhotoModel) -> Photo:
        """Convert database model to Photo entity."""
        return Photo(
            id=PhotoId.from_string(model.id),
            session_id=SessionId.from_string(model.session_id),
            index=model.index,
            file_path=model.file_path,
            thumbnail_path=model.thumbnail_path,
            width=model.width,
            height=model.height,
            size_bytes=model.file_size,
            captured_at=model.captured_at,
        )
