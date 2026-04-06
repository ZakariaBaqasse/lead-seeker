import pytest
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from app.pipeline.filter import filter_lead, is_duplicate
from app.schemas.pipeline import ExtractionResult


def make_valid_extraction(**overrides) -> ExtractionResult:
    today = date.today()
    recent = (today - timedelta(days=30)).isoformat()
    defaults = dict(
        company_name="Acme AI",
        company_domain="acme.ai",
        funding_amount="$10M",
        funding_round="Series A",
        funding_date=recent,
        employee_count_estimate=25,
        region="Europe",
        country="France",
        sector="GenAI",
        summary="AI startup",
        is_relevant=True,
    )
    defaults.update(overrides)
    return ExtractionResult(**defaults)


class TestFilterLead:
    def test_valid_lead_passes(self):
        assert filter_lead(make_valid_extraction()) is True

    def test_not_relevant_rejected(self):
        assert filter_lead(make_valid_extraction(is_relevant=False)) is False

    def test_wrong_sector_rejected(self):
        assert filter_lead(make_valid_extraction(sector="Other")) is False

    def test_non_genai_sector_rejected(self):
        assert filter_lead(make_valid_extraction(sector="Fintech")) is False

    def test_region_europe_accepted(self):
        assert filter_lead(make_valid_extraction(region="Europe")) is True

    def test_region_usa_accepted(self):
        assert filter_lead(make_valid_extraction(region="USA")) is True

    def test_region_other_rejected(self):
        assert filter_lead(make_valid_extraction(region="Asia")) is False

    def test_employee_count_at_min_accepted(self):
        assert filter_lead(make_valid_extraction(employee_count_estimate=10)) is True

    def test_employee_count_at_max_accepted(self):
        assert filter_lead(make_valid_extraction(employee_count_estimate=50)) is True

    def test_employee_count_below_min_rejected(self):
        assert filter_lead(make_valid_extraction(employee_count_estimate=5)) is False

    def test_employee_count_above_max_rejected(self):
        assert filter_lead(make_valid_extraction(employee_count_estimate=100)) is False

    def test_missing_employee_count_accepted(self):
        # employee_count is optional — null means we don't know, should pass
        assert filter_lead(make_valid_extraction(employee_count_estimate=None)) is True

    def test_funding_date_within_12_months_accepted(self):
        recent = (date.today() - timedelta(days=180)).isoformat()
        assert filter_lead(make_valid_extraction(funding_date=recent)) is True

    def test_funding_date_older_than_12_months_rejected(self):
        old = (date.today() - timedelta(days=400)).isoformat()
        assert filter_lead(make_valid_extraction(funding_date=old)) is False

    def test_missing_company_name_rejected(self):
        assert filter_lead(make_valid_extraction(company_name=None)) is False

    def test_missing_funding_amount_rejected(self):
        assert filter_lead(make_valid_extraction(funding_amount=None)) is False

    def test_missing_funding_date_rejected(self):
        assert filter_lead(make_valid_extraction(funding_date=None)) is False

    def test_invalid_funding_date_format_rejected(self):
        assert filter_lead(make_valid_extraction(funding_date="not-a-date")) is False


class TestIsDuplicate:
    @pytest.mark.asyncio
    async def test_domain_match_is_duplicate(self):
        """Domain match → duplicate."""
        mock_lead = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_lead
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute.return_value = mock_result

        extraction = make_valid_extraction(company_domain="acme.ai")
        assert await is_duplicate(mock_session, extraction) is True

    @pytest.mark.asyncio
    async def test_name_match_is_duplicate(self):
        """No domain, name match → duplicate."""
        mock_lead = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_lead
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute.return_value = mock_result

        extraction = make_valid_extraction(company_domain=None, company_name="Acme AI")
        assert await is_duplicate(mock_session, extraction) is True

    @pytest.mark.asyncio
    async def test_no_match_not_duplicate(self):
        """No domain, no name match → not duplicate."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute.return_value = mock_result

        extraction = make_valid_extraction(company_domain=None)
        assert await is_duplicate(mock_session, extraction) is False
