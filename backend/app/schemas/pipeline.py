import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class PipelineRunOut(BaseModel):
    id: uuid.UUID
    started_at: datetime
    completed_at: Optional[datetime] = None
    articles_fetched: int = 0
    articles_processed: int = 0
    leads_created: int = 0
    errors: Optional[Any] = None
    status: str

    model_config = {"from_attributes": True}


class StatsOut(BaseModel):
    draft: int = 0
    sent: int = 0
    replied_won: int = 0
    replied_lost: int = 0
    archived: int = 0
    no_response: int = 0
