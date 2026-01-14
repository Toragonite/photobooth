"""Abandon session use case."""

from app.application.ports.repositories import SessionRepository
from app.application.ports.services import StoragePort
from app.application.use_cases.base import UseCase, UseCaseResult
from app.domain.value_objects import SessionId


class AbandonSessionUseCase(UseCase[bool]):
    """Use case for abandoning a photo session."""

    def __init__(self, session_repo: SessionRepository, storage: StoragePort):
        self._session_repo = session_repo
        self._storage = storage

    async def execute(self, session_id: str) -> UseCaseResult[bool]:
        try:
            sid = SessionId(session_id)
        except ValueError:
            return UseCaseResult.fail("INVALID_SESSION_ID", "Invalid session ID")

        session = await self._session_repo.get_by_id(sid)
        if not session:
            return UseCaseResult.fail("SESSION_NOT_FOUND", "Session not found")

        try:
            session.abandon()
            await self._session_repo.save(session)
            await self._storage.delete_session_photos(session_id)
            return UseCaseResult.ok(True)
        except Exception as e:
            return UseCaseResult.fail("ABANDON_FAILED", str(e))
