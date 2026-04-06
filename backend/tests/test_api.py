import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.db import get_db
from app.config import settings

TEST_API_KEY = "test-api-key-for-tests"


@pytest.fixture(autouse=True)
def set_test_api_key(monkeypatch):
    monkeypatch.setattr(settings, "API_SECRET_KEY", TEST_API_KEY)


def make_mock_db_none():
    """DB dependency override that returns None for all queries."""
    async def _mock_db():
        mock_session = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_result.scalars.return_value.all.return_value = []
        mock_result.scalar_one.return_value = 0
        mock_result.all.return_value = []
        mock_session.execute.return_value = mock_result
        yield mock_session
    return _mock_db


@pytest.fixture
async def client():
    app.dependency_overrides[get_db] = make_mock_db_none()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
async def auth_client(client):
    client.headers["X-API-Key"] = TEST_API_KEY
    return client


class TestAuth:
    async def test_health_no_auth_returns_200(self, client):
        r = await client.get("/health")
        assert r.status_code == 200

    async def test_missing_api_key_returns_403(self, client):
        r = await client.get("/api/leads")
        assert r.status_code == 403

    async def test_wrong_api_key_returns_403(self, client):
        r = await client.get("/api/leads", headers={"X-API-Key": "wrong"})
        assert r.status_code == 403

    async def test_valid_api_key_not_403(self, auth_client):
        r = await auth_client.get("/api/leads")
        assert r.status_code != 403


class TestLeadsEndpoints:
    async def test_list_leads_returns_list_response(self, auth_client):
        r = await auth_client.get("/api/leads")
        assert r.status_code == 200
        data = r.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)

    async def test_list_leads_page_zero_returns_422(self, auth_client):
        r = await auth_client.get("/api/leads?page=0")
        assert r.status_code == 422

    async def test_list_leads_limit_too_high_returns_422(self, auth_client):
        r = await auth_client.get("/api/leads?limit=200")
        assert r.status_code == 422

    async def test_get_lead_not_found_returns_404(self, auth_client):
        r = await auth_client.get(f"/api/leads/{uuid.uuid4()}")
        assert r.status_code == 404

    async def test_patch_lead_not_found_returns_404(self, auth_client):
        r = await auth_client.patch(f"/api/leads/{uuid.uuid4()}", json={"notes": "test"})
        assert r.status_code == 404

    async def test_delete_lead_not_found_returns_404(self, auth_client):
        r = await auth_client.delete(f"/api/leads/{uuid.uuid4()}")
        assert r.status_code == 404

    async def test_regenerate_lead_not_found_returns_404(self, auth_client):
        r = await auth_client.post(f"/api/leads/{uuid.uuid4()}/regenerate")
        assert r.status_code == 404


class TestStatsEndpoint:
    async def test_stats_returns_correct_shape(self, auth_client):
        r = await auth_client.get("/api/stats")
        assert r.status_code == 200
        data = r.json()
        for key in ["draft", "sent", "replied_won", "replied_lost", "archived"]:
            assert key in data
            assert isinstance(data[key], int)
