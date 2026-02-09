"""Print job API endpoints."""

import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.api.response_utils import handle_result
from app.application.use_cases.print import SubmitPrintJobInput
from app.infrastructure.database import SettingsModel, get_db
from app.infrastructure.dependencies import (CancelPrintJobUseCaseDep,
                                             GetPrintStatusUseCaseDep,
                                             PrinterServiceDep,
                                             RetryPrintJobUseCaseDep,
                                             SubmitPrintJobUseCaseDep)

router = APIRouter()
logger = logging.getLogger(__name__)


# Request/Response models
class PrintJobRequest(BaseModel):
    """Request to create a print job."""

    session_id: str
    copies: int = 1
    printer_name: Optional[str] = None


class PrintJobResponse(BaseModel):
    """Print job response model."""

    success: bool
    data: dict


class ErrorResponse(BaseModel):
    """Error response model."""

    success: bool = False
    error: dict


@router.post("/print", response_model=PrintJobResponse, status_code=201)
async def create_print_job(
    request: PrintJobRequest,
    use_case: SubmitPrintJobUseCaseDep,
):
    """Submit a print job."""
    result = await use_case.execute(
        SubmitPrintJobInput(
            session_id=request.session_id,
            copies=request.copies,
            printer_name=request.printer_name,
        )
    )

    def transform(data):
        return {
            "job_id": data.id,
            "session_id": data.session_id,
            "status": data.status,
            "copies": data.copies,
            "printer_name": data.printer_name,
            "created_at": data.created_at.isoformat() if data.created_at else None,
        }

    return handle_result(result, transform=transform)


@router.get("/printers")
async def list_printers(
    printer: PrinterServiceDep,
):
    """List all configured printers with their current status.

    Printers are automatically discovered from CUPS if auto-discovery is enabled.
    """
    statuses = await printer.get_all_printer_statuses()
    return {
        "success": True,
        "data": {
            "printers": [
                {
                    "name": s.name,
                    "status": s.status,
                    "connected": s.connected,
                    "is_ready": s.is_ready,
                    "paper_status": s.paper_status,
                    "ink_status": s.ink_status,
                    "queue_length": s.queue_length,
                    "error_message": s.error_message,
                }
                for s in statuses
            ],
            "count": len(statuses),
        },
    }


@router.post("/printers/refresh")
async def refresh_printers(
    printer: PrinterServiceDep,
    auto_troubleshoot: bool = False,
):
    """Refresh the list of discovered printers from CUPS.

    Args:
        auto_troubleshoot: If True and no printers found, attempt auto-troubleshooting

    Useful after connecting or disconnecting printers.
    """
    # Refresh printer list from CUPS (with optional auto-troubleshooting)
    new_list = printer.refresh_printers(auto_troubleshoot=auto_troubleshoot)

    # Get updated statuses
    statuses = await printer.get_all_printer_statuses()

    return {
        "success": True,
        "data": {
            "printers": [
                {
                    "name": s.name,
                    "status": s.status,
                    "connected": s.connected,
                    "is_ready": s.is_ready,
                    "paper_status": s.paper_status,
                    "ink_status": s.ink_status,
                    "queue_length": s.queue_length,
                    "error_message": s.error_message,
                }
                for s in statuses
            ],
            "count": len(statuses),
            "refreshed": True,
            "auto_troubleshoot_attempted": auto_troubleshoot and len(statuses) == 0,
        },
    }


@router.post("/printers/troubleshoot")
async def troubleshoot_printers(
    printer: PrinterServiceDep,
):
    """Manually trigger printer troubleshooting.

    This will:
    1. Stop ipp-usb if running
    2. Load usblp module
    3. Rebind USB devices
    4. Auto-register any detected printers
    5. Refresh the printer list
    """
    # Trigger auto-troubleshooting
    printer._auto_troubleshoot()

    # Refresh and get updated list
    printer.refresh_printers()
    statuses = await printer.get_all_printer_statuses()

    return {
        "success": True,
        "data": {
            "message": "Troubleshooting completed",
            "printers": [
                {
                    "name": s.name,
                    "status": s.status,
                    "connected": s.connected,
                    "is_ready": s.is_ready,
                }
                for s in statuses
            ],
            "count": len(statuses),
        },
    }


@router.get("/print/{job_id}", response_model=PrintJobResponse)
async def get_print_job(
    job_id: str,
    use_case: GetPrintStatusUseCaseDep,
):
    """Get print job status."""
    result = await use_case.execute(job_id)

    def transform(data):
        return {
            "job_id": data.job_id,
            "status": data.status,
            "progress": data.progress,
            "error": (
                {"code": data.error_code, "message": data.error_message}
                if data.error_code
                else None
            ),
        }

    return handle_result(result, transform=transform)


@router.post("/print/{job_id}/retry", response_model=PrintJobResponse)
async def retry_print_job(
    job_id: str,
    use_case: RetryPrintJobUseCaseDep,
):
    """Manually retry a failed print job."""
    result = await use_case.execute(job_id)

    def transform(data):
        return {
            "job_id": data.job_id,
            "status": data.status,
            "message": "Job queued for retry",
        }

    return handle_result(result, transform=transform)


@router.post("/print/{job_id}/cancel", response_model=PrintJobResponse)
async def cancel_print_job(
    job_id: str,
    use_case: CancelPrintJobUseCaseDep,
):
    """Cancel a print job."""
    result = await use_case.execute(job_id)

    def transform(data):
        return {
            "job_id": job_id,
            "status": "cancelled",
            "cancelled": data,
        }

    return handle_result(result, transform=transform)


@router.get("/settings/public")
async def get_public_settings(db: AsyncSession = Depends(get_db)):
    """Get public settings for UI."""
    settings_keys = [
        "display.default_language",
        "display.countdown_options",
        "display.default_countdown",
        "display.sound_enabled",
        "print.max_copies",
        "print.logo_enabled",
        "print.date_format",
    ]

    result = await db.execute(
        select(SettingsModel).where(SettingsModel.key.in_(settings_keys))
    )
    settings = {s.key: json.loads(s.value) for s in result.scalars()}

    return {
        "success": True,
        "data": {
            "default_language": settings.get("display.default_language", "ko"),
            "countdown_options": settings.get(
                "display.countdown_options", [3, 5, 8, 10]
            ),
            "default_countdown": settings.get("display.default_countdown", 5),
            "sound_enabled": settings.get("display.sound_enabled", True),
            "max_copies": settings.get("print.max_copies", 3),
            "logo_enabled": settings.get("print.logo_enabled", True),
            "date_format": settings.get("print.date_format", "YYYY.MM.DD"),
        },
    }
