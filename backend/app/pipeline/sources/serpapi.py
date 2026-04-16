import logging
from datetime import timedelta, date
import httpx

from app.config import settings
from app.pipeline.sources import RawArticle

logger = logging.getLogger(__name__)

SERPAPI_URL = "https://serpapi.com/search"


def _build_queries() -> list[str]:
    """Build queries with a rolling 12-month after: date to avoid stale year hardcodes."""
    cutoff = (date.today() - timedelta(days=365)).isoformat()
    return [
        f'"GenAI" AND ("seed funding" OR "Series A" OR "Series B") after:{cutoff}',
        f'"generative AI" AND ("raised" OR "funding") AND "startup" after:{cutoff}',
    ]


async def fetch_serpapi() -> list[RawArticle]:
    if not settings.SERPAPI_API_KEY:
        logger.info("SerpAPI key not configured, skipping")
        return []

    articles = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        for query in _build_queries():
            try:
                resp = await client.get(
                    SERPAPI_URL,
                    params={
                        "engine": "google_news",
                        "q": query,
                        "hl": "en",
                        "gl": "us",
                        "tbs": "qdr:y",  # past 12 months
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
