"""Database configuration and models."""

from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy import (CheckConstraint, Column, DateTime, ForeignKey, Index,
                        Integer, String, Text, text)
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.orm import declarative_base, relationship

from ..config import get_settings

settings = get_settings()

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
)

# Create async session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()


# Database Models
class SessionModel(Base):
    """Photo session database model."""

    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True)
    language = Column(String(2), nullable=False, default="ko")
    status = Column(String(20), nullable=False, default="active")
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    completed_at = Column(DateTime, nullable=True)
    abandoned_at = Column(DateTime, nullable=True)
    composite_path = Column(Text, nullable=True)

    # Cleanup tracking
    files_cleaned = Column(Integer, nullable=False, default=0)
    cleaned_at = Column(DateTime, nullable=True)

    # Relationships
    photos = relationship(
        "PhotoModel", back_populates="session", cascade="all, delete-orphan"
    )
    print_jobs = relationship(
        "PrintJobModel", back_populates="session", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("language IN ('ko', 'en')"),
        CheckConstraint("status IN ('active', 'complete', 'printed', 'abandoned')"),
        Index("idx_sessions_status", "status"),
        Index("idx_sessions_created_at", "created_at"),
        Index("idx_sessions_files_cleaned", "files_cleaned"),
    )


class PhotoModel(Base):
    """Photo database model."""

    __tablename__ = "photos"

    id = Column(String(36), primary_key=True)
    session_id = Column(
        String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    index = Column(Integer, nullable=False)
    file_path = Column(Text, nullable=False)
    thumbnail_path = Column(Text, nullable=False)
    captured_at = Column(DateTime, nullable=False, default=datetime.now)
    file_size = Column(Integer, nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)

    # Relationships
    session = relationship("SessionModel", back_populates="photos")

    __table_args__ = (
        CheckConstraint('"index" >= 0 AND "index" <= 3'),
        Index("idx_photos_session_id", "session_id"),
    )


class PrintJobModel(Base):
    """Print job database model."""

    __tablename__ = "print_jobs"

    id = Column(String(8), primary_key=True)
    session_id = Column(
        String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    status = Column(String(20), nullable=False, default="pending")
    copies = Column(Integer, nullable=False, default=1)
    cups_job_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    next_retry_at = Column(DateTime, nullable=True)

    # Relationships
    session = relationship("SessionModel", back_populates="print_jobs")
    events = relationship(
        "JobEventModel", back_populates="job", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("copies >= 1 AND copies <= 3"),
        CheckConstraint(
            "status IN ('pending', 'processing', 'printing', 'completed', "
            "'failed', 'cancelled', 'retry_pending')"
        ),
        Index("idx_print_jobs_session_id", "session_id"),
        Index("idx_print_jobs_status", "status"),
        Index("idx_print_jobs_created_at", "created_at"),
    )


class JobEventModel(Base):
    """Job event timeline model."""

    __tablename__ = "job_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(
        String(8), ForeignKey("print_jobs.id", ondelete="CASCADE"), nullable=False
    )
    event_type = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    details = Column(Text, nullable=True)  # JSON
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    # Relationships
    job = relationship("PrintJobModel", back_populates="events")

    __table_args__ = (
        Index("idx_job_events_job_id", "job_id"),
        Index("idx_job_events_created_at", "created_at"),
    )


class SettingsModel(Base):
    """Application settings model."""

    __tablename__ = "settings"

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)  # JSON
    updated_at = Column(DateTime, nullable=False, default=datetime.now)


class AdminSessionModel(Base):
    """Admin authentication session model."""

    __tablename__ = "admin_sessions"

    token = Column(String(64), primary_key=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Integer, nullable=False, default=0)

    __table_args__ = (Index("idx_admin_sessions_expires_at", "expires_at"),)


class LoginAttemptModel(Base):
    """Login attempt tracking for rate limiting."""

    __tablename__ = "login_attempts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ip_address = Column(String(45), nullable=False)
    attempted_at = Column(DateTime, nullable=False, default=datetime.now)
    success = Column(Integer, nullable=False, default=0)

    __table_args__ = (
        Index("idx_login_attempts_ip", "ip_address"),
        Index("idx_login_attempts_time", "attempted_at"),
    )


# Default settings to seed
DEFAULT_SETTINGS = {
    "display.default_language": '"ko"',
    "display.countdown_options": "[3, 5, 8, 10]",
    "display.default_countdown": "5",
    "display.sound_enabled": "true",
    "print.max_copies": "3",
    "print.paper_size": '"4x6"',
    "print.quality": '"high"',
    "print.logo_enabled": "true",
    "print.date_enabled": "true",
    "print.date_format": '"YYYY.MM.DD"',
    "system.timezone": '"Africa/Kigali"',
    "system.auto_cleanup_days": "30",
    "system.log_level": '"error"',
}


async def init_db():
    """Initialize database and create tables."""
    async with engine.begin() as conn:
        # Enable foreign keys for SQLite
        await conn.execute(text("PRAGMA foreign_keys = ON"))
        await conn.execute(text("PRAGMA journal_mode = WAL"))
        await conn.run_sync(Base.metadata.create_all)

    # Seed default settings
    async with async_session() as session:
        for key, value in DEFAULT_SETTINGS.items():
            existing = await session.get(SettingsModel, key)
            if not existing:
                session.add(SettingsModel(key=key, value=value))
        await session.commit()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
