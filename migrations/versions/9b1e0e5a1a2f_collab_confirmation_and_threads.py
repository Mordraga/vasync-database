"""add collab confirmation state and thread tracking

Revision ID: 9b1e0e5a1a2f
Revises: 6057077bc312
Create Date: 2026-09-16 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = '9b1e0e5a1a2f'
down_revision = '6057077bc312'
branch_labels = None
depends_on = None


def upgrade() -> None:
    collab_status = sa.Enum('PENDING', 'CONFIRMED', 'CANCELLED', name='collabstatus')
    collab_status.create(op.get_bind())

    op.add_column(
        'confirmed_collabs',
        sa.Column('status', collab_status, nullable=False, server_default='PENDING'),
    )
    op.alter_column('confirmed_collabs', 'status', server_default=None)
    op.add_column('confirmed_collabs', sa.Column('thread_id', sa.BigInteger(), nullable=True))

    # Existing rows predate the PENDING/CONFIRMED split - they were only
    # ever created once a collab was already confirmed, so backfill them
    # as CONFIRMED rather than leaving them stuck PENDING.
    op.execute("UPDATE confirmed_collabs SET status = 'CONFIRMED'")

    op.add_column(
        'collab_participants',
        sa.Column('is_initiator', sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column('collab_participants', 'is_initiator', server_default=None)
    op.add_column('collab_participants', sa.Column('accepted', sa.Boolean(), nullable=True))
    # Existing participant rows belong to already-confirmed collabs.
    op.execute("UPDATE collab_participants SET accepted = true")


def downgrade() -> None:
    op.drop_column('collab_participants', 'accepted')
    op.drop_column('collab_participants', 'is_initiator')
    op.drop_column('confirmed_collabs', 'thread_id')
    op.drop_column('confirmed_collabs', 'status')
    sa.Enum(name='collabstatus').drop(op.get_bind())
