"""create leads and pipeline_runs tables

Revision ID: b0b20fd4e0c2
Revises: 
Create Date: 2026-04-06 13:14:05.893294

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects import postgresql
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'b0b20fd4e0c2'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "leads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("company_domain", sa.String(255), nullable=True),
        sa.Column("company_description", sa.Text, nullable=True),
        sa.Column("region", sa.String(100), nullable=True),
        sa.Column("country", sa.String(100), nullable=True),
        sa.Column("employee_count", sa.Integer, nullable=True),
        sa.Column("funding_amount", sa.String(50), nullable=True),
        sa.Column("funding_date", sa.Date, nullable=True),
        sa.Column("funding_round", sa.String(50), nullable=True),
        sa.Column("news_headline", sa.Text, nullable=True),
        sa.Column("news_url", sa.String(500), nullable=True),
        sa.Column("cto_name", sa.String(255), nullable=True),
        sa.Column("cto_email", sa.String(255), nullable=True),
        sa.Column("linkedin_url", sa.String(500), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("email_draft", sa.Text, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_leads_status", "leads", ["status"])
    op.create_index("idx_leads_created_at", "leads", ["created_at"], postgresql_ops={"created_at": "DESC NULLS LAST"})
    op.create_index(
        "idx_leads_domain",
        "leads",
        ["company_domain"],
        unique=True,
        postgresql_where=text("company_domain IS NOT NULL"),
    )

    op.create_table(
        "pipeline_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("articles_fetched", sa.Integer, nullable=False, server_default="0"),
        sa.Column("articles_processed", sa.Integer, nullable=False, server_default="0"),
        sa.Column("leads_created", sa.Integer, nullable=False, server_default="0"),
        sa.Column("errors", sa.JSON, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="running"),
    )


def downgrade() -> None:
    op.drop_table("pipeline_runs")
    op.drop_index("idx_leads_domain", table_name="leads")
    op.drop_index("idx_leads_created_at", table_name="leads")
    op.drop_index("idx_leads_status", table_name="leads")
    op.drop_table("leads")
