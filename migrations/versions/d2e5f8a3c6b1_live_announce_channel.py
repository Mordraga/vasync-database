"""add live_announce_channel_id to bot_settings

Revision ID: d2e5f8a3c6b1
Revises: c8d4e6f1a9b7
Create Date: 2026-09-20 20:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'd2e5f8a3c6b1'
down_revision = 'c8d4e6f1a9b7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('bot_settings', sa.Column('live_announce_channel_id', sa.BigInteger(), nullable=True))


def downgrade() -> None:
    op.drop_column('bot_settings', 'live_announce_channel_id')
