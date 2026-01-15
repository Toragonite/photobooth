"""Capture photo use case."""

from dataclasses import dataclass

from app.application.dto.session_dto import PhotoDTO
from app.application.ports.repositories import SessionRepository
from app.application.ports.services import ImageProcessorPort, StoragePort
from app.application.use_cases.base import UseCase, UseCaseResult
from app.domain.entities import Photo
from app.domain.value_objects import SessionId


@dataclass
class CapturePhotoInput:
    """Input for capturing a photo."""
    session_id: str
    photo_index: int
    image_data: bytes


class CapturePhotoUseCase(UseCase[PhotoDTO]):
    """Use case for capturing and saving a photo."""

    def __init__(
        self,
        session_repository: SessionRepository,
        storage: StoragePort,
        image_processor: ImageProcessorPort,
    ):
        self._session_repo = session_repository
        self._storage = storage
        self._image_processor = image_processor

    async def execute(self, input_data: CapturePhotoInput) -> UseCaseResult[PhotoDTO]:
        try:
            sid = SessionId(input_data.session_id)
        except ValueError:
            return UseCaseResult.fail("INVALID_SESSION_ID", "Invalid session ID")

        session = await self._session_repo.get_by_id(sid)
        if not session:
            return UseCaseResult.fail("SESSION_NOT_FOUND", "Session not found")

        if input_data.photo_index < 0 or input_data.photo_index >= 4:
            return UseCaseResult.fail("INVALID_INDEX", "Photo index must be 0-3")

        # Check if photo already exists at this index
        existing = session.get_photo(input_data.photo_index)

        # Save photo to storage
        photo_path = await self._storage.save_photo(
            input_data.session_id, input_data.photo_index, input_data.image_data
        )

        # Create photo entity
        photo = Photo.create(index=input_data.photo_index, path=photo_path)

        if existing:
            session.replace_photo(photo)
        else:
            session.add_photo(photo)

        await self._session_repo.save(session)

        return UseCaseResult.ok(
            PhotoDTO(
                index=photo.index,
                path=photo.path,
                thumbnail_path=photo.thumbnail_path,
                captured_at=photo.captured_at,
            )
        )
