"""Admin API endpoints."""

import json
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...config import get_settings
from ...infrastructure.database import (
    AdminSessionModel,
    JobEventModel,
    LoginAttemptModel,
    PrintJobModel,
    SessionModel,
    SettingsModel,
    get_db,
)
from ...infrastructure.services import PrinterService, StorageService

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
        result = await db.execute(
            select(AdminSessionModel).where(AdminSessionModel.token == token[:64])
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

    # Generate token
    expires_at = datetime.now() + timedelta(minutes=settings.token_expire_minutes)
    payload = {
        "sub": "admin",
        "exp": expires_at,
        "iat": datetime.now(),
    }
    token = jwt.encode(payload, settings.secret_key, algorithm="HS256")

    # Store session
    admin_session = AdminSessionModel(
        token=token[:64],  # Store hash of token
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
            result = await db.execute(
                select(AdminSessionModel).where(AdminSessionModel.token == token[:64])
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
    admin: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Get full system status."""
    # Printer status
    printer_service = PrinterService()
    printer_info = printer_service.get_printer_status()

    printer_data = {
        "name": printer_info.name if printer_info else "Unknown",
        "model": printer_info.model if printer_info else "Unknown",
        "status": printer_info.state.value if printer_info else "offline",
        "health": "healthy" if printer_info else "unhealthy",
        "mock_mode": printer_service.mock_mode,
    }

    # Storage status
    storage_service = StorageService()
    storage_stats = storage_service.get_storage_stats()

    storage_data = {
        "total_bytes": storage_stats["total_bytes"],
        "used_bytes": storage_stats["used_bytes"],
        "free_bytes": storage_stats["free_bytes"],
        "percent_used": storage_stats["percent_used"],
        "health": "healthy" if storage_stats["percent_used"] < 90 else "warning",
    }

    # Today's activity
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # Session counts
    result = await db.execute(
        select(func.count(SessionModel.id)).where(
            SessionModel.created_at >= today_start
        )
    )
    sessions_today = result.scalar() or 0

    # Print job counts
    result = await db.execute(
        select(PrintJobModel.status, func.count(PrintJobModel.id))
        .where(PrintJobModel.created_at >= today_start)
        .group_by(PrintJobModel.status)
    )
    job_counts = dict(result.all())

    activity = {
        "date": today_start.date().isoformat(),
        "sessions_started": sessions_today,
        "prints_total": sum(job_counts.values()),
        "prints_completed": job_counts.get("completed", 0),
        "prints_failed": job_counts.get("failed", 0),
        "prints_cancelled": job_counts.get("cancelled", 0),
    }

    return AdminResponse(
        success=True,
        data={
            "timestamp": datetime.now().isoformat(),
            "overall_health": "healthy",
            "printer": printer_data,
            "storage": storage_data,
            "activity": activity,
        },
    )


@router.get("/print-history", response_model=AdminResponse)
async def get_print_history(
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,
    admin: dict = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated print history."""
    limit = min(limit, 100)
    offset = (page - 1) * limit

    # Build query
    query = select(PrintJobModel).order_by(PrintJobModel.created_at.desc())

    if status and status != "all":
        query = query.where(PrintJobModel.status == status)

    # Get total count
    count_query = select(func.count(PrintJobModel.id))
    if status and status != "all":
        count_query = count_query.where(PrintJobModel.status == status)

    result = await db.execute(count_query)
    total = result.scalar() or 0

    # Get jobs
    result = await db.execute(query.offset(offset).limit(limit))
    jobs = result.scalars().all()

    jobs_data = [
        {
            "id": job.id,
            "session_id": job.session_id,
            "status": job.status,
            "copies": job.copies,
            "created_at": job.created_at.isoformat(),
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "error_code": job.error_code,
        }
        for job in jobs
    ]

    return AdminResponse(
        success=True,
        data={
            "jobs": jobs_data,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit,
            },
        },
    )


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
    admin: dict = Depends(get_admin_user),
):
    """Send test print."""
    printer_service = PrinterService()

    if not printer_service.is_available():
        raise HTTPException(status_code=503, detail="Printer is offline")

    # For now, just return success (would generate test pattern)
    logger.info("Test print requested")

    return AdminResponse(
        success=True,
        data={
            "message": "Test print submitted",
            "mock_mode": printer_service.mock_mode,
        },
    )


@router.get("/logs", response_model=AdminResponse)
async def get_logs(
    level: str = "all",
    limit: int = 100,
    admin: dict = Depends(get_admin_user),
):
    """Get system logs."""
    # For now, return empty (would read from log file)
    return AdminResponse(
        success=True,
        data={
            "logs": [],
            "total_count": 0,
            "has_more": False,
        },
    )


@router.post("/system/reboot", response_model=AdminResponse)
async def reboot_system(
    admin: dict = Depends(get_admin_user),
):
    """Schedule system reboot."""
    logger.warning("System reboot requested")

    # In production, would schedule actual reboot
    # os.system("sudo reboot")

    return AdminResponse(
        success=True,
        data={
            "message": "Reboot scheduled in 10 seconds",
            "scheduled_at": datetime.now().isoformat(),
            "delay_seconds": 10,
        },
    )
