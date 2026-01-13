"""Pytest configuration and fixtures."""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)

from app.domain.entities import Photo, PhotoSession, PrintJob
from app.domain.value_objects import JobId, Language, PhotoId, SessionId
from app.infrastructure.database import Base, get_db
from app.main import app


# Event loop fixture for async tests
@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


# Test database engine
@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create in-memory test database."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def test_db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Get test database session."""
    async_session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with async_session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client."""

    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# Domain fixtures
@pytest.fixture
def session_id() -> SessionId:
    """Generate a session ID."""
    return SessionId.generate()


@pytest.fixture
def photo_id() -> PhotoId:
    """Generate a photo ID."""
    return PhotoId.generate()


@pytest.fixture
def job_id() -> JobId:
    """Generate a job ID."""
    return JobId.generate()


@pytest.fixture
def sample_session() -> PhotoSession:
    """Create a sample photo session."""
    return PhotoSession.create(language=Language.KOREAN)


@pytest.fixture
def sample_session_english() -> PhotoSession:
    """Create a sample English session."""
    return PhotoSession.create(language=Language.ENGLISH)


@pytest.fixture
def sample_photo(session_id: SessionId) -> Photo:
    """Create a sample photo."""
    return Photo(
        id=PhotoId.generate(),
        session_id=session_id,
        index=0,
        file_path="/tmp/test_photo_0.jpg",
        thumbnail_path="/tmp/test_thumb_0.jpg",
        width=1920,
        height=1080,
        size_bytes=500000,
        captured_at=datetime.now(),
    )


def create_photo(session_id: SessionId, index: int) -> Photo:
    """Helper to create a photo at a specific index."""
    return Photo(
        id=PhotoId.generate(),
        session_id=session_id,
        index=index,
        file_path=f"/tmp/test_photo_{index}.jpg",
        thumbnail_path=f"/tmp/test_thumb_{index}.jpg",
        width=1920,
        height=1080,
        size_bytes=500000,
        captured_at=datetime.now(),
    )


@pytest.fixture
def complete_session() -> PhotoSession:
    """Create a complete photo session with 4 photos."""
    session = PhotoSession.create(language=Language.KOREAN)
    for i in range(4):
        photo = create_photo(session.id, i)
        session.add_photo(photo)
    return session


@pytest.fixture
def sample_print_job(session_id: SessionId) -> PrintJob:
    """Create a sample print job."""
    return PrintJob.create(session_id=session_id, copies=1)


@pytest.fixture
def processing_print_job(session_id: SessionId) -> PrintJob:
    """Create a print job in processing state."""
    job = PrintJob.create(session_id=session_id, copies=1)
    job.start_processing()
    return job


@pytest.fixture
def printing_print_job(session_id: SessionId) -> PrintJob:
    """Create a print job in printing state."""
    job = PrintJob.create(session_id=session_id, copies=1)
    job.start_processing()
    job.mark_printing(cups_job_id=12345)
    return job


# Temporary storage fixtures
@pytest.fixture
def temp_storage(tmp_path: Path) -> Path:
    """Create temporary storage directories."""
    photos_dir = tmp_path / "photos"
    composites_dir = tmp_path / "composites"
    thumbnails_dir = tmp_path / "thumbnails"

    photos_dir.mkdir()
    composites_dir.mkdir()
    thumbnails_dir.mkdir()

    return tmp_path
