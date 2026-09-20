"""add twitch link + live status to users, poll interval to bot_settings

Revision ID: c8d4e6f1a9b7
Revises: f47a1c9b3e2d
Create Date: 2026-09-20 15:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'c8d4e6f1a9b7'
down_revision = 'f47a1c9b3e2d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('twitch_username', sa.String(length=64), nullable=True))
    op.add_column('users', sa.Column('is_live', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.alter_column('users', 'is_live', server_default=None)

    op.add_column(
        'bot_settings', sa.Column('live_poll_interval_minutes', sa.Integer(), nullable=False, server_default='5')
    )
    op.alter_column('bot_settings', 'live_poll_interval_minutes', server_default=None)


def downgrade() -> None:
    op.drop_column('bot_settings', 'live_poll_interval_minutes')
    op.drop_column('users', 'is_live')
    op.drop_column('users', 'twitch_username')
