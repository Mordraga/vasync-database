"""make confirmed_collabs start_at_utc timezone aware

Revision ID: 6057077bc312
Revises: c2a2b2ebafe3
Create Date: 2026-09-16 04:08:42.436936
"""
from alembic import op
import sqlalchemy as sa


revision = '6057077bc312'
down_revision = 'c2a2b2ebafe3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "confirmed_collabs",
        "start_at_utc",
        type_=sa.DateTime(timezone=True),
        existing_type=sa.DateTime(timezone=False),
        postgresql_using="start_at_utc AT TIME ZONE 'UTC'",
    )


def downgrade() -> None:
    op.alter_column(
        "confirmed_collabs",
        "start_at_utc",
        type_=sa.DateTime(timezone=False),
        existing_type=sa.DateTime(timezone=True),
        postgresql_using="start_at_utc AT TIME ZONE 'UTC'",
    )
