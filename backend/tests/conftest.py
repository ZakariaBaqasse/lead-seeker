import pytest
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.config import settings

TEST_API_KEY = "test-secret-key"


@pytest.fixture(autouse=True)
def override_settings(monkeypatch):
    """Override settings for all tests."""
    monkeypatch.setattr(settings, "API_SECRET_KEY", TEST_API_KEY)


@pytest.fixture
async def client():
    """Async HTTP test client with valid API key."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"X-API-Key": TEST_API_KEY},
    ) as c:
        yield c


@pytest.fixture
def api_key_headers():
    return {"X-API-Key": TEST_API_KEY}
