"""Print job API endpoints."""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain import ErrorCode, PrintStatus, SessionId
from ...domain.entities import PrintJob
from ...infrastructure.database import (
    JobEventModel,
    PrintJobModel,
    SessionModel,
    get_db,
)
from ...infrastructure.services import PrinterService

router = APIRouter()
logger = logging.getLogger(__name__)


# Request/Response models
class PrintJobRequest(BaseModel):
    """Request to create a print job."""

    session_id: str
    copies: int = 1


class PrintJobResponse(BaseModel):
    """Print job response model."""

    success: bool
    data: dict


class ErrorResponse(BaseModel):
    """Error response model."""

    success: bool = False
    error: dict


# Endpoints
@router.post("/print", response_model=PrintJobResponse, status_code=201)
async def create_print_job(
    request: PrintJobRequest,
    db: AsyncSession = Depends(get_db),
):
    """Submit a print job."""
    # Validate copies
    if not 1 <= request.copies <= 3:
        raise HTTPException(status_code=400, detail="Copies must be between 1 and 3")

    # Get session
    result = await db.execute(
        select(SessionModel).where(SessionModel.id == request.session_id)
    )
    db_session = result.scalar_one_or_none()

    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not db_session.composite_path:
        raise HTTPException(status_code=400, detail="Session has no composite image")

    # Check printer availability
    printer_service = PrinterService()
    if not printer_service.is_available():
        raise HTTPException(status_code=503, detail="Printer is offline")

    # Create print job
    job = PrintJob.create(
        session_id=SessionId.from_string(request.session_id),
        copies=request.copies,
    )

    # Save to database
    db_job = PrintJobModel(
        id=str(job.id),
        session_id=request.session_id,
        status=job.status.value,
        copies=job.copies,
        created_at=job.created_at,
    )
    db.add(db_job)

    # Add event
    db_event = JobEventModel(
        job_id=str(job.id),
        event_type="CREATED",
        message="Print job created",
    )
    db.add(db_event)

    await db.commit()

    # Start print processing (in background ideally)
    # For now, we'll process synchronously
    await _process_print_job(str(job.id), db)

    logger.info(f"Created print job: {job.id}")

    return PrintJobResponse(
        success=True,
        data={
            "job_id": str(job.id),
            "session_id": request.session_id,
            "status": job.status.value,
            "copies": job.copies,
            "created_at": job.created_at.isoformat(),
        },
    )


@router.get("/print/{job_id}", response_model=PrintJobResponse)
async def get_print_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get print job status."""
    result = await db.execute(select(PrintJobModel).where(PrintJobModel.id == job_id))
    db_job = result.scalar_one_or_none()

    if not db_job:
        raise HTTPException(status_code=404, detail="Print job not found")

    # Calculate progress
    progress_map = {
        "pending": 0,
        "processing": 25,
        "printing": 75,
        "completed": 100,
        "retry_pending": 50,
        "failed": 0,
        "cancelled": 0,
    }
    progress = progress_map.get(db_job.status, 0)

    return PrintJobResponse(
        success=True,
        data={
            "job_id": db_job.id,
            "session_id": db_job.session_id,
            "status": db_job.status,
            "copies": db_job.copies,
            "progress": progress,
            "created_at": db_job.created_at.isoformat(),
            "started_at": db_job.started_at.isoformat() if db_job.started_at else None,
            "completed_at": (
                db_job.completed_at.isoformat() if db_job.completed_at else None
            ),
            "error": (
                {
                    "code": db_job.error_code,
                    "message": db_job.error_message,
                }
                if db_job.error_code
                else None
            ),
            "retry_count": db_job.retry_count,
        },
    )


@router.post("/print/{job_id}/retry", response_model=PrintJobResponse)
async def retry_print_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Manually retry a failed print job."""
    result = await db.execute(select(PrintJobModel).where(PrintJobModel.id == job_id))
    db_job = result.scalar_one_or_none()

    if not db_job:
        raise HTTPException(status_code=404, detail="Print job not found")

    if db_job.status != PrintStatus.FAILED.value:
        raise HTTPException(
            status_code=409,
            detail=f"Can only retry failed jobs, current status: {db_job.status}",
        )

    # Reset job for retry
    db_job.status = PrintStatus.PENDING.value
    db_job.retry_count = 0
    db_job.error_code = None
    db_job.error_message = None
    db_job.next_retry_at = None

    # Add event
    db_event = JobEventModel(
        job_id=job_id,
        event_type="RETRY_USER",
        message="User initiated retry",
    )
    db.add(db_event)

    await db.commit()

    # Process job
    await _process_print_job(job_id, db)

    logger.info(f"User retry for job: {job_id}")

    return PrintJobResponse(
        success=True,
        data={
            "job_id": db_job.id,
            "status": db_job.status,
            "retry_count": db_job.retry_count,
            "message": "Job queued for retry",
        },
    )


@router.post("/print/{job_id}/cancel", response_model=PrintJobResponse)
async def cancel_print_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Cancel a print job."""
    result = await db.execute(select(PrintJobModel).where(PrintJobModel.id == job_id))
    db_job = result.scalar_one_or_none()

    if not db_job:
        raise HTTPException(status_code=404, detail="Print job not found")

    if db_job.status in (PrintStatus.COMPLETED.value, PrintStatus.CANCELLED.value):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot cancel job in {db_job.status} state",
        )

    previous_status = db_job.status

    # Cancel CUPS job if exists
    if db_job.cups_job_id:
        printer_service = PrinterService()
        await printer_service.cancel_job(db_job.cups_job_id)

    # Update status
    db_job.status = PrintStatus.CANCELLED.value
    db_job.cancelled_at = datetime.now()

    # Add event
    db_event = JobEventModel(
        job_id=job_id,
        event_type="CANCELLED",
        message="Job cancelled by user",
    )
    db.add(db_event)

    await db.commit()

    logger.info(f"Cancelled job: {job_id}")

    return PrintJobResponse(
        success=True,
        data={
            "job_id": db_job.id,
            "status": db_job.status,
            "previous_status": previous_status,
        },
    )


@router.get("/settings/public")
async def get_public_settings(db: AsyncSession = Depends(get_db)):
    """Get public settings for UI."""
    import json

    from ...infrastructure.database import SettingsModel

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


# Internal helpers
async def _process_print_job(job_id: str, db: AsyncSession):
    """Process a print job."""
    result = await db.execute(select(PrintJobModel).where(PrintJobModel.id == job_id))
    db_job = result.scalar_one_or_none()

    if not db_job:
        return

    # Get session for composite path
    result = await db.execute(
        select(SessionModel).where(SessionModel.id == db_job.session_id)
    )
    db_session = result.scalar_one_or_none()

    if not db_session or not db_session.composite_path:
        db_job.status = PrintStatus.FAILED.value
        db_job.error_code = ErrorCode.PROCESSING_ERROR.value
        db_job.error_message = "No composite image found"
        await db.commit()
        return

    # Update status to processing
    db_job.status = PrintStatus.PROCESSING.value
    db_job.started_at = datetime.now()
    await db.commit()

    # Submit to printer
    printer_service = PrinterService()
    print_result = await printer_service.print_file(
        db_session.composite_path,
        db_job.copies,
    )

    if print_result.success:
        db_job.status = PrintStatus.PRINTING.value
        db_job.cups_job_id = print_result.job_id

        # Add event
        db_event = JobEventModel(
            job_id=job_id,
            event_type="SUBMITTED",
            message=f"Submitted to CUPS as job {print_result.job_id}",
        )
        db.add(db_event)

        # Check job status (simplified - in production would poll)
        job_status = await printer_service.get_job_status(print_result.job_id)

        if job_status and job_status.get("completed"):
            db_job.status = PrintStatus.COMPLETED.value
            db_job.completed_at = datetime.now()

            db_event = JobEventModel(
                job_id=job_id,
                event_type="COMPLETED",
                message="Print completed successfully",
            )
            db.add(db_event)

            # Update session status
            db_session.status = "printed"
    else:
        # Handle error
        db_job.error_code = (
            print_result.error_code.value if print_result.error_code else "unknown"
        )
        db_job.error_message = print_result.error_message

        # Check if retryable
        if print_result.error_code and print_result.error_code.is_retryable:
            if db_job.retry_count < 3:
                db_job.status = PrintStatus.RETRY_PENDING.value
                db_job.retry_count += 1

                db_event = JobEventModel(
                    job_id=job_id,
                    event_type="RETRY_SCHEDULED",
                    message=f"Retry {db_job.retry_count}/3 scheduled",
                )
                db.add(db_event)
            else:
                db_job.status = PrintStatus.FAILED.value
        else:
            db_job.status = PrintStatus.FAILED.value

    await db.commit()
