import logging
import yaml
from langfuse import get_client
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from app.config import settings
from app.pipeline.prompts import DRAFTING_PROMPT

logger = logging.getLogger(__name__)

DRAFTING_MODEL = "mistral-small-latest"


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
async def _call_mistral_drafting(prompt: str) -> str:
    from mistralai.client import Mistral

    client = Mistral(api_key=settings.MISTRAL_API_KEY)
    messages = [{"role": "user", "content": prompt}]
    langfuse = get_client()
    with langfuse.start_as_current_observation(
        as_type="generation",
        name="drafting-llm-call",
        model=DRAFTING_MODEL,
        input=messages,
    ) as gen:
        response = await client.chat.complete_async(
            model=DRAFTING_MODEL,
            messages=messages,
            # No response_format — free text output for email drafting
        )
        content = response.choices[0].message.content
        gen.update(
            output=content,
            usage_details={
                "input": response.usage.prompt_tokens,
                "output": response.usage.completion_tokens,
            },
        )
    return content


async def draft_email(lead_data: dict, profile: dict) -> str | None:
    """Generate a personalized cold outreach email for a lead.

    Returns the email text on success, or None if drafting fails after all retries.
    A None return does NOT prevent the lead from being stored — it is stored with email_draft=NULL.
    """
    logger.info(
        "Drafting email for company '%s' with profile '%s'",
        lead_data.get("company_name", "unknown"),
        profile.get("name", "unknown"),
    )
    try:
        profile_yaml_text = yaml.dump(
            profile, default_flow_style=False, allow_unicode=True
        )
        # Escape any literal braces in the YAML dump so str.format() doesn't
        # choke on profile content like "Uses {transformer} architecture"
        profile_yaml_text_safe = profile_yaml_text.replace("{", "{{").replace("}", "}}")
        prompt = DRAFTING_PROMPT.format(
            profile_yaml_as_text=profile_yaml_text_safe,
            company_name=lead_data.get("company_name", ""),
            cto_name=lead_data.get("cto_name") or "Unknown — address the founding team",
            product_description=lead_data.get("product_description") or lead_data.get("company_description") or lead_data.get("summary", ""),
            tech_stack=lead_data.get("tech_stack") or "Not available",
            summary=lead_data.get("company_description") or lead_data.get("summary", ""),
            funding_amount=lead_data.get("funding_amount", ""),
            funding_round=lead_data.get("funding_round", ""),
            funding_date=str(lead_data.get("funding_date", "")),
            country=lead_data.get("country") or lead_data.get("region", ""),
        )
        return await _call_mistral_drafting(prompt)
    except Exception as e:
        logger.error(
            "Email drafting failed for company '%s': %s",
            lead_data.get("company_name", "unknown"),
            e,
        )
        return None
