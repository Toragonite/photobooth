"""Get system status use case."""

from datetime import datetime

from app.application.dto.admin_dto import SystemStatusDTO
from app.application.ports.repositories import PrintJobRepository
from app.application.ports.services import PrinterPort, StoragePort, SystemServicePort
from app.application.use_cases.base import UseCase, UseCaseResult
from app.domain.value_objects import PrintStatus


class GetSystemStatusUseCase(UseCase[SystemStatusDTO]):
    """Use case for retrieving system status."""

    def __init__(
        self,
        print_job_repo: PrintJobRepository,
        printer: PrinterPort,
        storage: StoragePort,
        system: SystemServicePort,
    ):
        self._print_job_repo = print_job_repo
        self._printer = printer
        self._storage = storage
        self._system = system

    async def execute(self) -> UseCaseResult[SystemStatusDTO]:
        try:
            # Get printer status
            printer_status = await self._printer.get_printer_status()

            # Get storage info
            storage_info = await self._storage.get_storage_info()

            # Get system health
            health = await self._system.get_health()

            # Get activity stats
            completed_count = await self._print_job_repo.count_by_status(PrintStatus.COMPLETED)
            failed_count = await self._print_job_repo.count_by_status(PrintStatus.FAILED)
            pending_count = await self._print_job_repo.count_by_status(PrintStatus.PENDING)

            # Determine overall health
            overall_health = "healthy"
            if not printer_status.is_ready or storage_info.is_critical:
                overall_health = "degraded"
            if not printer_status.connected:
                overall_health = "critical"

            return UseCaseResult.ok(
                SystemStatusDTO(
                    overall_health=overall_health,
                    printer={
                        "name": "Canon Selphy CP1500",
                        "status": printer_status.status,
                        "connected": printer_status.connected,
                        "paper_status": printer_status.paper_status,
                        "ink_status": printer_status.ink_status,
                        "queue_length": printer_status.queue_length,
                    },
                    storage={
                        "total_bytes": storage_info.total_bytes,
                        "used_bytes": storage_info.used_bytes,
                        "free_bytes": storage_info.free_bytes,
                        "percent_used": storage_info.percent_used,
                    },
                    activity={
                        "prints_total": completed_count + failed_count + pending_count,
                        "prints_completed": completed_count,
                        "prints_failed": failed_count,
                        "prints_pending": pending_count,
                    },
                )
            )
        except Exception as e:
            return UseCaseResult.fail("STATUS_ERROR", str(e))
