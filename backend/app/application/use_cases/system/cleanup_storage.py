"""Cleanup storage use case."""

from dataclasses import dataclass

from app.application.ports.services import StoragePort
from app.application.use_cases.base import UseCase, UseCaseResult


@dataclass
class CleanupStorageInput:
    """Input for cleanup storage."""
    days: int = 7


@dataclass
class CleanupStorageOutput:
    """Output of cleanup storage."""
    sessions_cleaned: int
    bytes_freed: int


class CleanupStorageUseCase(UseCase[CleanupStorageOutput]):
    """Use case for cleaning up old session data."""

    def __init__(self, storage: StoragePort):
        self._storage = storage

    async def execute(self, input_data: CleanupStorageInput) -> UseCaseResult[CleanupStorageOutput]:
        try:
            # Get storage info before cleanup
            before = await self._storage.get_storage_info()

            # Clean up old sessions
            sessions_cleaned = await self._storage.cleanup_old_sessions(days=input_data.days)

            # Get storage info after cleanup
            after = await self._storage.get_storage_info()

            bytes_freed = before.used_bytes - after.used_bytes

            return UseCaseResult.ok(
                CleanupStorageOutput(
                    sessions_cleaned=sessions_cleaned,
                    bytes_freed=max(0, bytes_freed),
                )
            )
        except Exception as e:
            return UseCaseResult.fail("CLEANUP_ERROR", str(e))
