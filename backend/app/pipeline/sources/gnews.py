import logging
from datetime import date, datetime, timezone

import httpx

from app.config import settings
from app.pipeline.sources import RawArticle

logger = logging.getLogger(__name__)

# In-memory rate limiting: reset counter at UTC midnight
_request_count = 0
_last_reset_date: date | None = None
DAILY_LIMIT = 80

GNEWS_URL = "https://gnews.io/api/v4/search"


def _reset_if_new_day() -> None:
    global _request_count, _last_reset_date
    today = datetime.now(timezone.utc).date()
    if _last_reset_date != today:
        _request_count = 0
        _last_reset_date = today


def _can_make_request() -> bool:
    _reset_if_new_day()
    return _request_count < DAILY_LIMIT


def _increment_counter() -> None:
    global _request_count
    _request_count += 1


async def fetch_gnews() -> list[RawArticle]:
    if not settings.GNEWS_API_KEY:
        logger.info("GNews API key not configured, skipping")
        return []
    if not _can_make_request():
        logger.warning("GNews daily limit (%d) reached, skipping", DAILY_LIMIT)
        return []

    articles = []
    queries = [
        "GenAI startup funding",
        "generative AI startup raised",
    ]
    async with httpx.AsyncClient(timeout=30.0) as client:
        for query in queries:
            if not _can_make_request():
                break
            try:
                _increment_counter()
                resp = await client.get(GNEWS_URL, params={
                    "q": query,
                    "lang": "en",
                    "country": "us",
                    "max": 10,
                    "apikey": settings.GNEWS_API_KEY,
                })
                resp.raise_for_status()
                data = resp.json()
                for article in data.get("articles", []):
                    url = article.get("url", "")
                    title = article.get("title", "")
                    description = article.get("description", "")
                    if title and url:
                        articles.append(RawArticle(
                            headline=title,
                            body_snippet=(description or "")[:500],
                            url=url,
                            source_name="gnews",
                        ))
            except httpx.TimeoutException:
                logger.warning("GNews API timed out for query: %s", query)
            except Exception as e:
                logger.warning("GNews API fetch failed: %s", e)
    return articles
