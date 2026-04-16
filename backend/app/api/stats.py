from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.limiter import limiter
from app.models.lead import Lead
from app.schemas.lead import LeadStatus
from app.schemas.pipeline import StatsOut

router = APIRouter(tags=["stats"])


@router.get("/stats", response_model=StatsOut)
@limiter.limit("60/minute")
async def get_stats(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Lead.status, func.count(Lead.id)).group_by(Lead.status)
    )
    counts = dict(result.all())
    return StatsOut(
        draft=counts.get(LeadStatus.draft.value, 0),
        sent=counts.get(LeadStatus.sent.value, 0),
        replied_won=counts.get(LeadStatus.replied_won.value, 0),
        replied_lost=counts.get(LeadStatus.replied_lost.value, 0),
        archived=counts.get(LeadStatus.archived.value, 0),
    )
