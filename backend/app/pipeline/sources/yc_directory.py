import logging

import httpx

from app.pipeline.sources import RawArticle

logger = logging.getLogger(__name__)

YC_SEARCH_URL = "https://45bwzj1sgc-dsn.algolia.net/1/indexes/*/queries"
YC_APP_ID = "45bwzj1sgc"
YC_API_KEY = "be4effc9bcba2f8f56ac997f0a3b32d3"  # public read-only key from YC website


async def fetch_yc_directory() -> list[RawArticle]:
    articles = []
    try:
        payload = {
            "requests": [{
                "indexName": "YCCompany_production",
                "params": "query=AI&filters=top_company%3Atrue%20OR%20isHiring%3Atrue&hitsPerPage=50&attributesToRetrieve=name,slug,one_liner,long_description,batch,industries,regions,team_size,website",
            }]
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                YC_SEARCH_URL,
                json=payload,
                headers={
                    "X-Algolia-Application-Id": YC_APP_ID,
                    "X-Algolia-API-Key": YC_API_KEY,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            hits = data.get("results", [{}])[0].get("hits", [])
            for hit in hits:
                name = hit.get("name", "")
                one_liner = hit.get("one_liner", "")
                description = hit.get("long_description", one_liner)
                slug = hit.get("slug", "")
                url = f"https://www.ycombinator.com/companies/{slug}" if slug else ""
                industries = hit.get("industries", [])
                if not name or not url:
                    continue
                # Only include AI-related companies — check per-item to avoid substring false positives
                # e.g. "ai" in "retail" is True on concatenated string
                industry_lower = [i.lower() for i in industries]
                if not any(
                    "artificial intelligence" in i or i == "ai" or "generative ai" in i
                    for i in industry_lower
                ):
                    continue
                articles.append(RawArticle(
                    headline=f"{name}: {one_liner}",
                    body_snippet=(description or one_liner or "")[:500],
                    url=url,
                    source_name="yc_directory",
                ))
    except httpx.TimeoutException:
        logger.warning("YC directory fetch timed out")
    except Exception as e:
        logger.warning("YC directory fetch failed: %s", e)
    return articles
