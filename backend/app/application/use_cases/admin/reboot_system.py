"""Reboot system use case."""

from dataclasses import dataclass

from app.application.ports.repositories import PrintJobRepository
from app.application.ports.services import SystemServicePort
from app.application.use_cases.base import UseCase, UseCaseResult


@dataclass
class RebootSystemInput:
    """Input for reboot system."""
    delay_seconds: int = 0
    force: bool = False


@dataclass
class RebootSystemOutput:
    """Output of reboot system."""
    scheduled: bool
    message: str


class RebootSystemUseCase(UseCase[RebootSystemOutput]):
    """Use case for rebooting the system."""

    def __init__(
        self,
        system_service: SystemServicePort,
        print_job_repository: PrintJobRepository,
    ):
        self._system = system_service
        self._print_job_repo = print_job_repository

    async def execute(self, input_data: RebootSystemInput) -> UseCaseResult[RebootSystemOutput]:
        try:
            # Check for active print jobs unless force is set
            if not input_data.force:
                active_jobs = await self._print_job_repo.get_active_jobs()
                if active_jobs:
                    return UseCaseResult.fail(
                        "ACTIVE_JOBS",
                        f"Cannot reboot with {len(active_jobs)} active print job(s)",
                    )

            # Schedule reboot
            success = await self._system.reboot_system(delay_seconds=input_data.delay_seconds)

            if success:
                if input_data.delay_seconds > 0:
                    return UseCaseResult.ok(
                        RebootSystemOutput(
                            scheduled=True,
                            message=f"Reboot scheduled in {input_data.delay_seconds} seconds",
                        )
                    )
                else:
                    return UseCaseResult.ok(
                        RebootSystemOutput(
                            scheduled=True,
                            message="System is rebooting now",
                        )
                    )
            else:
                return UseCaseResult.fail("REBOOT_FAILED", "Failed to schedule reboot")
        except Exception as e:
            return UseCaseResult.fail("REBOOT_ERROR", str(e))
