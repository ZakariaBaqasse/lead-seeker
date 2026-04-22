from datetime import date, datetime, timezone

import pytest

from app.models.lead import Lead
from app.pipeline.followups import add_business_days


# ---------------------------------------------------------------------------
# Business-day calculation tests
# ---------------------------------------------------------------------------


def test_add_business_days_monday():
    # Monday Jan 8 + 3 = Thursday Jan 11
    assert add_business_days(date(2024, 1, 8), 3) == date(2024, 1, 11)


def test_add_business_days_friday():
    # Friday Jan 12 + 3 = Wednesday Jan 17 (skip Sat, Sun)
    assert add_business_days(date(2024, 1, 12), 3) == date(2024, 1, 17)


def test_add_business_days_thursday():
    # Thursday Jan 11 + 3 = Tuesday Jan 16 (Fri=1, Mon=2, Tue=3)
    assert add_business_days(date(2024, 1, 11), 3) == date(2024, 1, 16)


def test_add_business_days_zero():
    d = date(2024, 1, 8)
    assert add_business_days(d, 0) == d


def test_add_business_days_weekend_start():
    # Saturday Jan 13 + 1 business day = Monday Jan 15
    assert add_business_days(date(2024, 1, 13), 1) == date(2024, 1, 15)


# ---------------------------------------------------------------------------
# API tests — follow-up status transitions
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


async def test_patch_to_sent_initializes_followup_fields(client, auth_headers, test_lead):
    """First send: should set last_contact_at and follow_up_due_date."""
    response = await client.patch(
        f"/api/leads/{test_lead.id}",
        json={"status": "sent"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "sent"
    assert data["last_contact_at"] is not None
    assert data["follow_up_due_date"] is not None
    assert data["follow_up_count"] == 0
    assert data["follow_up_ready"] is False


async def test_patch_no_response_is_rejected(client, auth_headers, test_lead):
    """Manual PATCH cannot set no_response — it's excluded from ManualLeadStatus."""
    response = await client.patch(
        f"/api/leads/{test_lead.id}",
        json={"status": "no_response"},
        headers=auth_headers,
    )
    assert response.status_code == 422


async def test_patch_terminal_to_sent_rejected(client, auth_headers, db_session):
    """Reopening a terminal lead to sent must fail."""
    lead = Lead(company_name="Terminal Co", status="replied_won")
    db_session.add(lead)
    await db_session.commit()
    await db_session.refresh(lead)

    response = await client.patch(
        f"/api/leads/{lead.id}",
        json={"status": "sent"},
        headers=auth_headers,
    )
    assert response.status_code == 422


async def test_mark_followup_sent_increments_count(client, auth_headers, db_session):
    """mark-sent increments follow_up_count and resets follow_up_ready."""
    lead = Lead(
        company_name="ReadyAI",
        status="sent",
        sent_at=datetime.now(timezone.utc),
        last_contact_at=datetime.now(timezone.utc),
        follow_up_count=0,
        follow_up_ready=True,
        follow_up_due_date=date(2020, 1, 1),
        follow_up_draft="Follow up draft text",
    )
    db_session.add(lead)
    await db_session.commit()
    await db_session.refresh(lead)

    response = await client.post(
        f"/api/leads/{lead.id}/follow-ups/mark-sent",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["follow_up_count"] == 1
    assert data["follow_up_ready"] is False
    assert data["follow_up_due_date"] is not None


async def test_mark_followup_sent_duplicate_submission_blocked(client, auth_headers, db_session):
    """Second mark-sent call must fail when follow_up_ready is False."""
    lead = Lead(
        company_name="DuplicateAI",
        status="sent",
        sent_at=datetime.now(timezone.utc),
        last_contact_at=datetime.now(timezone.utc),
        follow_up_count=0,
        follow_up_ready=True,
        follow_up_due_date=date(2020, 1, 1),
    )
    db_session.add(lead)
    await db_session.commit()
    await db_session.refresh(lead)

    r1 = await client.post(f"/api/leads/{lead.id}/follow-ups/mark-sent", headers=auth_headers)
    assert r1.status_code == 200

    r2 = await client.post(f"/api/leads/{lead.id}/follow-ups/mark-sent", headers=auth_headers)
    assert r2.status_code == 422


async def test_mark_followup_sent_at_max_count_rejected(client, auth_headers, db_session):
    """Cannot mark-sent when follow_up_count is already 2."""
    lead = Lead(
        company_name="MaxCountAI",
        status="sent",
        sent_at=datetime.now(timezone.utc),
        last_contact_at=datetime.now(timezone.utc),
        follow_up_count=2,
        follow_up_ready=True,
        follow_up_due_date=date(2020, 1, 1),
    )
    db_session.add(lead)
    await db_session.commit()
    await db_session.refresh(lead)

    response = await client.post(
        f"/api/leads/{lead.id}/follow-ups/mark-sent",
        headers=auth_headers,
    )
    assert response.status_code == 422


async def test_patch_to_replied_clears_followup_flags(client, auth_headers, db_session):
    """Transitioning to replied_won clears follow_up_ready and follow_up_due_date."""
    lead = Lead(
        company_name="WonAI",
        status="sent",
        sent_at=datetime.now(timezone.utc),
        last_contact_at=datetime.now(timezone.utc),
        follow_up_count=1,
        follow_up_ready=True,
        follow_up_due_date=date(2024, 12, 31),
    )
    db_session.add(lead)
    await db_session.commit()
    await db_session.refresh(lead)

    response = await client.patch(
        f"/api/leads/{lead.id}",
        json={"status": "replied_won"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "replied_won"
    assert data["follow_up_ready"] is False
    assert data["follow_up_due_date"] is None


async def test_no_response_in_stats(client, auth_headers, db_session):
    """Stats endpoint should include no_response count."""
    lead = Lead(company_name="GhostAI", status="no_response")
    db_session.add(lead)
    await db_session.commit()

    response = await client.get("/api/stats", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "no_response" in data
    assert data["no_response"] == 1
