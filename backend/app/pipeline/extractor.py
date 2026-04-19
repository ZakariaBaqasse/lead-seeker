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
from app.pipeline.sources import RawArticle
from app.schemas.lead import ExtractionResult
from app.pipeline.prompts import EXTRACTION_PROMPT

logger = logging.getLogger(__name__)

EXTRACTION_MODEL = "mistral-small-2603"


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
    from mistralai.client import Mistral

    client = Mistral(api_key=settings.MISTRAL_API_KEY)
    messages = [
        {
            "role": "user",
            "content": EXTRACTION_PROMPT.format(article_text=article_text),
        }
    ]
    langfuse = get_client()
    with langfuse.start_as_current_observation(
        as_type="generation",
        name="extraction-llm-call",
        model=EXTRACTION_MODEL,
        input=messages,
    ) as gen:
        response = await client.chat.complete_async(
            model=EXTRACTION_MODEL,
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


async def extract_article(article: RawArticle) -> ExtractionResult | None:
    logger.info("Extracting data from article: %s", article.url)
    article_text = _build_article_text(article)
    try:
        data = await _call_mistral_extraction(article_text)
        if data is None:
            return None
        return ExtractionResult.model_validate(data)
    except Exception as e:
        logger.error("Extraction failed for article '%s': %s", article.url, e)
        return None
