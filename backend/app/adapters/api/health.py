"""Health check API endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ...infrastructure.database import get_db
from ...infrastructure.services import PrinterService, StorageService

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    timestamp: str


class DetailedHealthResponse(BaseModel):
    """Detailed health check response."""

    success: bool
    data: dict


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Simple health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
    )


@router.get("/health/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    """Detailed health check with component status."""
    components = {}

    # Check database
    try:
        await db.execute("SELECT 1")
        components["database"] = {
            "status": "healthy",
            "latency_ms": 1,  # TODO: measure actual latency
        }
    except Exception as e:
        components["database"] = {
            "status": "unhealthy",
            "error": str(e),
        }

    # Check printer
    printer_service = PrinterService()
    printer_status = printer_service.get_printer_status()
    if printer_status:
        components["printer"] = {
            "status": "healthy",
            "name": printer_status.name,
            "state": printer_status.state.value,
            "mock_mode": printer_service.mock_mode,
        }
    else:
        components["printer"] = {
            "status": "unhealthy",
            "error": "Printer not found",
        }

    # Check storage
    storage_service = StorageService()
    storage_stats = storage_service.get_storage_stats()
    if storage_stats["percent_used"] < 90:
        components["storage"] = {
            "status": "healthy",
            "percent_used": storage_stats["percent_used"],
            "free_gb": round(storage_stats["free_bytes"] / (1024**3), 2),
        }
    else:
        components["storage"] = {
            "status": "warning",
            "percent_used": storage_stats["percent_used"],
            "message": "Storage space low",
        }

    # Overall status
    overall = "healthy"
    for component in components.values():
        if component["status"] == "unhealthy":
            overall = "unhealthy"
            break
        if component["status"] == "warning":
            overall = "degraded"

    return DetailedHealthResponse(
        success=True,
        data={
            "status": overall,
            "timestamp": datetime.now().isoformat(),
            "components": components,
        },
    )
