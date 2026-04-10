import uuid

import pytest

from app.models.lead import Lead


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def test_lead(db_session):
    lead = Lead(
        company_name="TestAI Inc",
        company_domain="testai.com",
        status="draft",
    )
    db_session.add(lead)
    await db_session.commit()
    await db_session.refresh(lead)
    return lead


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


async def test_health_with_auth(client, auth_headers):
    response = await client.get("/api/health", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_health_without_auth(client):
    response = await client.get("/api/health")
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# GET /api/leads
# ---------------------------------------------------------------------------


async def test_list_leads_empty(client, auth_headers):
    response = await client.get("/api/leads", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["items"] == []
    assert data["total"] == 0


async def test_list_leads_status_filter(client, auth_headers):
    response = await client.get("/api/leads?status=draft", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data


# ---------------------------------------------------------------------------
# GET /api/leads/{id}
# ---------------------------------------------------------------------------


async def test_get_lead_not_found(client, auth_headers):
    response = await client.get(f"/api/leads/{uuid.uuid4()}", headers=auth_headers)
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /api/leads/{id}
# ---------------------------------------------------------------------------


async def test_patch_lead_not_found(client, auth_headers):
    response = await client.patch(
        f"/api/leads/{uuid.uuid4()}",
        json={"notes": "test"},
        headers=auth_headers,
    )
    assert response.status_code == 404


async def test_patch_lead_sent_sets_sent_at(client, auth_headers, test_lead):
    response = await client.patch(
        f"/api/leads/{test_lead.id}",
        json={"status": "sent"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "sent"
    assert data["sent_at"] is not None


async def test_patch_lead_status_null_returns_422(client, auth_headers, test_lead):
    response = await client.patch(
        f"/api/leads/{test_lead.id}",
        json={"status": None},
        headers=auth_headers,
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# DELETE /api/leads/{id}
# ---------------------------------------------------------------------------


async def test_delete_lead(client, auth_headers, test_lead):
    response = await client.delete(f"/api/leads/{test_lead.id}", headers=auth_headers)
    assert response.status_code == 204

    # Second delete on the same ID must return 404
    response = await client.delete(f"/api/leads/{test_lead.id}", headers=auth_headers)
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/stats
# ---------------------------------------------------------------------------


async def test_get_stats_empty(client, auth_headers):
    response = await client.get("/api/stats", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    for status_key in ["draft", "sent", "replied_won", "replied_lost", "archived"]:
        assert status_key in data
        assert data[status_key] == 0


# ---------------------------------------------------------------------------
# POST /api/leads/{id}/regenerate
# ---------------------------------------------------------------------------


async def test_regenerate_not_found(client, auth_headers):
    response = await client.post(f"/api/leads/{uuid.uuid4()}/regenerate", headers=auth_headers)
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/pipeline/status
# ---------------------------------------------------------------------------


async def test_pipeline_status_no_runs(client, auth_headers):
    response = await client.get("/api/pipeline/status", headers=auth_headers)
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/profile/reload
# ---------------------------------------------------------------------------


async def test_profile_reload(client, auth_headers):
    response = await client.post("/api/profile/reload", headers=auth_headers)
    assert response.status_code == 200
