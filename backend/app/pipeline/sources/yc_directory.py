import logging

import httpx

from app.pipeline.sources import RawArticle

logger = logging.getLogger(__name__)

YC_API_URL = (
    "https://api.ycombinator.com/v0.1/companies"
    "?industry=Artificial+Intelligence+%2F+Machine+Learning&batch=&limit=100"
)

RECENT_BATCHES = {"S24", "W24", "S25", "W25", "W26", "S26"}
AI_KEYWORDS = ["genai", "llm", "large language", "generative ai", "ai", "machine learning"]


def _is_ai_related(company: dict) -> bool:
    text = (
        (company.get("one_liner") or "") + " " + (company.get("long_description") or "")
    ).lower()
    return any(kw in text for kw in AI_KEYWORDS)


def _is_recent(company: dict) -> bool:
    batch = company.get("batch") or ""
    return batch in RECENT_BATCHES


async def fetch_yc_directory() -> list[RawArticle]:
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(YC_API_URL)
            response.raise_for_status()
        data = response.json()
        companies = data if isinstance(data, list) else data.get("companies", [])
        articles = []
        for company in companies:
            if not _is_recent(company):
                continue
            if not _is_ai_related(company):
                continue
            name = company.get("name", "")
            website = company.get("website") or company.get("url") or ""
            description = company.get("long_description") or company.get("one_liner") or ""
            if name:
                articles.append(
                    RawArticle(
                        headline=name,
                        body_snippet=description,
                        url=website,
                        source_name="yc_directory",
                    )
                )
        logger.info("YC Directory: fetched %d companies", len(articles))
        return articles
    except Exception as e:
        logger.warning("YC Directory fetch failed: %s", e)
        return []
