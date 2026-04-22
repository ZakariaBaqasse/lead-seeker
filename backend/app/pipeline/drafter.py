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
from app.pipeline.prompts import (
    DRAFTING_PROMPT,
    CRITIQUE_REWRITE_PROMPT,
    FOLLOW_UP_DRAFTING_PROMPT,
    FOLLOW_UP_CRITIQUE_PROMPT,
)

logger = logging.getLogger(__name__)

DRAFTING_MODEL = "mistral-small-latest"
CRITIQUE_MODEL = "mistral-medium-latest"


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
async def _call_mistral_drafting(
    prompt: str,
    *,
    model: str = DRAFTING_MODEL,
    observation_name: str = "drafting-llm-call",
) -> str:
    from mistralai.client import Mistral

    client = Mistral(api_key=settings.MISTRAL_API_KEY)
    messages = [{"role": "user", "content": prompt}]
    langfuse = get_client()
    with langfuse.start_as_current_observation(
        as_type="generation",
        name=observation_name,
        model=model,
        input=messages,
    ) as gen:
        response = await client.chat.complete_async(
            model=model,
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
        product_description = (
            lead_data.get("product_description")
            or lead_data.get("company_description")
            or lead_data.get("summary", "")
        )
        prompt = DRAFTING_PROMPT.format(
            profile_yaml_as_text=profile_yaml_text_safe,
            company_name=lead_data.get("company_name", ""),
            cto_name=lead_data.get("cto_name") or "Unknown — address the founding team",
            product_description=product_description,
            tech_stack=lead_data.get("tech_stack") or "Not available",
            summary=lead_data.get("company_description")
            or lead_data.get("summary", ""),
            funding_amount=lead_data.get("funding_amount", ""),
            funding_round=lead_data.get("funding_round", ""),
            funding_date=str(lead_data.get("funding_date", "")),
            country=lead_data.get("country") or lead_data.get("region", ""),
        )
        initial_draft = await _call_mistral_drafting(
            prompt, observation_name="drafting-llm-call"
        )

        critique_prompt = CRITIQUE_REWRITE_PROMPT.format(
            company_name=lead_data.get("company_name", ""),
            product_description=product_description,
            cto_name=lead_data.get("cto_name") or "Unknown",
            tech_stack=lead_data.get("tech_stack") or "Not available",
            summary=lead_data.get("company_description")
            or lead_data.get("summary", ""),
            funding_amount=lead_data.get("funding_amount", ""),
            funding_round=lead_data.get("funding_round", ""),
            funding_date=str(lead_data.get("funding_date", "")),
            country=lead_data.get("country") or lead_data.get("region", ""),
            profile_yaml_as_text=profile_yaml_text_safe,
            email_draft=initial_draft,
        )
        return await _call_mistral_drafting(
            critique_prompt,
            model=CRITIQUE_MODEL,
            observation_name="critique-rewrite-llm-call",
        )
    except Exception as e:
        logger.error(
            "Email drafting failed for company '%s': %s",
            lead_data.get("company_name", "unknown"),
            e,
        )
        return None


async def draft_follow_up_email(
    lead_data: dict,
    profile: dict,
    follow_up_number: int,
) -> str | None:
    """Generate a follow-up email draft.

    Returns the draft text or None on failure.
    follow_up_number is 1-based: 1 = first follow-up, 2 = second follow-up.
    """
    logger.info(
        "Drafting follow-up %d for company '%s'",
        follow_up_number,
        lead_data.get("company_name", "unknown"),
    )
    try:
        profile_yaml_text = yaml.dump(
            profile, default_flow_style=False, allow_unicode=True
        )
        profile_yaml_text_safe = profile_yaml_text.replace("{", "{{").replace("}", "}}")

        product_description = (
            lead_data.get("product_description")
            or lead_data.get("company_description")
            or lead_data.get("summary", "")
        )
        original_draft = lead_data.get("email_draft") or ""

        prompt = FOLLOW_UP_DRAFTING_PROMPT.format(
            company_name=lead_data.get("company_name", ""),
            cto_name=lead_data.get("cto_name") or "the founding team",
            product_description=product_description,
            tech_stack=lead_data.get("tech_stack") or "Not available",
            follow_up_number=follow_up_number,
            original_email_draft=original_draft,
            profile_yaml_as_text=profile_yaml_text_safe,
        )
        initial_draft = await _call_mistral_drafting(
            prompt, observation_name="followup-drafting-llm-call"
        )

        critique_prompt = FOLLOW_UP_CRITIQUE_PROMPT.format(
            follow_up_number=follow_up_number,
            original_email_draft=original_draft,
            follow_up_draft=initial_draft,
            company_name=lead_data.get("company_name", ""),
            profile_yaml_as_text=profile_yaml_text_safe,
        )
        return await _call_mistral_drafting(
            critique_prompt,
            model=CRITIQUE_MODEL,
            observation_name="followup-critique-rewrite-llm-call",
        )
    except Exception as e:
        logger.error(
            "Follow-up drafting failed for company '%s': %s",
            lead_data.get("company_name", "unknown"),
            e,
        )
        return None
