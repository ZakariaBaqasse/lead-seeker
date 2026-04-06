import uuid
from datetime import date, datetime, timezone
from sqlalchemy import String, Text, Integer, Date, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    company_domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    company_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    employee_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    funding_amount: Mapped[str | None] = mapped_column(String(50), nullable=True)
    funding_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    funding_round: Mapped[str | None] = mapped_column(String(50), nullable=True)
    news_headline: Mapped[str | None] = mapped_column(Text, nullable=True)
    news_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    cto_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cto_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")
    email_draft: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("idx_leads_status", "status"),
        Index("idx_leads_created_at", "created_at"),
        # Partial unique index on company_domain handled in Alembic migration:
        # op.create_index("idx_leads_domain", "leads", ["company_domain"],
        #                  unique=True, postgresql_where=text("company_domain IS NOT NULL"))
    )
