import uuid
from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.lead import Lead
from app.schemas.lead import LeadListResponse, LeadOut, LeadStatus, LeadUpdate

router = APIRouter(tags=["leads"])


@router.get("/leads", response_model=LeadListResponse)
async def list_leads(
    status: Optional[LeadStatus] = Query(None),
    region: Optional[str] = Query(None),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = select(Lead)
    if status:
        query = query.where(Lead.status == status.value)
    if region:
        query = query.where(Lead.region.ilike(f"%{region}%"))
    if from_date:
        query = query.where(Lead.created_at >= from_date)
    if to_date:
        query = query.where(Lead.created_at <= to_date)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    query = query.order_by(Lead.created_at.desc()).offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    leads = result.scalars().all()

    return LeadListResponse(items=leads, total=total)


@router.get("/leads/{lead_id}", response_model=LeadOut)
async def get_lead(lead_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead
