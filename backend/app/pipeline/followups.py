from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import Lead

CASABLANCA_TZ = ZoneInfo("Africa/Casablanca")


def add_business_days(from_date: date, days: int) -> date:
    """Add N business days (Mon–Fri) to a date in Africa/Casablanca."""
    current = from_date
    added = 0
    while added < days:
        current += timedelta(days=1)
        if current.weekday() < 5:  # Mon=0 … Fri=4
            added += 1
    return current


async def get_due_leads(session: AsyncSession, current_local_date: date) -> list[Lead]:
    """Select leads eligible for follow-up draft generation.

    Criteria: status='sent', follow_up_ready=False,
              follow_up_due_date <= current_local_date, follow_up_count < 2
    """
    result = await session.execute(
        select(Lead).where(
            Lead.status == "sent",
            Lead.follow_up_ready.is_(False),
            Lead.follow_up_due_date <= current_local_date,
            Lead.follow_up_count < 2,
        )
    )
    return list(result.scalars().all())


async def get_no_response_leads(
    session: AsyncSession, current_local_date: date
) -> list[Lead]:
    """Select leads to be auto-closed to no_response.

    Criteria: status='sent', follow_up_count=2, follow_up_ready=False,
              follow_up_due_date <= current_local_date
    """
    result = await session.execute(
        select(Lead).where(
            Lead.status == "sent",
            Lead.follow_up_count == 2,
            Lead.follow_up_ready.is_(False),
            Lead.follow_up_due_date <= current_local_date,
        )
    )
    return list(result.scalars().all())


async def run_followup_job(session: AsyncSession) -> None:
    """Orchestrate the full follow-up processing run.

    Order:
    1. Get current local date in Africa/Casablanca
    2. Close no_response leads (atomic transition for each)
    3. Generate follow-up drafts for due leads
    4. Send Telegram digest
    5. Log run summary
    """
    import logging
    from app.profile import get_profile
    from app.pipeline.drafter import draft_follow_up_email
    from app.notifications.telegram import send_followup_digest

    logger = logging.getLogger(__name__)

    try:
        current_local_date = datetime.now(CASABLANCA_TZ).date()

        # Step 1: close no_response leads
        no_response_candidates = await get_no_response_leads(session, current_local_date)
        no_response_closed: list[Lead] = []
        for lead in no_response_candidates:
            try:
                # Atomic recheck inside the same session
                if not (
                    lead.status == "sent"
                    and lead.follow_up_count == 2
                    and lead.follow_up_ready is False
                    and lead.follow_up_due_date is not None
                    and lead.follow_up_due_date <= current_local_date
                ):
                    continue
                lead.status = "no_response"  # type: ignore[assignment]
                lead.follow_up_ready = False
                lead.follow_up_due_date = None
                await session.commit()
                await session.refresh(lead)
                no_response_closed.append(lead)
                logger.info("Lead %s closed as no_response", lead.id)
            except Exception as e:
                logger.error("Failed to close lead %s as no_response: %s", lead.id, e)
                await session.rollback()

        # Step 2: generate follow-up drafts for due leads
        due_leads = await get_due_leads(session, current_local_date)
        try:
            profile = get_profile()
        except Exception as e:
            logger.error("Could not load profile for follow-up drafting: %s", e)
            profile = {}

        ready_leads: list[Lead] = []
        draft_failures = 0
        for lead in due_leads:
            try:
                follow_up_number = lead.follow_up_count + 1
                lead_data = {
                    "company_name": lead.company_name,
                    "cto_name": lead.cto_name,
                    "product_description": lead.product_description,
                    "tech_stack": lead.tech_stack,
                    "email_draft": lead.email_draft,
                    "summary": lead.company_description,
                }
                draft = await draft_follow_up_email(lead_data, profile, follow_up_number)
                if draft:
                    lead.follow_up_draft = draft
                    lead.follow_up_ready = True
                    lead.follow_up_generated_at = datetime.now(timezone.utc)
                    await session.commit()
                    await session.refresh(lead)
                    ready_leads.append(lead)
                    logger.info(
                        "Follow-up %d draft generated for lead %s",
                        follow_up_number,
                        lead.id,
                    )
                else:
                    draft_failures += 1
                    logger.error(
                        "Follow-up draft failed for lead %s (follow_up %d), will retry next run",
                        lead.id,
                        follow_up_number,
                    )
            except Exception as e:
                draft_failures += 1
                logger.error("Error generating follow-up for lead %s: %s", lead.id, e)
                await session.rollback()

        # Step 3: send Telegram digest
        await send_followup_digest(ready_leads, no_response_closed)

        logger.info(
            "Follow-up run complete: %d drafted, %d no_response, %d draft failures",
            len(ready_leads),
            len(no_response_closed),
            draft_failures,
        )
    except Exception as e:
        logger.error("Follow-up job top-level error: %s", e, exc_info=True)
