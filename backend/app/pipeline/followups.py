from datetime import date, datetime, timedelta
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
