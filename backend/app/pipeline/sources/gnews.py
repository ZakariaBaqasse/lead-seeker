import logging
import threading
from datetime import date

import httpx

from app.config import settings
from app.pipeline.sources import RawArticle

logger = logging.getLogger(__name__)

QUERY = '"GenAI" AND ("seed" OR "Series A" OR "Series B" OR "funding")'
GNEWS_URL = "https://gnews.io/api/v4/search?q={query}&lang=en&country=us&max=10&apikey={key}"

MAX_DAILY_REQUESTS = 80

_counter_lock = threading.Lock()
_daily_count = 0
_count_date = date.today()


def _check_and_increment() -> bool:
    """Returns True if the request can proceed, False if daily limit is reached."""
    global _daily_count, _count_date
    with _counter_lock:
        today = date.today()
        if today != _count_date:
            _daily_count = 0
            _count_date = today
        if _daily_count >= MAX_DAILY_REQUESTS:
            return False
        _daily_count += 1
        return True


async def fetch_gnews() -> list[RawArticle]:
    if settings.GNEWS_API_KEY is None:
        logger.debug("GNews: GNEWS_API_KEY not set, skipping")
        return []

    if not _check_and_increment():
        logger.warning("GNews: daily request limit (%d) reached, skipping", MAX_DAILY_REQUESTS)
        return []

    url = GNEWS_URL.format(query=QUERY, key=settings.GNEWS_API_KEY)
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
        data = response.json()
        articles = []
        for item in data.get("articles", []):
            headline = item.get("title", "")
            link = item.get("url", "")
            snippet = item.get("content") or item.get("description") or ""
            if headline and link:
                articles.append(
                    RawArticle(
                        headline=headline,
                        body_snippet=snippet,
                        url=link,
                        source_name="gnews",
                    )
                )
        logger.info("GNews: fetched %d articles", len(articles))
        return articles
    except Exception as e:
        logger.warning("GNews fetch failed: %s", e)
        return []
