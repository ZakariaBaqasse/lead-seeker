"""Telegram Bot API notification for Lead Seeker follow-up digest."""
import logging
import httpx
from app.config import settings

logger = logging.getLogger(__name__)

TELEGRAM_API_BASE = "https://api.telegram.org"


async def send_followup_digest(
    ready_leads: list,
    no_response_leads: list,
) -> bool:
    """Send a Telegram digest message. Returns True on success, False on failure.

    Best-effort: failures are logged but do not raise.
    Sends nothing if both lists are empty.
    """
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        logger.warning(
            "Telegram not configured (missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID) — skipping digest"
        )
        return True

    if not ready_leads and not no_response_leads:
        return True

    lines = ["🤖 Follow-up run complete"]

    if ready_leads:
        lines.append(f"\nReady now: {len(ready_leads)}")
        for lead in ready_leads:
            company = getattr(lead, "company_name", None) or lead.get("company_name", "Unknown")
            count = getattr(lead, "follow_up_count", None)
            if count is None:
                count = lead.get("follow_up_count", 0)
            lines.append(f"- {company} — Follow-up {count + 1} ready")

    if no_response_leads:
        lines.append(f"\nClosed as no_response: {len(no_response_leads)}")
        for lead in no_response_leads:
            company = getattr(lead, "company_name", None) or lead.get("company_name", "Unknown")
            lines.append(f"- {company}")

    text = "\n".join(lines)

    try:
        url = f"{TELEGRAM_API_BASE}/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                url,
                json={"chat_id": settings.TELEGRAM_CHAT_ID, "text": text},
            )
            response.raise_for_status()
            return True
    except Exception as e:
        logger.error("Telegram digest delivery failed: %s", e)
        return False
