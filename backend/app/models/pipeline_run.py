from sqlalchemy import JSON, DateTime, Integer, String, func, text
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[str] = mapped_column(
        String(36), server_default=text("gen_random_uuid()"), primary_key=True
    )
    started_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    articles_fetched: Mapped[int] = mapped_column(Integer, default=0)
    articles_processed: Mapped[int] = mapped_column(Integer, default=0)
    leads_created: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="running")
