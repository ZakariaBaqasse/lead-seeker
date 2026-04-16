import uuid
from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, field_validator


class LeadStatus(str, Enum):
    draft = "draft"
    sent = "sent"
    replied_won = "replied_won"
    replied_lost = "replied_lost"
    archived = "archived"


class LeadOut(BaseModel):
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
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class LeadUpdate(BaseModel):
    cto_name: Optional[str] = None
    cto_email: Optional[str] = None
    linkedin_url: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[LeadStatus] = None

    @field_validator("status", mode="before")
    @classmethod
    def status_not_null(cls, v):
        if v is None:
            raise ValueError(
                "status cannot be null; omit the field to leave it unchanged"
            )
        return v


class LeadListResponse(BaseModel):
    items: list[LeadOut]
    total: int


class ExtractionResult(BaseModel):
    company_name: Optional[str] = None
    company_domain: Optional[str] = None
    funding_amount: Optional[str] = None
    funding_round: Optional[str] = None

    @field_validator("funding_amount", mode="before")
    @classmethod
    def coerce_funding_amount(cls, v):
        if isinstance(v, (int, float)):
            return str(int(v))
        return v

    @field_validator("employee_count_estimate", mode="before")
    @classmethod
    def coerce_employee_count(cls, v):
        if isinstance(v, str):
            import re

            match = re.search(r"\d+", v)
            return int(match.group()) if match else None
        return v

    @field_validator("company_domain", mode="before")
    @classmethod
    def strip_domain_url(cls, v):
        if isinstance(v, str):
            import re

            v = re.sub(r"^https?://", "", v)
            v = v.split("/")[0].strip()
        return v or None

    funding_date: Optional[str] = None  # YYYY-MM-DD string from LLM
    employee_count_estimate: Optional[int] = None
    region: Optional[str] = None
    country: Optional[str] = None
    sector: Optional[str] = None
    summary: Optional[str] = None
    is_relevant: bool = False
    relevance_reason: Optional[str] = None
