"""Integration tests for Admin API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestAdminLogin:
    """Tests for admin authentication."""

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient):
        """Successful login with correct PIN."""
        response = await client.post(
            "/api/admin/login",
            json={"pin": "0000"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "token" in data["data"]
        assert "expires_at" in data["data"]

    @pytest.mark.asyncio
    async def test_login_invalid_pin(self, client: AsyncClient):
        """Login fails with incorrect PIN."""
        response = await client.post(
            "/api/admin/login",
            json={"pin": "9999"},  # Wrong PIN
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "AUTH_FAILED"

    @pytest.mark.asyncio
    async def test_login_empty_pin(self, client: AsyncClient):
        """Login fails with empty PIN."""
        response = await client.post(
            "/api/admin/login",
            json={"pin": ""},
        )

        data = response.json()
        assert data["success"] is False


@pytest.mark.integration
class TestAdminProtectedEndpoints:
    """Tests for protected admin endpoints."""

    @pytest.mark.asyncio
    async def test_status_requires_auth(self, client: AsyncClient):
        """Status endpoint requires authentication."""
        response = await client.get("/api/admin/status")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_status_with_valid_token(self, client: AsyncClient):
        """Status endpoint works with valid token."""
        # Login first
        login_resp = await client.post(
            "/api/admin/login",
            json={"pin": "0000"},
        )
        token = login_resp.json()["data"]["token"]

        # Get status
        response = await client.get(
            "/api/admin/status",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "printer" in data["data"]
        assert "storage" in data["data"]
        assert "activity" in data["data"]

    @pytest.mark.asyncio
    async def test_status_with_invalid_token(self, client: AsyncClient):
        """Status endpoint rejects invalid token."""
        response = await client.get(
            "/api/admin/status",
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_settings_requires_auth(self, client: AsyncClient):
        """Settings endpoint requires authentication."""
        response = await client.get("/api/admin/settings")

        assert response.status_code == 401


@pytest.mark.integration
class TestAdminLogout:
    """Tests for admin logout."""

    @pytest.mark.asyncio
    async def test_logout_success(self, client: AsyncClient):
        """Logout invalidates the token."""
        # Login
        login_resp = await client.post(
            "/api/admin/login",
            json={"pin": "0000"},
        )
        token = login_resp.json()["data"]["token"]

        # Logout
        logout_resp = await client.post(
            "/api/admin/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert logout_resp.json()["success"] is True

        # Token should no longer work
        status_resp = await client.get(
            "/api/admin/status",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert status_resp.status_code == 401


@pytest.mark.integration
class TestAdminPrintHistory:
    """Tests for print history endpoint."""

    @pytest.mark.asyncio
    async def test_print_history_empty(self, client: AsyncClient):
        """Print history returns empty list when no jobs."""
        # Login
        login_resp = await client.post(
            "/api/admin/login",
            json={"pin": "0000"},
        )
        token = login_resp.json()["data"]["token"]

        # Get history
        response = await client.get(
            "/api/admin/print-history",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "jobs" in data["data"]
        assert "pagination" in data["data"]

    @pytest.mark.asyncio
    async def test_print_history_pagination(self, client: AsyncClient):
        """Print history supports pagination."""
        # Login
        login_resp = await client.post(
            "/api/admin/login",
            json={"pin": "0000"},
        )
        token = login_resp.json()["data"]["token"]

        # Get history with pagination
        response = await client.get(
            "/api/admin/print-history?page=1&limit=10",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["pagination"]["page"] == 1
        assert data["data"]["pagination"]["limit"] == 10


@pytest.mark.integration
class TestAdminStorage:
    """Tests for storage endpoint."""

    @pytest.mark.asyncio
    async def test_storage_details(self, client: AsyncClient):
        """Storage endpoint returns disk info."""
        # Login
        login_resp = await client.post(
            "/api/admin/login",
            json={"pin": "0000"},
        )
        token = login_resp.json()["data"]["token"]

        # Get storage
        response = await client.get(
            "/api/admin/storage",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "total_bytes" in data["data"]
        assert "free_bytes" in data["data"]
        assert "percent_used" in data["data"]
