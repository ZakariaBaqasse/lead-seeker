"""add follow-up fields

Revision ID: 003_add_followup_fields
Revises: 002
Create Date: 2026-04-22

"""
from alembic import op
import sqlalchemy as sa

revision = '003_add_followup_fields'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('leads', sa.Column('last_contact_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('leads', sa.Column('follow_up_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('leads', sa.Column('follow_up_due_date', sa.Date(), nullable=True))
    op.add_column('leads', sa.Column('follow_up_ready', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('leads', sa.Column('follow_up_generated_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('leads', sa.Column('follow_up_draft', sa.Text(), nullable=True))

    op.create_check_constraint(
        'ck_leads_follow_up_count_range',
        'leads',
        'follow_up_count >= 0 AND follow_up_count <= 2',
    )
    op.create_index('idx_leads_follow_up_due_date', 'leads', ['follow_up_due_date'])
    op.create_index('idx_leads_followup_composite', 'leads', ['status', 'follow_up_ready', 'follow_up_due_date'])


def downgrade() -> None:
    op.drop_index('idx_leads_followup_composite', table_name='leads')
    op.drop_index('idx_leads_follow_up_due_date', table_name='leads')
    op.drop_constraint('ck_leads_follow_up_count_range', 'leads', type_='check')
    op.drop_column('leads', 'follow_up_draft')
    op.drop_column('leads', 'follow_up_generated_at')
    op.drop_column('leads', 'follow_up_ready')
    op.drop_column('leads', 'follow_up_due_date')
    op.drop_column('leads', 'follow_up_count')
    op.drop_column('leads', 'last_contact_at')
