import logging
import xml.etree.ElementTree as ET

import httpx

from app.pipeline.sources import RawArticle

logger = logging.getLogger(__name__)

RSS_FEEDS = [
    ("https://techcrunch.com/feed/", "techcrunch"),
    ("https://sifted.eu/feed", "sifted"),
    ("https://www.eu-startups.com/feed/", "eu_startups"),
]

FUNDING_KEYWORDS = ["funding", "raises", "raised", "seed", "series a", "series b", "investment", "ai", "genai", "generative"]


def _is_relevant(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in FUNDING_KEYWORDS)


async def fetch_rss_feeds() -> list[RawArticle]:
    articles = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        for feed_url, source_name in RSS_FEEDS:
            try:
                resp = await client.get(feed_url)
                resp.raise_for_status()
                root = ET.fromstring(resp.content)
                for item in root.findall(".//item"):
                    title = item.findtext("title") or ""
                    link = item.findtext("link") or ""
                    description = item.findtext("description") or ""
                    if not title or not link:
                        continue
                    combined = f"{title} {description}"
                    if _is_relevant(combined):
                        articles.append(RawArticle(
                            headline=title,
                            body_snippet=description[:500],
                            url=link,
                            source_name=source_name,
                        ))
            except httpx.TimeoutException:
                logger.warning("RSS feed timed out: %s", feed_url)
            except Exception as e:
                logger.warning("RSS feed fetch failed (%s): %s", feed_url, e)
    return articles
