"""Generate composite use case."""

from dataclasses import dataclass

import aiofiles

from app.application.ports.repositories import SessionRepository
from app.application.ports.services import StoragePort
from app.application.ports.services.image_processor_port import FrameType, LayoutType
from app.application.use_cases.base import UseCase, UseCaseResult
from app.domain.value_objects import SessionId
from app.infrastructure.services.image_processor import ImageProcessor


@dataclass
class GenerateCompositeInput:
    """Input for generating a composite image."""
    session_id: str
    include_date: bool = True
    include_logo: bool = True
    include_custom_text: bool = True
    custom_text: str = "2026 Somang Youth\nRwanda missionary"
    frame_type: str = "classic"  # classic, film_strip, polaroid, minimal, rounded, rwanda_*
    layout_type: str = "2x2"  # 2x2 (grid) or 1x4 (vertical strip duplicated)


@dataclass
class CompositeOutput:
    """Output of composite generation."""
    composite_path: str


class GenerateCompositeUseCase(UseCase[CompositeOutput]):
    """Use case for generating a 4-cut composite image."""

    def __init__(
        self,
        session_repository: SessionRepository,
        storage: StoragePort,
    ):
        self._session_repo = session_repository
        self._storage = storage

    async def execute(
        self, input_data: GenerateCompositeInput
    ) -> UseCaseResult[CompositeOutput]:
        try:
            sid = SessionId(input_data.session_id)
        except ValueError:
            return UseCaseResult.fail("INVALID_SESSION_ID", "Invalid session ID")

        session = await self._session_repo.get_by_id(sid)
        if not session:
            return UseCaseResult.fail("SESSION_NOT_FOUND", "Session not found")

        if session.photo_count < 4:
            return UseCaseResult.fail(
                "INCOMPLETE_SESSION", "Need 4 photos to generate composite"
            )

        # Get photo paths sorted by index
        photo_paths = [p.file_path for p in sorted(session.photos, key=lambda p: p.index)]

        try:
            # Read all photos
            photos_data = []
            for path in photo_paths:
                async with aiofiles.open(path, "rb") as f:
                    photos_data.append(await f.read())

            # Parse frame type
            try:
                frame_type = FrameType(input_data.frame_type)
            except ValueError:
                frame_type = FrameType.CLASSIC

            # Parse layout type
            try:
                layout_type = LayoutType(input_data.layout_type)
            except ValueError:
                layout_type = LayoutType.GRID_2X2

            # Create composite using ImageProcessor
            image_processor = ImageProcessor()
            composite_data = image_processor.create_composite(
                photos=photos_data,
                include_date=input_data.include_date,
                include_logo=input_data.include_logo,
                frame_type=frame_type,
                layout_type=layout_type,
                include_custom_text=input_data.include_custom_text,
                custom_text=input_data.custom_text,
            )

            # Save composite using storage service
            composite_path = await self._storage.save_composite(
                input_data.session_id, composite_data
            )

            session.set_composite_path(composite_path)
            await self._session_repo.save(session)

            return UseCaseResult.ok(CompositeOutput(composite_path=composite_path))

        except Exception as e:
            return UseCaseResult.fail("COMPOSITE_FAILED", f"Failed to generate composite: {e}")
