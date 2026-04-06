import uuid
from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import verify_api_key
from app.db import get_db
from app.models.lead import Lead
from app.pipeline.drafter import draft_email
from app.profile import get_profile
from app.schemas.lead import LeadListResponse, LeadOut, LeadStatus, LeadUpdate

router = APIRouter(prefix="/api/leads", tags=["leads"], dependencies=[Depends(verify_api_key)])


class LeadFilters:
    def __init__(
        self,
        status: Optional[LeadStatus] = Query(None),
        region: Optional[str] = Query(None),
        from_date: Optional[date] = Query(None),
        to_date: Optional[date] = Query(None),
        page: int = Query(1, ge=1),
        limit: int = Query(20, ge=1, le=100),
    ):
        self.status = status
        self.region = region
        self.from_date = from_date
        self.to_date = to_date
        self.page = page
        self.limit = limit


@router.get("", response_model=LeadListResponse)
async def list_leads(filters: LeadFilters = Depends(), db: AsyncSession = Depends(get_db)):
    query = select(Lead)
    count_query = select(func.count()).select_from(Lead)

    if filters.status:
        query = query.where(Lead.status == filters.status.value)
        count_query = count_query.where(Lead.status == filters.status.value)
    if filters.region:
        query = query.where(Lead.region == filters.region)
        count_query = count_query.where(Lead.region == filters.region)
    if filters.from_date:
        query = query.where(Lead.funding_date >= filters.from_date)
        count_query = count_query.where(Lead.funding_date >= filters.from_date)
    if filters.to_date:
        query = query.where(Lead.funding_date <= filters.to_date)
        count_query = count_query.where(Lead.funding_date <= filters.to_date)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    query = query.order_by(Lead.created_at.desc())
    query = query.offset((filters.page - 1) * filters.limit).limit(filters.limit)
    result = await db.execute(query)
    leads = result.scalars().all()

    return LeadListResponse(items=[LeadOut.model_validate(lead) for lead in leads], total=total)


@router.get("/{lead_id}", response_model=LeadOut)
async def get_lead(lead_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return LeadOut.model_validate(lead)


@router.patch("/{lead_id}", response_model=LeadOut)
async def update_lead(lead_id: uuid.UUID, body: LeadUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "status" and value is not None:
            setattr(lead, key, value.value)
        else:
            setattr(lead, key, value)

    # Auto-set sent_at when status changes to 'sent'
    if "status" in update_data and update_data["status"] == LeadStatus.sent:
        lead.sent_at = datetime.now(timezone.utc)

    lead.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(lead)
    return LeadOut.model_validate(lead)


@router.delete("/{lead_id}", status_code=204)
async def delete_lead(lead_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    await db.delete(lead)
    return Response(status_code=204)


@router.post("/{lead_id}/regenerate")
async def regenerate_email(lead_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    profile = get_profile()
    lead_data = {
        "company_name": lead.company_name,
        "company_description": lead.company_description,
        "summary": lead.company_description,
        "funding_amount": lead.funding_amount,
        "funding_round": lead.funding_round,
        "funding_date": lead.funding_date,
        "country": lead.country,
        "region": lead.region,
    }
    draft = await draft_email(lead_data, profile)
    if draft is None:
        raise HTTPException(status_code=502, detail="Email drafting failed, please try again")

    lead.email_draft = draft
    lead.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(lead)
    return {"email_draft": draft}
