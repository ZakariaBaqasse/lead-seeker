"""Hacker News source via the free Algolia search API.

Searches for HN stories mentioning AI startup funding published in the past 24 hours.
No API key required.
"""

import logging
import time

import httpx

from app.pipeline.sources import RawArticle

logger = logging.getLogger(__name__)

ALGOLIA_URL = "https://hn.algolia.com/api/v1/search"

_QUERIES = [
    "AI startup funding",
    "generative AI raises",
    "LLM startup Series",
    "machine learning startup seed",
]


async def fetch_hn() -> list[RawArticle]:
    """Fetch recent HN stories about AI startup funding from the past 24 hours."""
    cutoff = int(time.time()) - 86400  # 24 hours ago
    articles: list[RawArticle] = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        for query in _QUERIES:
            try:
                resp = await client.get(
                    ALGOLIA_URL,
                    params={
                        "query": query,
                        "tags": "story",
                        "numericFilters": f"created_at_i>{cutoff}",
                        "hitsPerPage": 20,
                    },
                )
                resp.raise_for_status()
                hits = resp.json().get("hits", [])
                logger.info(
                    "HN Algolia returned %d hits for query: %s", len(hits), query
                )
                for hit in hits:
                    title = hit.get("title", "")
                    # Prefer the external URL; fall back to the HN discussion page
                    url = (
                        hit.get("url")
                        or f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}"
                    )
                    story_text = hit.get("story_text") or ""
                    if title and url:
                        articles.append(
                            RawArticle(
                                headline=title,
                                body_snippet=story_text[:500],
                                url=url,
                                source_name="hackernews",
                            )
                        )
            except httpx.TimeoutException:
                logger.warning("HN Algolia timed out for query: %s", query)
            except Exception as e:
                logger.warning("HN Algolia fetch failed: %s", e)

    return articles
