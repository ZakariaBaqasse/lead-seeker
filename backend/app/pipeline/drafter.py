import logging

import yaml
from mistralai.client import Mistral
from tenacity import RetryError, retry, stop_after_attempt, wait_exponential

from app.config import settings

logger = logging.getLogger(__name__)

DRAFT_PROMPT = """\
You are writing a cold outreach email on behalf of {name}, a {title}.

Freelancer profile:
{profile_yaml_as_text}

Target company:
- Name: {company_name}
- Recent news: {summary}
- Funding: {funding_amount} {funding_round} on {funding_date}
- Region: {country}

Choose the single most relevant portfolio project from the profile above based on the
company's industry. Write a concise, direct cold email (150–200 words) that:
1. Opens by referencing the company's recent funding news
2. Briefly introduces the freelancer and their most relevant project with the demo video link
3. Proposes a time-bound engagement (e.g., 3-month contract)
4. Ends with a clear, low-friction call to action

Do not use filler phrases like "I hope this finds you well". Be direct."""


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def _call_mistral_draft(prompt: str) -> str:
    """Call Mistral API for email drafting. Returns free-text response."""
    client = Mistral(api_key=settings.MISTRAL_API_KEY)
    response = await client.chat.complete_async(
        model="mistral-small-latest",
        messages=[{"role": "user", "content": prompt}],
        timeout_ms=30000,
    )
    return response.choices[0].message.content


async def draft_email(lead_data: dict, profile: dict) -> str | None:
    """Generate a personalized outreach email draft. Returns draft string or None on failure."""
    profile_text = yaml.dump(profile, default_flow_style=False, allow_unicode=True)
    prompt = DRAFT_PROMPT.format(
        name=profile.get("name", ""),
        title=profile.get("title", ""),
        profile_yaml_as_text=profile_text,
        company_name=lead_data.get("company_name", ""),
        summary=lead_data.get("company_description") or lead_data.get("summary", ""),
        funding_amount=lead_data.get("funding_amount", ""),
        funding_round=lead_data.get("funding_round", ""),
        funding_date=str(lead_data.get("funding_date", "")),
        country=lead_data.get("country") or lead_data.get("region", ""),
    )
    try:
        draft = await _call_mistral_draft(prompt)
        return draft
    except RetryError as e:
        logger.error("Email drafting failed after 3 attempts: %s", e)
        return None
    except Exception as e:
        logger.error("Email drafting failed: %s", e)
        return None
