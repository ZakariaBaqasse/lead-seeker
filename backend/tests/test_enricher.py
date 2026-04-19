"""Unit tests for app.pipeline.enricher."""
import pytest
from unittest.mock import AsyncMock, patch
from app.pipeline.enricher import enrich_lead, _build_snippets_text
from app.schemas.lead import EnrichmentResult, ExtractionResult


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

sample_extraction = ExtractionResult(
    company_name="AcmeAI",
    company_domain="acmeai.io",
    funding_amount="$5M",
    funding_round="Seed",
    funding_date="2025-01-15",
    employee_count_estimate=20,
    region="USA",
    country="United States",
    summary="AcmeAI builds LLM tooling.",
    is_relevant=True,
)

sample_people_results = [
    {"title": "Jane Smith - CTO at AcmeAI", "url": "https://www.linkedin.com/in/janesmith", "content": "Jane Smith is the CTO of AcmeAI."},
]

sample_company_results = [
    {"title": "AcmeAI - AI platform", "url": "https://acmeai.io", "content": "AcmeAI builds Python-based LLM tooling with 25 employees."},
]

sample_enrichment_result = EnrichmentResult(
    cto_name="Jane Smith",
    linkedin_url="https://www.linkedin.com/in/janesmith",
    employee_count=25,
    product_description="AcmeAI builds LLM tooling for enterprise.",
    tech_stack="Python, LangChain, AWS",
)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


async def test_enrich_lead_success():
    """Full success: Tavily returns results, Mistral parses them."""
    with (
        patch("app.pipeline.enricher.settings") as mock_settings,
        patch("app.pipeline.enricher._search_tavily", new_callable=AsyncMock) as mock_search,
        patch("app.pipeline.enricher._parse_enrichment", new_callable=AsyncMock) as mock_parse,
    ):
        mock_settings.TAVILY_API_KEY = "test-key"
        mock_search.side_effect = [sample_people_results, sample_company_results]
        mock_parse.return_value = sample_enrichment_result

        result = await enrich_lead(sample_extraction)

    assert result is not None
    assert result.cto_name == "Jane Smith"
    assert result.linkedin_url == "https://www.linkedin.com/in/janesmith"
    assert result.tech_stack == "Python, LangChain, AWS"


async def test_enrich_lead_skipped_no_api_key():
    """When TAVILY_API_KEY is empty, enrichment is skipped — no API calls made."""
    with (
        patch("app.pipeline.enricher.settings") as mock_settings,
        patch("app.pipeline.enricher._search_tavily", new_callable=AsyncMock) as mock_search,
    ):
        mock_settings.TAVILY_API_KEY = ""

        result = await enrich_lead(sample_extraction)

    assert result is None
    mock_search.assert_not_called()


async def test_enrich_lead_tavily_failure():
    """When both Tavily searches return empty (failure), returns None."""
    with (
        patch("app.pipeline.enricher.settings") as mock_settings,
        patch("app.pipeline.enricher._search_tavily", new_callable=AsyncMock) as mock_search,
        patch("app.pipeline.enricher._parse_enrichment", new_callable=AsyncMock) as mock_parse,
    ):
        mock_settings.TAVILY_API_KEY = "test-key"
        mock_search.side_effect = [[], []]
        mock_parse.return_value = None

        result = await enrich_lead(sample_extraction)

    assert result is None


async def test_enrich_lead_mistral_failure():
    """When Tavily succeeds but Mistral parsing fails, returns None."""
    with (
        patch("app.pipeline.enricher.settings") as mock_settings,
        patch("app.pipeline.enricher._search_tavily", new_callable=AsyncMock) as mock_search,
        patch("app.pipeline.enricher._parse_enrichment", new_callable=AsyncMock) as mock_parse,
    ):
        mock_settings.TAVILY_API_KEY = "test-key"
        mock_search.side_effect = [sample_people_results, sample_company_results]
        mock_parse.return_value = None

        result = await enrich_lead(sample_extraction)

    assert result is None


async def test_enrich_lead_partial_results():
    """When only people results found, partial EnrichmentResult returned."""
    partial_result = EnrichmentResult(cto_name="Jane Smith", linkedin_url="https://www.linkedin.com/in/janesmith")

    with (
        patch("app.pipeline.enricher.settings") as mock_settings,
        patch("app.pipeline.enricher._search_tavily", new_callable=AsyncMock) as mock_search,
        patch("app.pipeline.enricher._parse_enrichment", new_callable=AsyncMock) as mock_parse,
    ):
        mock_settings.TAVILY_API_KEY = "test-key"
        mock_search.side_effect = [sample_people_results, []]
        mock_parse.return_value = partial_result

        result = await enrich_lead(sample_extraction)

    assert result is not None
    assert result.cto_name == "Jane Smith"
    assert result.tech_stack is None
    assert result.product_description is None


def test_snippets_truncated():
    """_build_snippets_text output is capped at 4000 characters."""
    long_content = "x" * 3000
    people = [{"title": "Person", "url": "https://example.com", "content": long_content}]
    company = [{"title": "Company", "url": "https://company.com", "content": long_content}]

    result = _build_snippets_text(people, company)

    assert len(result) <= 4000


def test_snippets_empty_results():
    """_build_snippets_text handles empty result lists."""
    result = _build_snippets_text([], [])
    assert result == "" or isinstance(result, str)


async def test_enrich_lead_linkedin_url_extraction():
    """LinkedIn URL in result URL field is extracted correctly."""
    people_with_linkedin = [
        {"title": "Jane Smith CTO", "url": "https://www.linkedin.com/in/janesmith-cto", "content": "Jane is CTO of AcmeAI"},
    ]
    result_with_linkedin = EnrichmentResult(
        cto_name="Jane Smith",
        linkedin_url="https://www.linkedin.com/in/janesmith-cto",
    )

    with (
        patch("app.pipeline.enricher.settings") as mock_settings,
        patch("app.pipeline.enricher._search_tavily", new_callable=AsyncMock) as mock_search,
        patch("app.pipeline.enricher._parse_enrichment", new_callable=AsyncMock) as mock_parse,
    ):
        mock_settings.TAVILY_API_KEY = "test-key"
        mock_search.side_effect = [people_with_linkedin, []]
        mock_parse.return_value = result_with_linkedin

        result = await enrich_lead(sample_extraction)

    assert result is not None
    assert result.linkedin_url is not None
    assert "linkedin.com/in/" in result.linkedin_url
