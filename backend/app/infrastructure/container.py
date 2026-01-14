"""Dependency Injection Container.

This module provides a simple DI container for managing service instances
and their dependencies following Clean Architecture principles.
"""

from dataclasses import dataclass
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.repositories import PrintJobRepository, SessionRepository
from app.application.ports.services import (
    ImageProcessorPort,
    PrinterPort,
    StoragePort,
    SystemServicePort,
)
from app.infrastructure.repositories import (
    SQLAlchemyPrintJobRepository,
    SQLAlchemySessionRepository,
)
from app.infrastructure.services.image_processor import ImageProcessor
from app.infrastructure.services.printer_service import PrinterService
from app.infrastructure.services.storage_service import StorageService
from app.infrastructure.services.system_service import SystemService


@dataclass
class Container:
    """Dependency injection container.

    Provides factory methods for creating properly configured instances
    of repositories, services, and use cases.
    """

    # Database session (request-scoped)
    _db: Optional[AsyncSession] = None

    # Service singletons
    _printer_service: Optional[PrinterPort] = None
    _storage_service: Optional[StoragePort] = None
    _image_processor: Optional[ImageProcessorPort] = None
    _system_service: Optional[SystemServicePort] = None

    def __init__(self, db: Optional[AsyncSession] = None):
        """Initialize container with optional database session."""
        self._db = db

    # ─────────────────────────────────────────────────────────────────
    # Repository factories (request-scoped, depend on db session)
    # ─────────────────────────────────────────────────────────────────

    def get_session_repository(self) -> SessionRepository:
        """Get session repository instance."""
        if self._db is None:
            raise RuntimeError("Database session not set")
        return SQLAlchemySessionRepository(self._db)

    def get_print_job_repository(self) -> PrintJobRepository:
        """Get print job repository instance."""
        if self._db is None:
            raise RuntimeError("Database session not set")
        return SQLAlchemyPrintJobRepository(self._db)

    # ─────────────────────────────────────────────────────────────────
    # Service factories (singletons)
    # ─────────────────────────────────────────────────────────────────

    def get_printer_service(self) -> PrinterPort:
        """Get printer service instance (singleton)."""
        if self._printer_service is None:
            self._printer_service = PrinterService()
        return self._printer_service

    def get_storage_service(self) -> StoragePort:
        """Get storage service instance (singleton)."""
        if self._storage_service is None:
            self._storage_service = StorageService()
        return self._storage_service

    def get_image_processor(self) -> ImageProcessorPort:
        """Get image processor instance (singleton)."""
        if self._image_processor is None:
            self._image_processor = ImageProcessor()
        return self._image_processor

    def get_system_service(self) -> SystemServicePort:
        """Get system service instance (singleton)."""
        if self._system_service is None:
            self._system_service = SystemService()
        return self._system_service


# Global container instance for singletons
_container = Container()


def get_container() -> Container:
    """Get the global container instance."""
    return _container


def create_request_container(db: AsyncSession) -> Container:
    """Create a request-scoped container with database session.

    This preserves singleton services while providing fresh
    repository instances for each request.
    """
    container = Container(db)
    # Share service singletons
    container._printer_service = _container._printer_service
    container._storage_service = _container._storage_service
    container._image_processor = _container._image_processor
    container._system_service = _container._system_service
    return container
