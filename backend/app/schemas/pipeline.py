import uuid
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict


class PipelineRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    started_at: datetime
    completed_at: Optional[datetime] = None
    articles_fetched: int
    articles_processed: int
    leads_created: int
    errors: Optional[list[Any]] = None
    status: str


class StatsOut(BaseModel):
    draft: int = 0
    sent: int = 0
    replied_won: int = 0
    replied_lost: int = 0
    archived: int = 0


class ExtractionResult(BaseModel):
    company_name: Optional[str] = None
    company_domain: Optional[str] = None
    funding_amount: Optional[str] = None
    funding_round: Optional[str] = None
    funding_date: Optional[str] = None  # YYYY-MM-DD string from LLM
    employee_count_estimate: Optional[int] = None
    region: Optional[str] = None
    country: Optional[str] = None
    sector: Optional[str] = None
    summary: Optional[str] = None
    is_relevant: bool = False
