"""Get session use case."""

from app.application.dto.session_dto import PhotoDTO, SessionDTO
from app.application.ports.repositories import SessionRepository
from app.application.use_cases.base import UseCase, UseCaseResult
from app.domain.value_objects import SessionId


class GetSessionUseCase(UseCase[SessionDTO]):
    """Use case for retrieving a photo session."""

    def __init__(self, session_repository: SessionRepository):
        self._session_repo = session_repository

    async def execute(self, session_id: str) -> UseCaseResult[SessionDTO]:
        try:
            sid = SessionId(session_id)
        except ValueError:
            return UseCaseResult.fail("INVALID_SESSION_ID", "Invalid session ID format")

        session = await self._session_repo.get_by_id(sid)
        if not session:
            return UseCaseResult.fail("SESSION_NOT_FOUND", "Session not found")

        photos = [
            PhotoDTO(
                index=p.index,
                path=p.path,
                thumbnail_path=p.thumbnail_path,
                captured_at=p.captured_at,
            )
            for p in session.photos
        ]

        return UseCaseResult.ok(
            SessionDTO(
                id=str(session.id),
                language=session.language.value,
                status=session.status.value,
                photo_count=session.photo_count,
                photos=photos,
                composite_path=session.composite_path,
                created_at=session.created_at,
                completed_at=session.completed_at,
            )
        )
