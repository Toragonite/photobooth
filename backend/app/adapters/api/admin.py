"""Admin API endpoints."""

import hashlib
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.api.response_utils import handle_result
from app.application.use_cases.admin import (GetLogsInput,
                                             GetPrintHistoryInput,
                                             RebootSystemInput, TestPrintInput)
from app.config import get_settings
from app.infrastructure.database import (AdminSessionModel, JobEventModel,
                                         LoginAttemptModel, PrintJobModel,
                                         SessionModel, SettingsModel, get_db)
from app.infrastructure.dependencies import (GetLogsUseCaseDep,
                                             GetPrintHistoryUseCaseDep,
                                             GetSystemStatusUseCaseDep,
                                             RebootSystemUseCaseDep,
                                             TestPrintUseCaseDep)
from app.infrastructure.services import (CleanupService, ExportType, LogLevel,
                                         LogSource, LogViewerService,
                                         PhotoExportService, ServiceName,
                                         StorageService, SystemService,
                                         TestPatternType)

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()


# Request/Response models
class LoginRequest(BaseModel):
    """Admin login request."""

    pin: str


class LoginResponse(BaseModel):
    """Admin login response."""

    success: bool
    data: Optional[dict] = None
    error: Optional[dict] = None


class AdminResponse(BaseModel):
    """Generic admin response."""

    success: bool
    data: dict


class TestPrintRequest(BaseModel):
    """Request to send test print."""

    pattern: Optional[str] = None
    pattern_type: Optional[str] = None  # Alias for backward compat
    printer_name: Optional[str] = None


class RebootSystemRequest(BaseModel):
    """Request to reboot system."""

    delay: int = 10
    force: bool = False


class CleanupRequest(BaseModel):
    """Request to execute cleanup."""

    older_than_days: int = 30
    dry_run: bool = False  # Reserved for future use


# Auth dependency
async def get_admin_user(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Verify admin token."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid auth scheme")

        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])

        # Check if token is revoked
        token_hash = hashlib.sha256(token.encode()).hexdigest()[:64]
        result = await db.execute(
            select(AdminSessionModel).where(AdminSessionModel.token == token_hash)
        )
        db_session = result.scalar_one_or_none()

        if db_session and db_session.revoked:
            raise HTTPException(status_code=401, detail="Token revoked")

        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")


# Endpoints
@router.post("/login", response_model=LoginResponse)
async def admin_login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate admin."""
    # Check rate limiting
    one_hour_ago = datetime.now() - timedelta(hours=1)
    result = await db.execute(
        select(func.count(LoginAttemptModel.id)).where(
            and_(
                LoginAttemptModel.attempted_at > one_hour_ago,
                LoginAttemptModel.success == 0,
            )
        )
    )
    failed_attempts = result.scalar() or 0

    if failed_attempts >= 10:
        raise HTTPException(status_code=429, detail="Too many failed attempts")

    # Record attempt
    attempt = LoginAttemptModel(ip_address="local")
    db.add(attempt)

    # Verify PIN
    if request.pin != settings.admin_pin:
        await db.commit()
        return LoginResponse(
            success=False,
            error={"code": "AUTH_FAILED", "message": "Invalid PIN"},
        )

    # Mark success
    attempt.success = 1

    # Generate token (use UTC for consistency across timezones)
    now_utc = datetime.now(timezone.utc)
    expires_at = now_utc + timedelta(minutes=settings.token_expire_minutes)
    payload = {
        "sub": "admin",
        "exp": expires_at,
        "iat": now_utc,
    }
    token = jwt.encode(payload, settings.secret_key, algorithm="HS256")

    # Store session with hashed token
    token_hash = hashlib.sha256(token.encode()).hexdigest()[:64]
    admin_session = AdminSessionModel(
        token=token_hash,
        expires_at=expires_at,
    )
    db.add(admin_session)
    await db.commit()

    logger.info("Admin logged in")

    return LoginResponse(
        success=True,
        data={
            "token": token,
            "expires_at": expires_at.isoformat(),
        },
    )


@router.post("/logout")
async def admin_logout(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Invalidate admin token."""
    if authorization:
        try:
            _, token = authorization.split()
            token_hash = hashlib.sha256(token.encode()).hexdigest()[:64]
            result = await db.execute(
                select(AdminSessionModel).where(AdminSessionModel.token == token_hash)
            )
            db_session = result.scalar_one_or_none()
            if db_session:
                db_session.revoked = 1
                await db.commit()
        except Exception:
            pass

    return {"success": True}


@router.get("/status", response_model=AdminResponse)
async def get_system_status(
    use_case: GetSystemStatusUseCaseDep,
    admin: dict = Depends(get_admin_user),
):
    """Get full system status."""
    result = await use_case.execute()
    return handle_result(result)


@router.get("/print-history", response_model=AdminResponse)
async def get_print_history(
    use_case: GetPrintHistoryUseCaseDep,
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,
    admin: dict = Depends(get_admin_user),
):
    """Get paginated print history."""
    input_data = GetPrintHistoryInput(
        page=page,
        per_page=min(limit, 100),
        status_filter=status if status != "all" else None,
    )
    result = await use_case.execute(input_data)
    return handle_result(result)


@router.get("/print-history/{job_id}", response_model=AdminResponse)
async def get_print_job_detail(
    job_id: str,
    admin: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed job info with timeline."""
    result = await db.execute(select(PrintJobModel).where(PrintJobModel.id == job_id))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Get events
    result = await db.execute(
        select(JobEventModel)
        .where(JobEventModel.job_id == job_id)
        .order_by(JobEventModel.created_at.asc())
    )
    events = result.scalars().all()

    timeline = [
        {
            "timestamp": event.created_at.isoformat(),
            "event": event.event_type,
            "message": event.message,
        }
        for event in events
    ]

    return AdminResponse(
        success=True,
        data={
            "job": {
                "id": job.id,
                "session_id": job.session_id,
                "status": job.status,
                "copies": job.copies,
                "created_at": job.created_at.isoformat(),
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": (
                    job.completed_at.isoformat() if job.completed_at else None
                ),
                "error_code": job.error_code,
                "error_message": job.error_message,
                "retry_count": job.retry_count,
                "cups_job_id": job.cups_job_id,
            },
            "timeline": timeline,
        },
    )


@router.get("/settings", response_model=AdminResponse)
async def get_all_settings(
    admin: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all settings."""
    result = await db.execute(select(SettingsModel))
    settings_rows = result.scalars().all()

    # Group settings by category
    settings_data = {"display": {}, "print": {}, "system": {}, "network": {}}

    for setting in settings_rows:
        parts = setting.key.split(".", 1)
        if len(parts) == 2:
            category, key = parts
            if category in settings_data:
                settings_data[category][key] = json.loads(setting.value)

    # Mask sensitive values
    if "admin_pin_hash" in settings_data.get("system", {}):
        settings_data["system"]["admin_pin"] = "****"
        del settings_data["system"]["admin_pin_hash"]

    if "password_hash" in settings_data.get("network", {}):
        settings_data["network"]["password"] = "********"
        del settings_data["network"]["password_hash"]

    return AdminResponse(success=True, data=settings_data)


@router.patch("/settings", response_model=AdminResponse)
async def update_settings(
    updates: dict,
    admin: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Update settings."""
    updated_fields = []

    for category, values in updates.items():
        if not isinstance(values, dict):
            continue

        for key, value in values.items():
            full_key = f"{category}.{key}"

            result = await db.execute(
                select(SettingsModel).where(SettingsModel.key == full_key)
            )
            setting = result.scalar_one_or_none()

            if setting:
                setting.value = json.dumps(value)
                setting.updated_at = datetime.now()
                updated_fields.append(full_key)
            else:
                new_setting = SettingsModel(
                    key=full_key,
                    value=json.dumps(value),
                )
                db.add(new_setting)
                updated_fields.append(full_key)

    await db.commit()

    logger.info(f"Updated settings: {updated_fields}")

    return AdminResponse(
        success=True,
        data={
            "updated_fields": updated_fields,
            "restart_required": False,
        },
    )


@router.get("/storage", response_model=AdminResponse)
async def get_storage_details(
    admin: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Get storage details."""
    storage_service = StorageService()
    stats = storage_service.get_storage_stats()

    # Get session count
    result = await db.execute(select(func.count(SessionModel.id)))
    session_count = result.scalar() or 0

    return AdminResponse(
        success=True,
        data={
            **stats,
            "session_count": session_count,
        },
    )


@router.post("/test-print", response_model=AdminResponse)
async def test_print(
    use_case: TestPrintUseCaseDep,
    request: Optional[TestPrintRequest] = None,
    admin: dict = Depends(get_admin_user),
):
    """Send test print with specified pattern.

    Args:
        request: JSON body with pattern or pattern_type field
    """
    # Handle request body - prefer 'pattern' over 'pattern_type'
    pattern = "full"
    printer_name = None
    if request:
        pattern = request.pattern or request.pattern_type or "full"
        printer_name = request.printer_name

    input_data = TestPrintInput(pattern_type=pattern, printer_name=printer_name)
    result = await use_case.execute(input_data)
    return handle_result(result)


@router.get("/test-print/patterns", response_model=AdminResponse)
async def get_test_patterns(
    admin: dict = Depends(get_admin_user),
):
    """Get available test pattern types."""
    patterns = [
        {
            "id": TestPatternType.COLOR_BARS.value,
            "name": "Color Bars",
            "description": "SMPTE-style color bars for color accuracy testing",
        },
        {
            "id": TestPatternType.ALIGNMENT.value,
            "name": "Alignment Grid",
            "description": "Grid pattern with crosshairs for alignment testing",
        },
        {
            "id": TestPatternType.GRADIENT.value,
            "name": "Gradient",
            "description": "Grayscale and RGB gradients for tone reproduction",
        },
        {
            "id": TestPatternType.FULL.value,
            "name": "Full Test",
            "description": "Complete test pattern with all elements",
        },
    ]

    return AdminResponse(
        success=True,
        data={"patterns": patterns},
    )


@router.get("/logs", response_model=AdminResponse)
async def get_logs(
    use_case: GetLogsUseCaseDep,
    source: str = "app",
    level: str = "all",
    limit: Optional[int] = None,
    lines: Optional[int] = None,
    admin: dict = Depends(get_admin_user),
):
    """Get system logs.

    Args:
        source: Log source (app, print, cups, system)
        level: Minimum log level (debug, info, warning, error, critical, all)
        limit: Number of lines to return (primary param)
        lines: Number of lines to return (alias for backward compat)
    """
    # Use limit as primary, fall back to lines, then default to 100
    line_count = limit if limit is not None else (lines if lines is not None else 100)

    input_data = GetLogsInput(
        source=source,
        limit=min(line_count, 1000),
        level=level if level != "all" else None,
    )
    result = await use_case.execute(input_data)
    return handle_result(result)


@router.get("/logs/sources", response_model=AdminResponse)
async def get_log_sources(
    admin: dict = Depends(get_admin_user),
):
    """Get available log sources."""
    sources = [
        {
            "id": LogSource.APP.value,
            "name": "Application",
            "description": "Main application logs",
        },
        {
            "id": LogSource.PRINT.value,
            "name": "Print Service",
            "description": "Print-related logs",
        },
        {
            "id": LogSource.CUPS.value,
            "name": "CUPS",
            "description": "CUPS printer daemon logs",
        },
        {
            "id": LogSource.SYSTEM.value,
            "name": "System",
            "description": "System service logs",
        },
    ]

    levels = [
        {"id": LogLevel.ALL.value, "name": "All"},
        {"id": LogLevel.DEBUG.value, "name": "Debug"},
        {"id": LogLevel.INFO.value, "name": "Info"},
        {"id": LogLevel.WARNING.value, "name": "Warning"},
        {"id": LogLevel.ERROR.value, "name": "Error"},
        {"id": LogLevel.CRITICAL.value, "name": "Critical"},
    ]

    return AdminResponse(
        success=True,
        data={
            "sources": sources,
            "levels": levels,
        },
    )


@router.get("/logs/download")
async def download_logs(
    source: str = "app",
    hours: int = 24,
    admin: dict = Depends(get_admin_user),
):
    """Download logs as a file.

    Args:
        source: Log source (app, print, cups, system)
        hours: Number of hours of logs to include
    """
    from fastapi.responses import Response

    log_viewer = LogViewerService()

    # Validate source
    try:
        log_source = LogSource(source)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid log source. Must be one of: {[s.value for s in LogSource]}",
        )

    content = log_viewer.download_logs(source=log_source, hours=hours)
    filename = (
        f"photobooth_{source}_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    )

    return Response(
        content=content,
        media_type="text/plain",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.post("/system/reboot", response_model=AdminResponse)
async def reboot_system(
    use_case: RebootSystemUseCaseDep,
    request: Optional[RebootSystemRequest] = None,
    admin: dict = Depends(get_admin_user),
):
    """Schedule system reboot.

    Args:
        request: JSON body with delay and force fields
    """
    delay = request.delay if request else 10
    force = request.force if request else False

    input_data = RebootSystemInput(delay_seconds=delay, force=force)
    result = await use_case.execute(input_data)
    return handle_result(result)


@router.post("/system/reboot/cancel", response_model=AdminResponse)
async def cancel_reboot(
    admin: dict = Depends(get_admin_user),
):
    """Cancel a scheduled reboot."""
    system_service = SystemService()

    result = await system_service.cancel_reboot()

    return AdminResponse(
        success=result["success"],
        data=result,
    )


@router.get("/system/reboot/status", response_model=AdminResponse)
async def get_reboot_status(
    admin: dict = Depends(get_admin_user),
):
    """Get current reboot status."""
    system_service = SystemService()

    status = system_service.get_reboot_status()

    return AdminResponse(
        success=True,
        data={
            "scheduled": status.scheduled,
            "scheduled_at": (
                status.scheduled_at.isoformat() if status.scheduled_at else None
            ),
            "delay_seconds": status.delay_seconds,
            "can_cancel": status.can_cancel,
        },
    )


@router.post("/system/shutdown", response_model=AdminResponse)
async def shutdown_system(
    delay: int = 10,
    admin: dict = Depends(get_admin_user),
):
    """Schedule system shutdown.

    Args:
        delay: Seconds before shutdown (default 10)
    """
    system_service = SystemService()

    logger.warning(f"System shutdown requested with delay={delay}s")

    result = await system_service.shutdown_system(delay_seconds=delay)

    return AdminResponse(
        success=result["success"],
        data=result,
    )


# Service management endpoints
@router.get("/services", response_model=AdminResponse)
async def get_services(
    admin: dict = Depends(get_admin_user),
):
    """Get list of manageable system services."""
    system_service = SystemService()

    services = system_service.get_services()

    return AdminResponse(
        success=True,
        data={
            "services": [
                {
                    "name": s.name,
                    "display_name": s.display_name,
                    "status": s.status.value,
                    "description": s.description,
                    "can_restart": s.can_restart,
                    "warning_level": s.warning_level,
                }
                for s in services
            ]
        },
    )


@router.post("/service/{name}/restart", response_model=AdminResponse)
async def restart_service(
    name: str,
    admin: dict = Depends(get_admin_user),
):
    """Restart a system service.

    Args:
        name: Service name (cups, photobooth-backend, hostapd, dnsmasq)
    """
    # Validate service name
    valid_services = [s.value for s in ServiceName]
    if name not in valid_services:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid service name. Must be one of: {valid_services}",
        )

    system_service = SystemService()

    logger.warning(f"Service restart requested: {name}")

    result = await system_service.restart_service(name)

    if not result["success"]:
        raise HTTPException(
            status_code=500, detail=result.get("error", "Restart failed")
        )

    return AdminResponse(
        success=result["success"],
        data=result,
    )


# Cleanup endpoints
@router.get("/cleanup/preview", response_model=AdminResponse)
async def preview_cleanup(
    older_than_days: Optional[int] = None,
    days: Optional[int] = None,
    admin: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Preview cleanup without deleting.

    Shows how many sessions and files would be cleaned.

    Args:
        older_than_days: Retention period in days (primary param)
        days: Retention period in days (alias for backward compat)
    """
    # Use older_than_days as primary, fall back to days, then default to 30
    retention_days = (
        older_than_days if older_than_days is not None
        else (days if days is not None else 30)
    )

    cleanup_service = CleanupService()

    try:
        preview = await cleanup_service.preview_cleanup(db, retention_days=retention_days)

        return AdminResponse(
            success=True,
            data={
                "sessions_count": preview.sessions_count,
                "files_count": preview.files_count,
                "total_size_bytes": preview.total_size_bytes,
                "total_size_mb": round(preview.total_size_bytes / (1024 * 1024), 2),
                "estimated_new_usage_percent": preview.estimated_new_usage_percent,
                "retention_days": retention_days,
            },
        )
    except Exception as e:
        logger.error(f"Cleanup preview failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Preview failed: {str(e)}")


@router.post("/cleanup", response_model=AdminResponse)
async def execute_cleanup(
    request: Optional[CleanupRequest] = None,
    admin: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Execute storage cleanup.

    Deletes files for sessions older than retention period.
    Session metadata is preserved for statistics.

    Args:
        request: JSON body with older_than_days and dry_run fields
    """
    retention_days = request.older_than_days if request else 30

    cleanup_service = CleanupService()

    logger.info(f"Cleanup requested by admin with {retention_days} days retention")

    try:
        result = await cleanup_service.execute_cleanup(db, retention_days=retention_days)

        return AdminResponse(
            success=result.success,
            data={
                "sessions_cleaned": result.sessions_cleaned,
                "files_deleted": result.files_deleted,
                "bytes_freed": result.bytes_freed,
                "mb_freed": round(result.bytes_freed / (1024 * 1024), 2),
                "duration_seconds": result.duration_seconds,
                "errors": result.errors,
            },
        )
    except Exception as e:
        logger.error(f"Cleanup execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


# Photo export endpoints
@router.get("/photos", response_model=AdminResponse)
async def list_exportable_sessions(
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,
    admin: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """List sessions with photos available for export.

    Args:
        page: Page number
        limit: Items per page
        status: Optional status filter (all, active, complete, printed, abandoned)
    """
    export_service = PhotoExportService()

    result = await export_service.list_exportable_sessions(
        db, page=page, limit=min(limit, 100), status_filter=status
    )

    return AdminResponse(
        success=True,
        data=result,
    )


@router.get("/photos/{session_id}", response_model=AdminResponse)
async def get_session_photos(
    session_id: str,
    admin: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Get photos info for a specific session.

    Args:
        session_id: Session ID
    """
    export_service = PhotoExportService()

    result = await export_service.get_session_photos(db, session_id)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return AdminResponse(
        success=True,
        data=result,
    )


@router.get("/photos/{session_id}/download")
async def download_session_photos(
    session_id: str,
    export_type: str = "all",
    admin: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Download photos from a specific session.

    Args:
        session_id: Session ID
        export_type: Export type (all, photos, composite)
    """
    from fastapi.responses import FileResponse

    export_service = PhotoExportService()

    # Validate export type
    try:
        exp_type = ExportType(export_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid export type. Must be one of: {[e.value for e in ExportType]}",
        )

    zip_path = await export_service.export_session(db, session_id, exp_type)

    if not zip_path:
        raise HTTPException(
            status_code=404, detail="Session not found or no files available"
        )

    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=os.path.basename(zip_path),
    )


@router.post("/export", response_model=AdminResponse)
async def create_bulk_export(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status: Optional[str] = None,
    admin: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a bulk export job.

    Args:
        start_date: Start date (ISO format)
        end_date: End date (ISO format)
        status: Session status filter
    """
    export_service = PhotoExportService()

    # Parse dates
    parsed_start = None
    parsed_end = None

    if start_date:
        try:
            parsed_start = datetime.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format")

    if end_date:
        try:
            parsed_end = datetime.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format")

    job_id = await export_service.create_bulk_export(
        db,
        start_date=parsed_start,
        end_date=parsed_end,
        status_filter=status,
    )

    return AdminResponse(
        success=True,
        data={
            "job_id": job_id,
            "message": "Export job created",
        },
    )


@router.get("/export/{job_id}/status", response_model=AdminResponse)
async def get_export_status(
    job_id: str,
    admin: dict = Depends(get_admin_user),
):
    """Get status of an export job.

    Args:
        job_id: Export job ID
    """
    export_service = PhotoExportService()

    job = export_service.get_export_status(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Export job not found")

    return AdminResponse(
        success=True,
        data={
            "id": job.id,
            "status": job.status.value,
            "sessions_count": job.sessions_count,
            "files_count": job.files_count,
            "total_size": job.total_size,
            "total_size_mb": (
                round(job.total_size / (1024 * 1024), 2) if job.total_size else 0
            ),
            "progress": job.progress,
            "created_at": job.created_at.isoformat(),
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "error": job.error,
        },
    )


@router.get("/export/{job_id}/download")
async def download_export(
    job_id: str,
    admin: dict = Depends(get_admin_user),
):
    """Download completed export.

    Args:
        job_id: Export job ID
    """
    from fastapi.responses import FileResponse

    export_service = PhotoExportService()

    job = export_service.get_export_status(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Export job not found")

    if job.status.value != "completed":
        raise HTTPException(
            status_code=400, detail=f"Export not ready. Status: {job.status.value}"
        )

    if not job.download_path or not os.path.exists(job.download_path):
        raise HTTPException(status_code=404, detail="Export file not found")

    return FileResponse(
        job.download_path,
        media_type="application/zip",
        filename=os.path.basename(job.download_path),
    )


# =============================================================================
# Mobile Upload API Endpoints
# =============================================================================


class CreateUploadSessionRequest(BaseModel):
    """Request to create an upload session."""
    layout_type: str = "2x2"  # 1x1, 2x2, or 1x4
    language: str = "ko"


class GenerateUploadCompositeRequest(BaseModel):
    """Request to generate composite from uploaded photos."""
    frame_type: str = "classic"
    include_date: bool = True
    include_logo: bool = False
    include_custom_text: bool = True
    custom_text: Optional[str] = None


class PrintUploadRequest(BaseModel):
    """Request to print uploaded session."""
    copies: int = 1


@router.post("/upload/session", response_model=AdminResponse)
async def create_upload_session(
    request: CreateUploadSessionRequest,
    admin: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new session for mobile photo upload.

    Args:
        request: Session creation parameters including layout_type
    """
    from app.application.ports.services.image_processor_port import (
        LAYOUT_PHOTO_COUNTS, LayoutType
    )

    # Validate layout type
    try:
        layout_type = LayoutType(request.layout_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid layout_type. Must be one of: 1x1, 2x2, 1x4"
        )

    # Get required photo count
    required_photos = LAYOUT_PHOTO_COUNTS.get(layout_type, 4)

    # Create session using existing use case
    from app.application.use_cases.session import CreateSessionInput, CreateSessionUseCase
    from app.infrastructure.repositories import SQLAlchemySessionRepository

    session_repo = SQLAlchemySessionRepository(db)
    use_case = CreateSessionUseCase(session_repo)

    result = await use_case.execute(CreateSessionInput(language=request.language))

    if not result.success:
        raise HTTPException(status_code=400, detail=result.error_message)

    return AdminResponse(
        success=True,
        data={
            "session_id": result.data.session_id,
            "layout_type": request.layout_type,
            "required_photos": required_photos,
            "language": request.language,
        },
    )


@router.post("/upload/session/{session_id}/photos", response_model=AdminResponse)
async def upload_photo(
    session_id: str,
    photo: UploadFile = File(...),
    index: int = Form(...),
    admin: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a photo for mobile upload session.

    Args:
        session_id: Session ID
        photo: Photo file (multipart/form-data)
        index: Photo index (0-based)
    """
    from app.application.use_cases.session import CapturePhotoInput, CapturePhotoUseCase
    from app.infrastructure.repositories import SQLAlchemySessionRepository
    from app.infrastructure.services import ImageProcessor, StorageService

    # Read photo data
    image_data = await photo.read()

    # Create use case with dependencies
    session_repo = SQLAlchemySessionRepository(db)
    storage = StorageService()
    image_processor = ImageProcessor()

    use_case = CapturePhotoUseCase(
        session_repository=session_repo,
        storage=storage,
        image_processor=image_processor,
    )

    result = await use_case.execute(
        CapturePhotoInput(
            session_id=session_id,
            photo_index=index,
            image_data=image_data,
        )
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.error_message)

    return AdminResponse(
        success=True,
        data={
            "photo_id": f"{session_id}_{result.data.index}",
            "index": result.data.index,
            "thumbnail_url": f"/api/photos/{session_id}/{result.data.index}/thumbnail",
        },
    )


@router.post("/upload/session/{session_id}/composite", response_model=AdminResponse)
async def generate_upload_composite(
    session_id: str,
    request: GenerateUploadCompositeRequest,
    layout_type: str = "2x2",
    admin: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate composite image from uploaded photos.

    Args:
        session_id: Session ID
        request: Composite generation options
        layout_type: Layout type (query parameter)
    """
    from app.application.use_cases.session import (
        GenerateCompositeInput, GenerateCompositeUseCase
    )
    from app.infrastructure.repositories import SQLAlchemySessionRepository
    from app.infrastructure.services import StorageService

    session_repo = SQLAlchemySessionRepository(db)
    storage = StorageService()

    use_case = GenerateCompositeUseCase(
        session_repository=session_repo,
        storage=storage,
    )

    result = await use_case.execute(
        GenerateCompositeInput(
            session_id=session_id,
            include_date=request.include_date,
            include_logo=request.include_logo,
            include_custom_text=request.include_custom_text,
            custom_text=request.custom_text or "2026 Somang Youth\nRwanda missionary",
            frame_type=request.frame_type,
            layout_type=layout_type,
        )
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.error_message)

    return AdminResponse(
        success=True,
        data={
            "composite_path": result.data.composite_path,
            "composite_url": f"/api/composite/{session_id}",
        },
    )


@router.post("/upload/session/{session_id}/print", response_model=AdminResponse)
async def print_upload_session(
    session_id: str,
    request: PrintUploadRequest,
    admin: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit print job for uploaded session.

    Args:
        session_id: Session ID
        request: Print options including copies
    """
    from app.application.use_cases.print import SubmitPrintJobInput, SubmitPrintJobUseCase
    from app.infrastructure.repositories import (
        SQLAlchemyPrintJobRepository, SQLAlchemySessionRepository
    )
    from app.infrastructure.services import PrinterService

    session_repo = SQLAlchemySessionRepository(db)
    job_repo = SQLAlchemyPrintJobRepository(db)
    printer = PrinterService()

    use_case = SubmitPrintJobUseCase(
        session_repository=session_repo,
        print_job_repository=job_repo,
        printer=printer,
    )

    result = await use_case.execute(
        SubmitPrintJobInput(
            session_id=session_id,
            copies=request.copies,
        )
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.error_message)

    return AdminResponse(
        success=True,
        data={
            "job_id": result.data.job_id,
            "status": result.data.status,
            "copies": request.copies,
        },
    )
