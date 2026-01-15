"""FastAPI dependency providers.

This module provides FastAPI `Depends` functions for injecting
repositories, services, and use cases into API endpoints.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.repositories import (PrintJobRepository,
                                                SessionRepository)
from app.application.ports.services import (ImageProcessorPort, PrinterPort,
                                            StoragePort, SystemServicePort)
from app.application.use_cases.admin import (AuthenticateUseCase,
                                             GetLogsUseCase,
                                             GetPrintHistoryUseCase,
                                             GetSystemStatusUseCase,
                                             RebootSystemUseCase,
                                             TestPrintUseCase)
from app.application.use_cases.print import (CancelPrintJobUseCase,
                                             GetPrintStatusUseCase,
                                             RetryPrintJobUseCase,
                                             SubmitPrintJobUseCase)
from app.application.use_cases.session import (AbandonSessionUseCase,
                                               CapturePhotoUseCase,
                                               CreateSessionUseCase,
                                               GenerateCompositeUseCase,
                                               GetSessionUseCase)
from app.application.use_cases.system import (CleanupStorageUseCase,
                                              HealthCheckUseCase)
from app.infrastructure.container import Container, create_request_container
from app.infrastructure.database import get_db

# ─────────────────────────────────────────────────────────────────
# Container dependency
# ─────────────────────────────────────────────────────────────────


async def get_container(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Container:
    """Get request-scoped container with database session."""
    return create_request_container(db)


ContainerDep = Annotated[Container, Depends(get_container)]


# ─────────────────────────────────────────────────────────────────
# Repository dependencies
# ─────────────────────────────────────────────────────────────────


async def get_session_repository(
    container: ContainerDep,
) -> SessionRepository:
    """Get session repository."""
    return container.get_session_repository()


async def get_print_job_repository(
    container: ContainerDep,
) -> PrintJobRepository:
    """Get print job repository."""
    return container.get_print_job_repository()


SessionRepositoryDep = Annotated[SessionRepository, Depends(get_session_repository)]
PrintJobRepositoryDep = Annotated[PrintJobRepository, Depends(get_print_job_repository)]


# ─────────────────────────────────────────────────────────────────
# Service dependencies
# ─────────────────────────────────────────────────────────────────


async def get_printer_service(container: ContainerDep) -> PrinterPort:
    """Get printer service."""
    return container.get_printer_service()


async def get_storage_service(container: ContainerDep) -> StoragePort:
    """Get storage service."""
    return container.get_storage_service()


async def get_image_processor(container: ContainerDep) -> ImageProcessorPort:
    """Get image processor."""
    return container.get_image_processor()


async def get_system_service(container: ContainerDep) -> SystemServicePort:
    """Get system service."""
    return container.get_system_service()


PrinterServiceDep = Annotated[PrinterPort, Depends(get_printer_service)]
StorageServiceDep = Annotated[StoragePort, Depends(get_storage_service)]
ImageProcessorDep = Annotated[ImageProcessorPort, Depends(get_image_processor)]
SystemServiceDep = Annotated[SystemServicePort, Depends(get_system_service)]


# ─────────────────────────────────────────────────────────────────
# Session use case dependencies
# ─────────────────────────────────────────────────────────────────


async def get_create_session_use_case(
    session_repo: SessionRepositoryDep,
) -> CreateSessionUseCase:
    """Get CreateSession use case."""
    return CreateSessionUseCase(session_repository=session_repo)


async def get_get_session_use_case(
    session_repo: SessionRepositoryDep,
) -> GetSessionUseCase:
    """Get GetSession use case."""
    return GetSessionUseCase(session_repository=session_repo)


async def get_capture_photo_use_case(
    session_repo: SessionRepositoryDep,
    storage: StorageServiceDep,
    image_processor: ImageProcessorDep,
) -> CapturePhotoUseCase:
    """Get CapturePhoto use case."""
    return CapturePhotoUseCase(
        session_repository=session_repo,
        storage=storage,
        image_processor=image_processor,
    )


async def get_generate_composite_use_case(
    session_repo: SessionRepositoryDep,
    storage: StorageServiceDep,
) -> GenerateCompositeUseCase:
    """Get GenerateComposite use case."""
    return GenerateCompositeUseCase(
        session_repository=session_repo,
        storage=storage,
    )


async def get_abandon_session_use_case(
    session_repo: SessionRepositoryDep,
    storage: StorageServiceDep,
) -> AbandonSessionUseCase:
    """Get AbandonSession use case."""
    return AbandonSessionUseCase(
        session_repository=session_repo,
        storage=storage,
    )


CreateSessionUseCaseDep = Annotated[CreateSessionUseCase, Depends(get_create_session_use_case)]
GetSessionUseCaseDep = Annotated[GetSessionUseCase, Depends(get_get_session_use_case)]
CapturePhotoUseCaseDep = Annotated[CapturePhotoUseCase, Depends(get_capture_photo_use_case)]
GenerateCompositeUseCaseDep = Annotated[
    GenerateCompositeUseCase, Depends(get_generate_composite_use_case)
]
AbandonSessionUseCaseDep = Annotated[AbandonSessionUseCase, Depends(get_abandon_session_use_case)]


# ─────────────────────────────────────────────────────────────────
# Print use case dependencies
# ─────────────────────────────────────────────────────────────────


async def get_submit_print_job_use_case(
    session_repo: SessionRepositoryDep,
    job_repo: PrintJobRepositoryDep,
    printer: PrinterServiceDep,
) -> SubmitPrintJobUseCase:
    """Get SubmitPrintJob use case."""
    return SubmitPrintJobUseCase(
        session_repository=session_repo,
        print_job_repository=job_repo,
        printer=printer,
    )


async def get_get_print_status_use_case(
    job_repo: PrintJobRepositoryDep,
    printer: PrinterServiceDep,
) -> GetPrintStatusUseCase:
    """Get GetPrintStatus use case."""
    return GetPrintStatusUseCase(
        print_job_repository=job_repo,
        printer=printer,
    )


async def get_retry_print_job_use_case(
    job_repo: PrintJobRepositoryDep,
    printer: PrinterServiceDep,
) -> RetryPrintJobUseCase:
    """Get RetryPrintJob use case."""
    return RetryPrintJobUseCase(
        print_job_repository=job_repo,
        printer=printer,
    )


async def get_cancel_print_job_use_case(
    job_repo: PrintJobRepositoryDep,
    printer: PrinterServiceDep,
) -> CancelPrintJobUseCase:
    """Get CancelPrintJob use case."""
    return CancelPrintJobUseCase(
        print_job_repository=job_repo,
        printer=printer,
    )


SubmitPrintJobUseCaseDep = Annotated[SubmitPrintJobUseCase, Depends(get_submit_print_job_use_case)]
GetPrintStatusUseCaseDep = Annotated[GetPrintStatusUseCase, Depends(get_get_print_status_use_case)]
RetryPrintJobUseCaseDep = Annotated[RetryPrintJobUseCase, Depends(get_retry_print_job_use_case)]
CancelPrintJobUseCaseDep = Annotated[CancelPrintJobUseCase, Depends(get_cancel_print_job_use_case)]


# ─────────────────────────────────────────────────────────────────
# Admin use case dependencies
# ─────────────────────────────────────────────────────────────────


async def get_authenticate_use_case() -> AuthenticateUseCase:
    """Get Authenticate use case."""
    import hashlib

    from app.config import get_settings

    settings = get_settings()
    pin_hash = hashlib.sha256(settings.admin_pin.encode()).hexdigest()
    return AuthenticateUseCase(
        admin_pin_hash=pin_hash,
        token_expiry_hours=max(1, settings.token_expire_minutes // 60),
    )


async def get_system_status_use_case(
    system: SystemServiceDep,
    storage: StorageServiceDep,
    printer: PrinterServiceDep,
    job_repo: PrintJobRepositoryDep,
) -> GetSystemStatusUseCase:
    """Get GetSystemStatus use case."""
    return GetSystemStatusUseCase(
        system_service=system,
        storage=storage,
        printer=printer,
        print_job_repository=job_repo,
    )


async def get_print_history_use_case(
    job_repo: PrintJobRepositoryDep,
) -> GetPrintHistoryUseCase:
    """Get GetPrintHistory use case."""
    return GetPrintHistoryUseCase(print_job_repository=job_repo)


async def get_logs_use_case(
    system: SystemServiceDep,
) -> GetLogsUseCase:
    """Get GetLogs use case."""
    return GetLogsUseCase(system_service=system)


async def get_test_print_use_case(
    image_processor: ImageProcessorDep,
    printer: PrinterServiceDep,
) -> TestPrintUseCase:
    """Get TestPrint use case."""
    return TestPrintUseCase(
        image_processor=image_processor,
        printer=printer,
    )


async def get_reboot_system_use_case(
    system: SystemServiceDep,
    job_repo: PrintJobRepositoryDep,
) -> RebootSystemUseCase:
    """Get RebootSystem use case."""
    return RebootSystemUseCase(
        system_service=system,
        print_job_repository=job_repo,
    )


AuthenticateUseCaseDep = Annotated[AuthenticateUseCase, Depends(get_authenticate_use_case)]
GetSystemStatusUseCaseDep = Annotated[GetSystemStatusUseCase, Depends(get_system_status_use_case)]
GetPrintHistoryUseCaseDep = Annotated[GetPrintHistoryUseCase, Depends(get_print_history_use_case)]
GetLogsUseCaseDep = Annotated[GetLogsUseCase, Depends(get_logs_use_case)]
TestPrintUseCaseDep = Annotated[TestPrintUseCase, Depends(get_test_print_use_case)]
RebootSystemUseCaseDep = Annotated[RebootSystemUseCase, Depends(get_reboot_system_use_case)]


# ─────────────────────────────────────────────────────────────────
# System use case dependencies
# ─────────────────────────────────────────────────────────────────


async def get_cleanup_storage_use_case(
    storage: StorageServiceDep,
) -> CleanupStorageUseCase:
    """Get CleanupStorage use case."""
    return CleanupStorageUseCase(storage=storage)


async def get_health_check_use_case(
    system: SystemServiceDep,
    storage: StorageServiceDep,
    printer: PrinterServiceDep,
) -> HealthCheckUseCase:
    """Get HealthCheck use case."""
    return HealthCheckUseCase(
        system_service=system,
        storage=storage,
        printer=printer,
    )


CleanupStorageUseCaseDep = Annotated[CleanupStorageUseCase, Depends(get_cleanup_storage_use_case)]
HealthCheckUseCaseDep = Annotated[HealthCheckUseCase, Depends(get_health_check_use_case)]
