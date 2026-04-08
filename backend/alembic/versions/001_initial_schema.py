"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-04-08

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'leads',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('company_name', sa.String(255), nullable=False),
        sa.Column('company_domain', sa.String(255), nullable=True),
        sa.Column('company_description', sa.Text(), nullable=True),
        sa.Column('region', sa.String(100), nullable=True),
        sa.Column('country', sa.String(100), nullable=True),
        sa.Column('employee_count', sa.Integer(), nullable=True),
        sa.Column('funding_amount', sa.String(50), nullable=True),
        sa.Column('funding_date', sa.Date(), nullable=True),
        sa.Column('funding_round', sa.String(50), nullable=True),
        sa.Column('news_headline', sa.Text(), nullable=True),
        sa.Column('news_url', sa.String(500), nullable=True),
        sa.Column('cto_name', sa.String(255), nullable=True),
        sa.Column('cto_email', sa.String(255), nullable=True),
        sa.Column('linkedin_url', sa.String(500), nullable=True),
        sa.Column('status', sa.String(50), server_default='draft', nullable=False),
        sa.Column('email_draft', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_leads_status', 'leads', ['status'])
    op.create_index('idx_leads_created_at', 'leads', [sa.text('created_at DESC')])
    op.create_index(
        'idx_leads_domain', 'leads', ['company_domain'],
        unique=True,
        postgresql_where=sa.text('company_domain IS NOT NULL')
    )

    op.create_table(
        'pipeline_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('articles_fetched', sa.Integer(), server_default='0', nullable=True),
        sa.Column('articles_processed', sa.Integer(), server_default='0', nullable=True),
        sa.Column('leads_created', sa.Integer(), server_default='0', nullable=True),
        sa.Column('errors', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_index('idx_leads_domain', table_name='leads')
    op.drop_index('idx_leads_created_at', table_name='leads')
    op.drop_index('idx_leads_status', table_name='leads')
    op.drop_table('leads')
    op.drop_table('pipeline_runs')
