import logging

import httpx

from app.pipeline.sources import RawArticle

logger = logging.getLogger(__name__)

JINA_READER_PREFIX = "https://r.jina.ai/"
# ≤5 concurrent requests (20 RPM free tier)


async def enrich_article_body(article: RawArticle) -> RawArticle:
    """Fetch article content via Jina Reader (free, handles JS rendering).

    Returns a new RawArticle with body_snippet replaced by the extracted text.
    Falls back to the original snippet silently on any failure.
    """
    try:
        jina_url = f"{JINA_READER_PREFIX}{article.url}"
        async with httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "Accept": "text/plain",
                "User-Agent": "Mozilla/5.0 (compatible; lead-seeker/1.0)",
            },
        ) as client:
            resp = await client.get(jina_url)
            resp.raise_for_status()
            text = resp.text

        if text and len(text.strip()) > 100:
            logger.debug("Enriched body for: %s", article.headline[:80])
            return RawArticle(
                headline=article.headline,
                body_snippet=text,
                url=article.url,
                source_name=article.source_name,
            )

    except httpx.TimeoutException:
        logger.warning("Jina Reader timed out: %s", article.url)
    except Exception as e:
        logger.warning("Jina Reader failed for %s: %s", article.url, e)

    return article
