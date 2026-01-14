"""Generate composite use case."""

from dataclasses import dataclass

from app.application.ports.repositories import SessionRepository
from app.application.ports.services import ImageProcessorPort, CompositeOptions
from app.application.use_cases.base import UseCase, UseCaseResult
from app.domain.value_objects import SessionId


@dataclass
class GenerateCompositeInput:
    """Input for generating a composite image."""
    session_id: str
    include_date: bool = True
    include_logo: bool = True


@dataclass
class CompositeOutput:
    """Output of composite generation."""
    composite_path: str


class GenerateCompositeUseCase(UseCase[CompositeOutput]):
    """Use case for generating a 4-cut composite image."""

    def __init__(
        self,
        session_repo: SessionRepository,
        image_processor: ImageProcessorPort,
    ):
        self._session_repo = session_repo
        self._image_processor = image_processor

    async def execute(self, input_data: GenerateCompositeInput) -> UseCaseResult[CompositeOutput]:
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

        photo_paths = [p.path for p in sorted(session.photos, key=lambda p: p.index)]
        output_path = f"sessions/{input_data.session_id}/composite.jpg"

        options = CompositeOptions(
            include_date=input_data.include_date,
            include_logo=input_data.include_logo,
        )

        result = await self._image_processor.generate_composite(
            photo_paths=photo_paths,
            output_path=output_path,
            options=options,
        )

        if not result.success:
            return UseCaseResult.fail("COMPOSITE_FAILED", result.error_message or "Failed to generate composite")

        session.set_composite_path(result.output_path)
        await self._session_repo.save(session)

        return UseCaseResult.ok(CompositeOutput(composite_path=result.output_path))
