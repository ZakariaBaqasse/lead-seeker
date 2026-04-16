import logging
import re
import xml.etree.ElementTree as ET

import httpx

from app.pipeline.sources import RawArticle

logger = logging.getLogger(__name__)

# RSS_FEEDS now includes a tier: "funding" or "general"
# Funding-tier feeds: already curated for startup funding (only check funding signal)
# General-tier feeds: broad tech news (require both AI and funding signals)
RSS_FEEDS = [
    ("https://techcrunch.com/feed/", "techcrunch", "general"),
    ("https://sifted.eu/feed", "sifted", "funding"),
    ("https://www.eu-startups.com/feed/", "eu_startups", "funding"),
    ("https://tech.eu/feed", "tech_eu", "funding"),
    ("https://venturebeat.com/feed/", "venturebeat", "general"),
    ("https://techfundingnews.com/feed/", "techfundingnews", "funding"),
    ("https://news.crunchbase.com/feed/", "crunchbase_news", "funding"),
]

# Expanded AI keywords for broader matching
AI_KEYWORDS = [
    "artificial intelligence",
    "machine learning",
    "llm",
    "deep learning",
    "foundation model",
    "large language model",
    "genai",
    "generative ai",
    "generative artificial intelligence",
]

# Word-boundary regex for short terms like "AI" to avoid matching "said", "email", etc.
AI_WORD_BOUNDARY_KEYWORDS = [
    r"\bai\b",  # Standalone "AI"
]

# Expanded funding keywords
FUNDING_KEYWORDS = [
    "funding",
    "raises",
    "raised",
    "seed",
    "series a",
    "series b",
    "series c",
    "series d",
    "secures",
    "investment",
    "round",
    "backed",
    "million",
    "venture",
    "capital",
    "pre-seed",
]

# Compile regex patterns for word-boundary matching
AI_WORD_BOUNDARY_PATTERNS = [
    re.compile(pattern, re.IGNORECASE) for pattern in AI_WORD_BOUNDARY_KEYWORDS
]


def _has_ai_signal(text: str, categories: list[str]) -> bool:
    """Check if text or categories contain AI-related terms."""
    lower = text.lower()

    # Check substring keywords
    if any(kw in lower for kw in AI_KEYWORDS):
        return True

    # Check word-boundary keywords (e.g., "AI")
    if any(pattern.search(lower) for pattern in AI_WORD_BOUNDARY_PATTERNS):
        return True

    # Check categories
    categories_lower = [cat.lower() for cat in categories]
    if any(kw in cat for cat in categories_lower for kw in AI_KEYWORDS):
        return True

    if any(
        pattern.search(cat)
        for cat in categories_lower
        for pattern in AI_WORD_BOUNDARY_PATTERNS
    ):
        return True

    return False


def _has_funding_signal(text: str, categories: list[str]) -> bool:
    """Check if text or categories contain funding-related terms."""
    lower = text.lower()

    # Check substring keywords
    if any(kw in lower for kw in FUNDING_KEYWORDS):
        return True

    # Check categories
    categories_lower = [cat.lower() for cat in categories]
    if any(kw in cat for cat in categories_lower for kw in FUNDING_KEYWORDS):
        return True

    return False


def _is_relevant(text: str, categories: list[str], tier: str) -> bool:
    """
    Determine if an article is relevant based on tier.

    Args:
        text: Combined title + description text
        categories: RSS category tags
        tier: "funding" or "general"

    Returns:
        True if article should be processed
    """
    if tier == "funding":
        # Funding-tier feeds: only check for funding signal
        # AI filtering delegated to LLM extractor
        return _has_funding_signal(text, categories)
    elif tier == "general":
        # General-tier feeds: require both AI and funding signals
        return _has_ai_signal(text, categories) and _has_funding_signal(
            text, categories
        )
    else:
        logger.warning("Unknown feed tier: %s", tier)
        return False


async def fetch_rss_feeds() -> list[RawArticle]:
    articles = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        for feed_url, source_name, tier in RSS_FEEDS:
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

                    # Extract category tags from RSS item
                    categories = []
                    for category_elem in item.findall("category"):
                        cat_text = category_elem.text
                        if cat_text:
                            categories.append(cat_text)

                    combined = f"{title} {description}"
                    if _is_relevant(combined, categories, tier):
                        articles.append(
                            RawArticle(
                                headline=title,
                                body_snippet=description[:500],
                                url=link,
                                source_name=source_name,
                            )
                        )
            except httpx.TimeoutException:
                logger.warning("RSS feed timed out: %s", feed_url)
            except Exception as e:
                logger.warning("RSS feed fetch failed (%s): %s", feed_url, e)
    return articles
