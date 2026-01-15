"""Health check API endpoints."""

from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel

from app.adapters.api.response_utils import handle_result
from app.infrastructure.dependencies import HealthCheckUseCaseDep

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
async def detailed_health_check(
    use_case: HealthCheckUseCaseDep,
):
    """Detailed health check with component status."""
    result = await use_case.execute()

    # Transform the use case output to match expected API response format
    def transform(data):
        return {
            "status": data.status,
            "timestamp": datetime.now().isoformat(),
            "components": data.details,
        }

    return handle_result(result, transform=transform)
