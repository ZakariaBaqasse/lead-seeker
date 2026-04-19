"""add enrichment columns

Revision ID: 002
Revises: 001
Create Date: 2026-04-19

"""
from alembic import op
import sqlalchemy as sa

revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('leads', sa.Column('product_description', sa.Text(), nullable=True))
    op.add_column('leads', sa.Column('tech_stack', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('leads', 'tech_stack')
    op.drop_column('leads', 'product_description')
