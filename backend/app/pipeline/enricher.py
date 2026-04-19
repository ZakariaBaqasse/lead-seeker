import asyncio
import json
import logging

from langfuse import get_client
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import settings
from app.schemas.lead import EnrichmentResult, ExtractionResult
from app.pipeline.prompts import ENRICHMENT_PROMPT

logger = logging.getLogger(__name__)

ENRICHMENT_MODEL = "mistral-small-2603"


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
async def _search_tavily_with_retry(query: str, api_key: str) -> list[dict]:
    from tavily import AsyncTavilyClient

    client = AsyncTavilyClient(api_key=api_key)
    response = await client.search(query, search_depth="basic", max_results=5)
    results = response.get("results", [])
    return [
        {"title": r.get("title", ""), "url": r.get("url", ""), "content": r.get("content", "")}
        for r in results
    ]


async def _search_tavily(query: str, api_key: str) -> list[dict]:
    try:
        return await _search_tavily_with_retry(query, api_key)
    except Exception as e:
        logger.warning("Tavily search failed for query '%s': %s", query, e)
        return []


def _build_snippets_text(people_results: list[dict], company_results: list[dict]) -> str:
    parts = []
    for result in people_results + company_results:
        parts.append(
            f"Title: {result['title']}\nURL: {result['url']}\nContent: {result['content']}\n\n"
        )
    combined = "".join(parts)
    return combined[:4000]


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
async def _call_mistral_enrichment(snippets_text: str, company_name: str) -> dict:
    from mistralai.client import Mistral

    client = Mistral(api_key=settings.MISTRAL_API_KEY)
    messages = [
        {
            "role": "user",
            "content": ENRICHMENT_PROMPT.format(
                snippets_text=snippets_text, company_name=company_name
            ),
        }
    ]
    langfuse = get_client()
    with langfuse.start_as_current_observation(
        as_type="generation",
        name="enrichment-llm-call",
        model=ENRICHMENT_MODEL,
        input=messages,
    ) as gen:
        response = await client.chat.complete_async(
            model=ENRICHMENT_MODEL,
            messages=messages,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        gen.update(
            output=content,
            usage_details={
                "input": response.usage.prompt_tokens,
                "output": response.usage.completion_tokens,
            },
        )
    return json.loads(content)


async def _parse_enrichment(snippets_text: str, company_name: str) -> EnrichmentResult | None:
    try:
        data = await _call_mistral_enrichment(snippets_text, company_name)
        return EnrichmentResult.model_validate(data)
    except json.JSONDecodeError as e:
        logger.error("Enrichment JSON parse failed for '%s': %s", company_name, e)
        return None
    except Exception as e:
        logger.error("Enrichment LLM call failed for '%s': %s", company_name, e)
        return None


async def enrich_lead(extraction: ExtractionResult) -> EnrichmentResult | None:
    if not settings.TAVILY_API_KEY:
        logger.info("Enrichment skipped: TAVILY_API_KEY not configured")
        return None

    company_name = extraction.company_name
    api_key = settings.TAVILY_API_KEY
    people_query = f'"{company_name}" CTO OR founder OR CEO LinkedIn'
    company_query = f'"{company_name}" product technology stack employees'

    try:
        people_results, company_results = await asyncio.gather(
            _search_tavily(people_query, api_key),
            _search_tavily(company_query, api_key),
        )

        if not people_results and not company_results:
            logger.info("Enrichment skipped: no Tavily results for '%s'", company_name)
            return None

        snippets_text = _build_snippets_text(people_results, company_results)
        return await _parse_enrichment(snippets_text, company_name)
    except Exception as e:
        logger.error("Enrichment failed for '%s': %s", company_name, e)
        return None
