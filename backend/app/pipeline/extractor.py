import json
import logging

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import settings
from app.pipeline.sources import RawArticle
from app.schemas.lead import ExtractionResult

logger = logging.getLogger(__name__)

EXTRACTION_MODEL = "mistral-small-latest"

EXTRACTION_PROMPT = """You are a data extraction assistant. Given a news article about a startup funding event, extract the following fields as a JSON object. If you cannot confidently extract a field, use null. Set is_relevant=false if the article is not about a GenAI startup funding event.

Fields: company_name, company_domain, funding_amount, funding_round, funding_date (YYYY-MM-DD), employee_count_estimate (integer or null), region (Europe/USA/Other), country, sector (GenAI/Other), summary (2-3 sentences), is_relevant (bool).

Article:
{article_text}"""


def _build_article_text(article: RawArticle) -> str:
    parts = [article.headline]
    if article.body_snippet:
        parts.append(article.body_snippet)
    return "\n\n".join(parts)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
async def _call_mistral_extraction(article_text: str) -> dict:
    from mistralai import Mistral

    client = Mistral(api_key=settings.MISTRAL_API_KEY)
    response = await client.chat.complete_async(
        model=EXTRACTION_MODEL,
        messages=[{"role": "user", "content": EXTRACTION_PROMPT.format(article_text=article_text)}],
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content
    return json.loads(content)


async def extract_article(article: RawArticle) -> ExtractionResult | None:
    article_text = _build_article_text(article)
    try:
        data = await _call_mistral_extraction(article_text)
        if data is None:
            return None
        return ExtractionResult.model_validate(data)
    except Exception as e:
        logger.error("Extraction failed for article '%s': %s", article.headline[:80], e)
        return None
