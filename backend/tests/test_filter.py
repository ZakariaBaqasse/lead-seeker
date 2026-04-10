import uuid
from datetime import date, timedelta

import pytest

from app.models.lead import Lead
from app.pipeline.filter import filter_lead, is_duplicate
from app.schemas.lead import ExtractionResult

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MAX_FUNDING_AGE_DAYS = 365  # must match filter.py


def valid_extraction(**overrides) -> ExtractionResult:
    """Return a base ExtractionResult that passes all filters."""
    base = dict(
        company_name="TestAI",
        company_domain="testai.com",
        sector="GENAI",
        region="USA",
        country="United States",
        employee_count_estimate=20,
        funding_amount="$10M",
        funding_round="Series A",
        funding_date=date.today().isoformat(),
        summary="TestAI builds LLM tooling",
        is_relevant=True,
    )
    base.update(overrides)
    return ExtractionResult(**base)


# ---------------------------------------------------------------------------
# filter_lead() tests
# ---------------------------------------------------------------------------


def test_filter_valid_genai_startup():
    assert filter_lead(valid_extraction()) is True


def test_filter_non_genai_sector_rejected():
    assert filter_lead(valid_extraction(sector="fintech")) is False


def test_filter_non_eu_usa_region_rejected():
    assert filter_lead(valid_extraction(region="Asia")) is False


def test_filter_too_many_employees_rejected():
    assert filter_lead(valid_extraction(employee_count_estimate=100)) is False


def test_filter_too_few_employees_rejected():
    assert filter_lead(valid_extraction(employee_count_estimate=5)) is False


def test_filter_old_funding_date_rejected():
    old_date = (date.today() - timedelta(days=MAX_FUNDING_AGE_DAYS + 1)).isoformat()
    assert filter_lead(valid_extraction(funding_date=old_date)) is False


def test_filter_none_sector_passes():
    """Unknown sector (None) should not be filtered out."""
    assert filter_lead(valid_extraction(sector=None)) is True


def test_filter_none_region_passes():
    """Unknown region (None) should not be filtered out."""
    assert filter_lead(valid_extraction(region=None)) is True


def test_filter_none_employee_count_passes():
    """Unknown employee count (None) should not be filtered out."""
    assert filter_lead(valid_extraction(employee_count_estimate=None)) is True


# ---------------------------------------------------------------------------
# is_duplicate() tests
# ---------------------------------------------------------------------------


async def test_is_duplicate_new_company(db_session):
    extraction = valid_extraction()
    assert await is_duplicate(db_session, extraction) is False


async def test_is_duplicate_same_domain(db_session):
    lead = Lead(company_name="TestAI", company_domain="testai.com", status="draft")
    db_session.add(lead)
    await db_session.commit()

    extraction = valid_extraction(company_name="Different Name", company_domain="testai.com")
    assert await is_duplicate(db_session, extraction) is True


async def test_is_duplicate_same_name_case_insensitive_null_domain(db_session):
    lead = Lead(company_name="TestAI", company_domain=None, status="draft")
    db_session.add(lead)
    await db_session.commit()

    extraction = valid_extraction(company_name="testai", company_domain=None)
    assert await is_duplicate(db_session, extraction) is True


async def test_is_duplicate_null_domain_different_name(db_session):
    lead = Lead(company_name="OtherCompany", company_domain=None, status="draft")
    db_session.add(lead)
    await db_session.commit()

    extraction = valid_extraction(company_name="TestAI", company_domain=None)
    assert await is_duplicate(db_session, extraction) is False


async def test_is_duplicate_domain_present_name_match_not_duplicate(db_session):
    """Name fallback must NOT fire when extraction has a domain (different from stored one)."""
    lead = Lead(company_name="TestAI", company_domain="old-testai.com", status="draft")
    db_session.add(lead)
    await db_session.commit()

    extraction = valid_extraction(company_name="TestAI", company_domain="new-testai.com")
    assert await is_duplicate(db_session, extraction) is False
