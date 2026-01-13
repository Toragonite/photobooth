"""Integration tests for Session API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestSessionAPI:
    """Tests for session management API."""

    @pytest.mark.asyncio
    async def test_create_session_korean(self, client: AsyncClient):
        """Create a session with Korean language."""
        response = await client.post(
            "/api/session",
            json={"language": "ko"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "session_id" in data["data"]
        assert data["data"]["language"] == "ko"
        assert data["data"]["status"] == "active"

    @pytest.mark.asyncio
    async def test_create_session_english(self, client: AsyncClient):
        """Create a session with English language."""
        response = await client.post(
            "/api/session",
            json={"language": "en"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["data"]["language"] == "en"

    @pytest.mark.asyncio
    async def test_create_session_default_language(self, client: AsyncClient):
        """Create a session without language defaults to Korean."""
        response = await client.post(
            "/api/session",
            json={},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["data"]["language"] == "ko"

    @pytest.mark.asyncio
    async def test_get_session(self, client: AsyncClient):
        """Get an existing session."""
        # Create session
        create_resp = await client.post(
            "/api/session",
            json={"language": "ko"},
        )
        session_id = create_resp.json()["data"]["session_id"]

        # Get session
        response = await client.get(f"/api/session/{session_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["session_id"] == session_id

    @pytest.mark.asyncio
    async def test_get_nonexistent_session(self, client: AsyncClient):
        """Getting a nonexistent session returns 404."""
        response = await client.get("/api/session/nonexistent-id")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_abandon_session(self, client: AsyncClient):
        """Abandon an active session."""
        # Create session
        create_resp = await client.post(
            "/api/session",
            json={"language": "ko"},
        )
        session_id = create_resp.json()["data"]["session_id"]

        # Abandon session (DELETE method)
        response = await client.delete(f"/api/session/{session_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify session is abandoned
        get_resp = await client.get(f"/api/session/{session_id}")
        assert get_resp.json()["data"]["status"] == "abandoned"


@pytest.mark.integration
class TestSessionPhotoUpload:
    """Tests for photo upload to sessions."""

    @pytest.mark.asyncio
    async def test_session_status_after_creation(self, client: AsyncClient):
        """Session starts with status active and 0 photos."""
        create_resp = await client.post(
            "/api/session",
            json={"language": "ko"},
        )
        session_id = create_resp.json()["data"]["session_id"]

        response = await client.get(f"/api/session/{session_id}")
        data = response.json()["data"]

        assert data["status"] == "active"
        assert data["photo_count"] == 0
