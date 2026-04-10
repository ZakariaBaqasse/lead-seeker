import logging
import xml.etree.ElementTree as ET

import httpx

from app.pipeline.sources import RawArticle

logger = logging.getLogger(__name__)

QUERIES = [
    '"GenAI" AND ("seed funding" OR "Series A" OR "Series B") AND "2025"',
    '"generative AI" AND ("raised" OR "funding") AND "startup" AND "2025"',
]
BASE_URL = "https://news.google.com/rss/search"


async def fetch_google_news() -> list[RawArticle]:
    articles = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        for query in QUERIES:
            try:
                resp = await client.get(BASE_URL, params={"q": query, "hl": "en-US", "gl": "US", "ceid": "US:en"})
                resp.raise_for_status()
                root = ET.fromstring(resp.text)
                for item in root.findall(".//item"):
                    title = item.findtext("title") or ""
                    link = item.findtext("link") or ""
                    description = item.findtext("description") or ""
                    if title and link:
                        articles.append(RawArticle(
                            headline=title,
                            body_snippet=description[:500],
                            url=link,
                            source_name="google_news",
                        ))
            except httpx.TimeoutException:
                logger.warning("Google News RSS timed out for query: %s", query)
            except Exception as e:
                logger.warning("Google News RSS fetch failed: %s", e)
    return articles
