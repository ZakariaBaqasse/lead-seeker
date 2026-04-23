import logging
import httpx

from app.config import settings
from app.pipeline.sources import RawArticle

logger = logging.getLogger(__name__)

SERPAPI_URL = "https://serpapi.com/search"

# Each entry is (query, gl) where gl is the Google country code for result localisation.
# Using qdr:d at call time — these strings must NOT include an after: date.
_QUERIES: list[tuple[str, str]] = [
    # US-focused — broad AI funding
    ('"AI startup" AND ("seed" OR "Series A" OR "Series B") AND "raises"', "us"),
    ('"generative AI" AND ("seed" OR "Series A" OR "Series B") AND "funding"', "us"),
    ('"LLM" OR "large language model" AND "startup" AND ("raises" OR "funding")', "us"),
    ('"machine learning" AND "startup" AND ("raises" OR "Series A" OR "seed")', "us"),
    # EU-focused
    (
        '"AI startup" AND ("seed" OR "Series A" OR "Series B") AND ("Europe" OR "EU")',
        "gb",
    ),
    (
        '"artificial intelligence" AND "startup" AND "funding" AND ("Europe" OR "EU" OR "UK")',
        "gb",
    ),
    (
        '"GenAI" OR "generative AI" AND "raises" AND ("Europe" OR "France" OR "Germany" OR "UK")',
        "gb",
    ),
]


def _build_queries() -> list[tuple[str, str]]:
    return _QUERIES


async def fetch_serpapi() -> list[RawArticle]:
    if not settings.SERPAPI_API_KEY:
        logger.info("SerpAPI key not configured, skipping")
        return []

    articles = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        for query, gl in _build_queries():
            try:
                resp = await client.get(
                    SERPAPI_URL,
                    params={
                        "engine": "google_news",
                        "q": query,
                        "hl": "en",
                        "gl": gl,
                        "tbs": "qdr:d",  # past 24 hours — ensures fresh results on each daily run
                        "api_key": settings.SERPAPI_API_KEY,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                news_results = data.get("news_results", [])
                logger.info(
                    "SerpAPI returned %d results for query: %s",
                    len(news_results),
                    query,
                )
                for item in news_results:
                    title = item.get("title", "")
                    link = item.get("link", "")
                    snippet = item.get("snippet", "")
                    if title and link:
                        articles.append(
                            RawArticle(
                                headline=title,
                                body_snippet=snippet[:500],
                                url=link,
                                source_name="serpapi",
                            )
                        )
            except httpx.TimeoutException:
                logger.warning("SerpAPI timed out for query: %s", query)
            except Exception as e:
                logger.warning("SerpAPI fetch failed: %s", e)

    return articles
