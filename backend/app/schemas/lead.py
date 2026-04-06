import uuid
from datetime import date, datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator


class LeadStatus(str, Enum):
    draft = "draft"
    sent = "sent"
    replied_won = "replied_won"
    replied_lost = "replied_lost"
    archived = "archived"


class LeadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_name: str
    company_domain: Optional[str] = None
    company_description: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    employee_count: Optional[int] = None
    funding_amount: Optional[str] = None
    funding_date: Optional[date] = None
    funding_round: Optional[str] = None
    news_headline: Optional[str] = None
    news_url: Optional[str] = None
    cto_name: Optional[str] = None
    cto_email: Optional[str] = None
    linkedin_url: Optional[str] = None
    status: LeadStatus
    email_draft: Optional[str] = None
    notes: Optional[str] = None
    sent_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class LeadUpdate(BaseModel):
    cto_name: Optional[str] = None
    cto_email: Optional[str] = None
    linkedin_url: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[LeadStatus] = None


class LeadListResponse(BaseModel):
    items: list[LeadOut]
    total: int


class LeadListParams(BaseModel):
    status: Optional[LeadStatus] = None
    region: Optional[str] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    page: int = 1
    limit: int = 20

    @field_validator("page")
    @classmethod
    def page_must_be_positive(cls, v):
        if v < 1:
            raise ValueError("page must be >= 1")
        return v

    @field_validator("limit")
    @classmethod
    def limit_must_be_valid(cls, v):
        if not 1 <= v <= 100:
            raise ValueError("limit must be between 1 and 100")
        return v
