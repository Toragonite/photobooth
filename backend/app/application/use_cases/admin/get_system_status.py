"""Get system status use case."""

from app.application.dto.admin_dto import SystemStatusDTO
from app.application.ports.repositories import PrintJobRepository
from app.application.ports.services import (PrinterPort, StoragePort,
                                            SystemServicePort)
from app.application.use_cases.base import UseCase, UseCaseResult
from app.domain.value_objects import PrintStatus


class GetSystemStatusUseCase(UseCase[SystemStatusDTO]):
    """Use case for retrieving system status."""

    def __init__(
        self,
        system_service: SystemServicePort,
        storage: StoragePort,
        printer: PrinterPort,
        print_job_repository: PrintJobRepository,
    ):
        self._system = system_service
        self._storage = storage
        self._printer = printer
        self._print_job_repo = print_job_repository

    async def execute(self) -> UseCaseResult[SystemStatusDTO]:
        try:
            # Get all printer statuses
            all_printer_statuses = await self._printer.get_all_printer_statuses()

            # Get storage info
            storage_info = await self._storage.get_storage_info()

            # Get system health (for future health metrics integration)
            await self._system.get_health()

            # Get activity stats
            completed_count = await self._print_job_repo.count_by_status(PrintStatus.COMPLETED)
            failed_count = await self._print_job_repo.count_by_status(PrintStatus.FAILED)
            pending_count = await self._print_job_repo.count_by_status(PrintStatus.PENDING)

            # Determine overall health based on all printers
            any_ready = any(ps.is_ready for ps in all_printer_statuses)
            any_connected = any(ps.connected for ps in all_printer_statuses)

            overall_health = "healthy"
            if not any_ready or storage_info.is_critical:
                overall_health = "degraded"
            if not any_connected:
                overall_health = "critical"

            # Build printers list for response
            printers_data = [
                {
                    "name": ps.name,
                    "status": ps.status,
                    "connected": ps.connected,
                    "is_ready": ps.is_ready,
                    "paper_status": ps.paper_status,
                    "ink_status": ps.ink_status,
                    "queue_length": ps.queue_length,
                    "error_message": ps.error_message,
                }
                for ps in all_printer_statuses
            ]

            # Backward-compatible 'printer' field (primary printer)
            primary_status = all_printer_statuses[0] if all_printer_statuses else None
            printer_compat = {
                "name": primary_status.name if primary_status else "No printer",
                "status": primary_status.status if primary_status else "offline",
                "connected": primary_status.connected if primary_status else False,
                "paper_status": primary_status.paper_status if primary_status else "unknown",
                "ink_status": primary_status.ink_status if primary_status else "unknown",
                "queue_length": primary_status.queue_length if primary_status else 0,
            }

            return UseCaseResult.ok(
                SystemStatusDTO(
                    overall_health=overall_health,
                    printer=printer_compat,
                    printers=printers_data,
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
