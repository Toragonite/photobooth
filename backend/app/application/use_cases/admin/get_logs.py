"""Get logs use case."""

from dataclasses import dataclass
from typing import Optional

from app.application.dto.admin_dto import LogsDTO
from app.application.ports.services import SystemServicePort
from app.application.use_cases.base import UseCase, UseCaseResult


@dataclass
class GetLogsInput:
    """Input for getting logs."""
    source: str = "all"
    limit: int = 100
    level: Optional[str] = None


class GetLogsUseCase(UseCase[LogsDTO]):
    """Use case for retrieving system logs."""

    def __init__(self, system: SystemServicePort):
        self._system = system

    async def execute(self, input_data: GetLogsInput) -> UseCaseResult[LogsDTO]:
        try:
            entries = await self._system.get_logs(
                source=input_data.source,
                limit=input_data.limit,
                level=input_data.level,
            )

            entry_dicts = [
                {
                    "timestamp": entry.timestamp,
                    "level": entry.level,
                    "source": entry.source,
                    "message": entry.message,
                }
                for entry in entries
            ]

            return UseCaseResult.ok(
                LogsDTO(
                    entries=entry_dicts,
                    source=input_data.source,
                    total=len(entry_dicts),
                )
            )
        except Exception as e:
            return UseCaseResult.fail("LOGS_ERROR", str(e))
