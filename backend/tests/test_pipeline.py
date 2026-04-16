from datetime import date
from unittest.mock import AsyncMock, patch

from app.pipeline.runner import run_pipeline
from app.pipeline.sources import RawArticle
from app.schemas.lead import ExtractionResult

# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

sample_article = RawArticle(
    url="https://example.com/article",
    headline="AI startup raises $10M",
    source_name="test",
    body_snippet="TestAI has raised $10M in Series A funding.",
)

sample_extraction = ExtractionResult(
    company_name="TestAI",
    company_domain="testai.com",
    sector=None,  # None passes the sector filter (unknown sector allowed)
    region="USA",
    country="United States",
    employee_count_estimate=20,
    funding_amount="$10M",
    funding_round="Series A",
    funding_date=date.today().isoformat(),
    summary="TestAI builds LLM tooling.",
    is_relevant=True,
)

_mock_profile = {
    "name": "Test User",
    "title": "Freelance Developer",
    "pitch": "I build things.",
    "projects": [
        {
            "name": "My Project",
            "description": "A great project.",
            "video_url": "https://example.com/video",
            "tags": ["python"],
        }
    ],
    "skills": ["Python", "FastAPI"],
}


# ---------------------------------------------------------------------------
# Integration test
# ---------------------------------------------------------------------------


async def test_pipeline_run_completes(db_session):
    with (
        patch(
            "app.pipeline.runner.fetch_serpapi", new_callable=AsyncMock
        ) as mock_serpapi,
        patch("app.pipeline.runner.fetch_gnews", new_callable=AsyncMock) as mock_gnews,
        patch(
            "app.pipeline.runner.fetch_rss_feeds", new_callable=AsyncMock
        ) as mock_rss,
        patch(
            "app.pipeline.runner.enrich_article_body", new_callable=AsyncMock
        ) as mock_enrich,
        patch(
            "app.pipeline.runner.extract_article", new_callable=AsyncMock
        ) as mock_extract,
        patch("app.pipeline.runner.draft_email", new_callable=AsyncMock) as mock_draft,
        patch("app.pipeline.runner.get_profile") as mock_profile,
    ):
        mock_serpapi.return_value = [sample_article]
        mock_gnews.return_value = []
        mock_rss.return_value = []
        mock_enrich.return_value = sample_article
        mock_extract.return_value = sample_extraction
        mock_draft.return_value = "Test email draft"
        mock_profile.return_value = _mock_profile

        pipeline_run = await run_pipeline(db_session)

    assert pipeline_run.status == "completed"
    assert pipeline_run.leads_created == 1
    assert pipeline_run.articles_fetched == 1
