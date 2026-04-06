import asyncio
import logging
import re
import xml.etree.ElementTree as ET

import httpx

from app.pipeline.sources import RawArticle

logger = logging.getLogger(__name__)

RSS_FEEDS = [
    ("https://techcrunch.com/feed/", "techcrunch"),
    ("https://sifted.eu/feed", "sifted"),
    ("https://www.eu-startups.com/feed/", "eu_startups"),
]

FUNDING_KEYWORDS = ["fund", "raise", "series", "seed", "invest", "round"]


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


def _has_funding_keywords(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in FUNDING_KEYWORDS)


async def _fetch_feed(url: str, source_name: str) -> list[RawArticle]:
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
            headline = (title_el.text or "") if title_el is not None else ""
            link = (link_el.text or "") if link_el is not None else ""
            snippet = _strip_html((desc_el.text or "") if desc_el is not None else "")
            if not headline or not link:
                continue
            if _has_funding_keywords(headline) or _has_funding_keywords(snippet):
                articles.append(
                    RawArticle(
                        headline=headline,
                        body_snippet=snippet,
                        url=link,
                        source_name=source_name,
                    )
                )
        logger.info("RSS %s: fetched %d matching articles", source_name, len(articles))
        return articles
    except Exception as e:
        logger.warning("RSS feed %s fetch failed: %s", source_name, e)
        return []


async def fetch_rss_feeds() -> list[RawArticle]:
    results = await asyncio.gather(*[_fetch_feed(url, name) for url, name in RSS_FEEDS])
    articles: list[RawArticle] = []
    for batch in results:
        articles.extend(batch)
    return articles
