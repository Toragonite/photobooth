"""Create session use case."""

from dataclasses import dataclass

from app.application.dto.session_dto import CreateSessionResponse
from app.application.ports.repositories import SessionRepository
from app.application.use_cases.base import UseCase, UseCaseResult
from app.domain.entities import PhotoSession
from app.domain.value_objects import Language, LayoutType


@dataclass
class CreateSessionInput:
    """Input for creating a session."""
    language: str = "ko"
    layout_type: str = "2x2"


class CreateSessionUseCase(UseCase[CreateSessionResponse]):
    """Use case for creating a new photo session."""

    def __init__(self, session_repository: SessionRepository):
        self._session_repo = session_repository

    async def execute(
        self, input_data: CreateSessionInput
    ) -> UseCaseResult[CreateSessionResponse]:
        try:
            language = Language(input_data.language)
        except ValueError:
            language = Language.KOREAN

        try:
            layout_type = LayoutType(input_data.layout_type)
        except ValueError:
            layout_type = LayoutType.GRID_2X2

        session = PhotoSession.create(language=language, layout_type=layout_type)
        await self._session_repo.save(session)

        return UseCaseResult.ok(
            CreateSessionResponse(
                session_id=str(session.id),
                language=session.language.value,
                status=session.status.value,
                layout_type=session.layout_type.value,
                required_photos=session.required_photos,
            )
        )
