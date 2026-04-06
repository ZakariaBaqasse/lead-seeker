import logging
import re
import urllib.parse
import xml.etree.ElementTree as ET

import httpx

from app.pipeline.sources import RawArticle

logger = logging.getLogger(__name__)

QUERY = '"GenAI" AND ("seed" OR "Series A" OR "Series B" OR "funding")'
RSS_URL = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"


async def fetch_google_news() -> list[RawArticle]:
    url = RSS_URL.format(query=urllib.parse.quote(QUERY))
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
        root = ET.fromstring(response.text)
        articles = []
        for item in root.findall(".//item"):
            title_el = item.find("title")
            link_el = item.find("link")
            desc_el = item.find("description")
            if title_el is None or link_el is None:
                continue
            headline = title_el.text or ""
            link = link_el.text or ""
            snippet = _strip_html(desc_el.text or "") if desc_el is not None else ""
            if headline and link:
                articles.append(
                    RawArticle(
                        headline=headline,
                        body_snippet=snippet,
                        url=link,
                        source_name="google_news",
                    )
                )
        logger.info("Google News: fetched %d articles", len(articles))
        return articles
    except Exception as e:
        logger.warning("Google News fetch failed: %s", e)
        return []


def _strip_html(text: str) -> str:
    """Very simple HTML tag stripper."""
    return re.sub(r"<[^>]+>", "", text).strip()
