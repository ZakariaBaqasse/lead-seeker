# backend/scripts/backfill_followup_dates.py
import asyncio
from zoneinfo import ZoneInfo
from sqlalchemy import select
from app.db import AsyncSessionLocal
from app.models.lead import Lead
from app.pipeline.followups import add_business_days


async def backfill():
    tz = ZoneInfo("Africa/Casablanca")
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Lead).where(Lead.status == "sent", Lead.follow_up_due_date is None)
        )
        leads = result.scalars().all()
        print(f"Backfilling {len(leads)} leads...")
        for lead in leads:
            base_date = (lead.sent_at or lead.updated_at).astimezone(tz).date()
            lead.last_contact_at = lead.sent_at or lead.updated_at
            lead.follow_up_count = 0
            lead.follow_up_ready = False
            lead.follow_up_due_date = add_business_days(base_date, 3)
            print(f"  {lead.company_name}: due {lead.follow_up_due_date}")
        await session.commit()
        print("Done.")


asyncio.run(backfill())
