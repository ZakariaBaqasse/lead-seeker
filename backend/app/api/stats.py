from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import verify_api_key
from app.db import get_db
from app.models.lead import Lead
from app.schemas.pipeline import StatsOut

router = APIRouter(prefix="/api/stats", tags=["stats"], dependencies=[Depends(verify_api_key)])


@router.get("", response_model=StatsOut)
async def get_stats(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Lead.status, func.count(Lead.id)).group_by(Lead.status)
    )
    counts = dict(result.all())
    return StatsOut(
        draft=counts.get("draft", 0),
        sent=counts.get("sent", 0),
        replied_won=counts.get("replied_won", 0),
        replied_lost=counts.get("replied_lost", 0),
        archived=counts.get("archived", 0),
    )
