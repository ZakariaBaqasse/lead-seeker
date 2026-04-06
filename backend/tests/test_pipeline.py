import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from app.pipeline.sources import RawArticle
from app.schemas.pipeline import ExtractionResult
from datetime import date, timedelta


def make_extraction(company_name="Test AI", **kwargs) -> ExtractionResult:
    today = date.today()
    recent = (today - timedelta(days=30)).isoformat()
    return ExtractionResult(
        company_name=company_name,
        company_domain=f"{company_name.lower().replace(' ', '')}.ai",
        funding_amount="$5M",
        funding_round="Seed",
        funding_date=recent,
        employee_count_estimate=20,
        region="Europe",
        country="Germany",
        sector="GenAI",
        summary="Test AI company",
        is_relevant=True,
        **kwargs,
    )


class TestDedupeByUrl:
    def test_removes_duplicates(self):
        from app.pipeline.sources import dedupe_by_url
        articles = [
            RawArticle("A", "b", "http://x.com", "s1"),
            RawArticle("C", "d", "http://x.com", "s2"),  # duplicate URL
            RawArticle("E", "f", "http://y.com", "s3"),
        ]
        result = dedupe_by_url(articles)
        assert len(result) == 2
        assert result[0].url == "http://x.com"
        assert result[1].url == "http://y.com"

    def test_empty_list(self):
        from app.pipeline.sources import dedupe_by_url
        assert dedupe_by_url([]) == []

    def test_no_duplicates(self):
        from app.pipeline.sources import dedupe_by_url
        articles = [RawArticle("A", "b", f"http://url{i}.com", "s") for i in range(5)]
        assert len(dedupe_by_url(articles)) == 5


class TestProfileLoader:
    def test_valid_profile_loads(self):
        from app.profile import _validate_profile
        valid = {
            "name": "Test User",
            "title": "Engineer",
            "pitch": "I build things.",
            "projects": [{"name": "P1", "description": "desc", "video_url": "http://v.com", "tags": ["Python"]}],
            "skills": ["Python"],
        }
        _validate_profile(valid)  # should not raise

    def test_missing_name_raises(self):
        from app.profile import _validate_profile
        with pytest.raises(ValueError, match="name"):
            _validate_profile({"title": "T", "pitch": "P", "projects": [], "skills": []})

    def test_empty_projects_raises(self):
        from app.profile import _validate_profile
        with pytest.raises(ValueError, match="projects"):
            _validate_profile({"name": "N", "title": "T", "pitch": "P", "projects": [], "skills": []})

    def test_project_missing_field_raises(self):
        from app.profile import _validate_profile
        with pytest.raises(ValueError, match="video_url"):
            _validate_profile({
                "name": "N", "title": "T", "pitch": "P",
                "projects": [{"name": "P1", "description": "d", "tags": []}],
                "skills": [],
            })

    def test_lru_cache_returns_same_object(self, tmp_path, monkeypatch):
        """get_profile() should return cached object on second call."""
        import yaml
        from app import profile as profile_module

        profile_data = {
            "name": "Test",
            "title": "Dev",
            "pitch": "pitch",
            "projects": [{"name": "P", "description": "d", "video_url": "u", "tags": ["t"]}],
            "skills": ["Python"],
        }
        profile_file = tmp_path / "profile.yaml"
        profile_file.write_text(yaml.dump(profile_data))
        monkeypatch.setattr(profile_module, "PROFILE_PATH", str(profile_file))
        profile_module.get_profile.cache_clear()

        first = profile_module.get_profile()
        second = profile_module.get_profile()
        assert first is second  # same cached object

        profile_module.get_profile.cache_clear()  # cleanup


@pytest.mark.asyncio
class TestPipelineRunner:
    async def test_run_pipeline_creates_leads(self):
        """Full pipeline with mocked sources + Mistral creates leads."""
        article = RawArticle("Test AI raises $5M", "Body text here.", "http://test.com/article", "test")
        extraction = make_extraction("Test AI Corp")

        with (
            patch("app.pipeline.runner.fetch_google_news", new=AsyncMock(return_value=[article])),
            patch("app.pipeline.runner.fetch_gnews", new=AsyncMock(return_value=[])),
            patch("app.pipeline.runner.fetch_yc_directory", new=AsyncMock(return_value=[])),
            patch("app.pipeline.runner.fetch_rss_feeds", new=AsyncMock(return_value=[])),
            patch("app.pipeline.runner.extract_article", new=AsyncMock(return_value=extraction)),
            patch("app.pipeline.runner.is_duplicate", new=AsyncMock(return_value=False)),
            patch("app.pipeline.runner.draft_email", new=AsyncMock(return_value="Dear CTO, ...")),
            patch("app.pipeline.runner.get_profile", return_value={"name": "Test", "title": "Dev", "pitch": "p", "projects": [], "skills": []}),
            patch("app.pipeline.runner.AsyncSessionLocal") as mock_session_factory,
        ):
            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=False)
            mock_session.flush = AsyncMock()
            mock_session.commit = AsyncMock()
            mock_session.add = MagicMock()
            mock_session_factory.return_value = mock_session

            from app.pipeline.runner import run_pipeline
            await run_pipeline()

            assert mock_session.add.called
            assert mock_session.commit.called

    async def test_failed_extraction_does_not_abort_run(self):
        """If extraction returns None, pipeline continues."""
        article = RawArticle("Bad article", "", "http://bad.com", "test")

        with (
            patch("app.pipeline.runner.fetch_google_news", new=AsyncMock(return_value=[article])),
            patch("app.pipeline.runner.fetch_gnews", new=AsyncMock(return_value=[])),
            patch("app.pipeline.runner.fetch_yc_directory", new=AsyncMock(return_value=[])),
            patch("app.pipeline.runner.fetch_rss_feeds", new=AsyncMock(return_value=[])),
            patch("app.pipeline.runner.extract_article", new=AsyncMock(return_value=None)),
            patch("app.pipeline.runner.AsyncSessionLocal") as mock_session_factory,
        ):
            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=False)
            mock_session.flush = AsyncMock()
            mock_session.commit = AsyncMock()
            mock_session.add = MagicMock()
            mock_session_factory.return_value = mock_session

            from app.pipeline.runner import run_pipeline
            await run_pipeline()
            assert mock_session.commit.called

    async def test_draft_failure_lead_still_stored(self):
        """If email drafting fails, lead is still saved (email_draft=None)."""
        article = RawArticle("Good article", "Content.", "http://good.com", "test")
        extraction = make_extraction("No Draft Co")

        with (
            patch("app.pipeline.runner.fetch_google_news", new=AsyncMock(return_value=[article])),
            patch("app.pipeline.runner.fetch_gnews", new=AsyncMock(return_value=[])),
            patch("app.pipeline.runner.fetch_yc_directory", new=AsyncMock(return_value=[])),
            patch("app.pipeline.runner.fetch_rss_feeds", new=AsyncMock(return_value=[])),
            patch("app.pipeline.runner.extract_article", new=AsyncMock(return_value=extraction)),
            patch("app.pipeline.runner.is_duplicate", new=AsyncMock(return_value=False)),
            patch("app.pipeline.runner.draft_email", new=AsyncMock(return_value=None)),
            patch("app.pipeline.runner.get_profile", return_value={"name": "T", "title": "D", "pitch": "p", "projects": [], "skills": []}),
            patch("app.pipeline.runner.AsyncSessionLocal") as mock_session_factory,
        ):
            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=False)
            mock_session.flush = AsyncMock()
            mock_session.commit = AsyncMock()
            mock_session.add = MagicMock()
            mock_session_factory.return_value = mock_session

            from app.pipeline.runner import run_pipeline
            await run_pipeline()
            # Lead should still be added even if drafting fails
            assert mock_session.add.called
