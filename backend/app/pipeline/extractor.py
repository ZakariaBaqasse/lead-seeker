import json
import logging

from tenacity import retry, stop_after_attempt, wait_exponential, RetryError
from mistralai.client import Mistral
from app.config import settings
from app.pipeline.sources import RawArticle
from app.schemas.pipeline import ExtractionResult

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """\
You are a data extraction assistant. Given a news article about a startup funding event, \
extract the following fields as a JSON object. If you cannot confidently extract a field, \
use null. Set is_relevant=false if the article is not about a GenAI startup funding event.

Fields: company_name, company_domain, funding_amount, funding_round, funding_date \
(YYYY-MM-DD), employee_count_estimate (integer or null), region (Europe/USA/Other), \
country, sector (GenAI/Other), summary (2-3 sentences), is_relevant (bool).

Article:
{article_text}"""


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def _call_mistral_extraction(article_text: str) -> str:
    """Call Mistral API for extraction. Returns raw JSON string."""
    client = Mistral(api_key=settings.MISTRAL_API_KEY)
    response = await client.chat.complete_async(
        model="mistral-small-latest",
        messages=[{"role": "user", "content": EXTRACTION_PROMPT.format(article_text=article_text)}],
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content


async def extract_article(article: RawArticle) -> ExtractionResult | None:
    """Extract structured data from a raw article using Mistral API.

    Returns ExtractionResult or None if extraction fails or article is irrelevant.
    """
    article_text = f"{article.headline}\n\n{article.body_snippet}"
    try:
        raw_json = await _call_mistral_extraction(article_text)
        data = json.loads(raw_json)
        result = ExtractionResult(**{k: data.get(k) for k in ExtractionResult.model_fields})
        return result
    except RetryError as e:
        logger.error("Mistral extraction failed after 3 attempts for %s: %s", article.url, e)
        return None
    except json.JSONDecodeError as e:
        logger.error("JSON parse error for article %s: %s", article.url, e)
        return None
    except Exception as e:
        logger.error("Extraction failed for article %s: %s", article.url, e)
        return None
