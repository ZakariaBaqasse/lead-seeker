import uuid
from datetime import date, datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.limiter import limiter
from app.models.lead import Lead
from app.pipeline.drafter import draft_email
from app.pipeline.followups import add_business_days
from app.profile import get_profile
from app.schemas.lead import LeadListResponse, LeadOut, LeadStatus, LeadUpdate

CASABLANCA_TZ = ZoneInfo("Africa/Casablanca")
_TERMINAL_STATUSES = {"replied_won", "replied_lost", "archived", "no_response"}

router = APIRouter(tags=["leads"])


@router.get("/leads", response_model=LeadListResponse)
@limiter.limit("60/minute")
async def list_leads(
    request: Request,
    status: Optional[LeadStatus] = Query(None),
    region: Optional[str] = Query(None),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    search: Optional[str] = Query(None, max_length=200),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = select(Lead)
    if status:
        query = query.where(Lead.status == status.value)
    if region:
        query = query.where(Lead.region.ilike(f"%{region}%"))
    if search:
        query = query.where(Lead.company_name.ilike(f"%{search}%"))
    if from_date:
        query = query.where(Lead.created_at >= from_date)
    if to_date:
        query = query.where(Lead.created_at <= to_date)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    query = (
        query.order_by(Lead.created_at.desc()).offset((page - 1) * limit).limit(limit)
    )
    result = await db.execute(query)
    leads = result.scalars().all()

    return LeadListResponse(items=leads, total=total)


@router.get("/leads/{lead_id}", response_model=LeadOut)
@limiter.limit("60/minute")
async def get_lead(
    request: Request, lead_id: uuid.UUID, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.patch("/leads/{lead_id}", response_model=LeadOut)
@limiter.limit("30/minute")
async def update_lead(
    request: Request,
    lead_id: uuid.UUID,
    data: LeadUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    update_data = data.model_dump(exclude_unset=True)
    new_status_raw = update_data.get("status")
    new_status_str: str | None = (
        new_status_raw.value if hasattr(new_status_raw, "value") else new_status_raw
    )

    # Reject reopening a terminal lead to 'sent'
    if new_status_str == "sent" and lead.status in _TERMINAL_STATUSES:
        raise HTTPException(
            status_code=422, detail="Cannot reopen a terminal lead to sent"
        )

    for field, value in update_data.items():
        if field == "status" and value is not None:
            setattr(lead, field, value.value if hasattr(value, "value") else value)
        else:
            setattr(lead, field, value)

    now_utc = datetime.now(timezone.utc)
    today_casablanca: date = datetime.now(CASABLANCA_TZ).date()

    # draft → sent (first send only: sent_at is still null)
    if new_status_str == "sent" and lead.sent_at is None:
        lead.sent_at = now_utc
        lead.last_contact_at = now_utc
        lead.follow_up_count = 0
        lead.follow_up_ready = False
        lead.follow_up_due_date = add_business_days(today_casablanca, 3)

    # Transition to terminal outcome: clear follow-up scheduling
    if new_status_str in {"replied_won", "replied_lost", "archived"}:
        lead.follow_up_ready = False
        lead.follow_up_due_date = None

    lead.updated_at = now_utc
    await db.commit()
    await db.refresh(lead)
    return lead


@router.delete("/leads/{lead_id}", status_code=204)
@limiter.limit("30/minute")
async def delete_lead(
    request: Request, lead_id: uuid.UUID, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    await db.delete(lead)
    await db.commit()
    return Response(status_code=204)


@router.post("/leads/{lead_id}/follow-ups/mark-sent", response_model=LeadOut)
@limiter.limit("10/minute")
async def mark_follow_up_sent(
    request: Request, lead_id: uuid.UUID, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if lead.status != "sent":
        raise HTTPException(status_code=422, detail="Lead is not in sent status")
    if not lead.follow_up_ready:
        raise HTTPException(status_code=422, detail="No follow-up draft is ready")
    if lead.follow_up_count >= 2:
        raise HTTPException(status_code=422, detail="Maximum follow-up count reached")

    now_utc = datetime.now(timezone.utc)
    today_casablanca: date = datetime.now(CASABLANCA_TZ).date()

    lead.follow_up_count += 1
    lead.last_contact_at = now_utc
    lead.follow_up_ready = False
    lead.follow_up_due_date = add_business_days(today_casablanca, 3)
    lead.updated_at = now_utc

    await db.commit()
    await db.refresh(lead)
    return lead


@router.post("/leads/{lead_id}/regenerate")
@limiter.limit("2/minute")
async def regenerate_email(
    request: Request, lead_id: uuid.UUID, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    profile = get_profile()
    lead_data = {
        "company_name": lead.company_name,
        "company_description": lead.company_description,
        "funding_amount": lead.funding_amount,
        "funding_round": lead.funding_round,
        "funding_date": lead.funding_date,
        "country": lead.country,
        "region": lead.region,
    }
    email_draft = await draft_email(lead_data, profile)

    lead.email_draft = email_draft
    lead.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(lead)

    return {"email_draft": email_draft}
