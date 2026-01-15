"""Health check use case."""

from dataclasses import dataclass

from app.application.ports.services import (PrinterPort, StoragePort,
                                            SystemServicePort)
from app.application.use_cases.base import UseCase, UseCaseResult


@dataclass
class HealthCheckOutput:
    """Output of health check."""
    healthy: bool
    status: str
    details: dict


class HealthCheckUseCase(UseCase[HealthCheckOutput]):
    """Use case for system health check."""

    def __init__(
        self,
        system_service: SystemServicePort,
        storage: StoragePort,
        printer: PrinterPort,
    ):
        self._system = system_service
        self._storage = storage
        self._printer = printer

    async def execute(self) -> UseCaseResult[HealthCheckOutput]:
        try:
            issues = []
            details = {}

            # Check printer
            try:
                printer_ready = await self._printer.is_ready()
                details["printer"] = "ready" if printer_ready else "not_ready"
                if not printer_ready:
                    issues.append("Printer not ready")
            except Exception as e:
                details["printer"] = f"error: {str(e)}"
                issues.append(f"Printer check failed: {str(e)}")

            # Check storage
            try:
                storage_info = await self._storage.get_storage_info()
                details["storage"] = {
                    "percent_used": storage_info.percent_used,
                    "free_gb": storage_info.free_bytes / (1024**3),
                }
                if storage_info.is_critical:
                    issues.append("Storage critically low")
            except Exception as e:
                details["storage"] = f"error: {str(e)}"
                issues.append(f"Storage check failed: {str(e)}")

            # Check system health
            try:
                health = await self._system.get_health()
                details["system"] = {
                    "cpu_percent": health.cpu_percent,
                    "memory_percent": health.memory_percent,
                    "temperature": health.temperature,
                }
            except Exception as e:
                details["system"] = f"error: {str(e)}"
                issues.append(f"System check failed: {str(e)}")

            # Determine overall health
            healthy = len(issues) == 0
            if healthy:
                status = "healthy"
            elif len(issues) < 2:
                status = "degraded"
            else:
                status = "critical"

            return UseCaseResult.ok(
                HealthCheckOutput(
                    healthy=healthy,
                    status=status,
                    details=details,
                )
            )
        except Exception as e:
            return UseCaseResult.fail("HEALTH_CHECK_ERROR", str(e))
