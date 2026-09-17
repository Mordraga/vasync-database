"""move role->discord-role-id mapping into a server_roles table

Revision ID: f47a1c9b3e2d
Revises: 9b1e0e5a1a2f
Create Date: 2026-09-17 21:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = 'f47a1c9b3e2d'
down_revision = '9b1e0e5a1a2f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'server_roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('discord_role_id', sa.BigInteger(), nullable=False),
        sa.Column('is_staff', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('discord_role_id'),
    )

    op.add_column('users', sa.Column('cached_is_staff', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.alter_column('users', 'cached_is_staff', server_default=None)

    # cached_role was a Postgres enum of the Python StrEnum's *member names*
    # (ENTITY/RESEARCHER/STAFF) - roles are now free-form strings so this
    # becomes plain text, lowercased to match server_roles.name.
    op.alter_column(
        'users',
        'cached_role',
        type_=sa.String(length=64),
        postgresql_using='lower(cached_role::text)',
    )
    op.execute("UPDATE users SET cached_is_staff = true WHERE cached_role = 'staff'")
    op.execute("DROP TYPE role")

    server_roles = sa.table(
        'server_roles',
        sa.column('name', sa.String),
        sa.column('discord_role_id', sa.BigInteger),
        sa.column('is_staff', sa.Boolean),
    )
    op.bulk_insert(
        server_roles,
        [
            {'name': 'entity', 'discord_role_id': 1519059009003454524, 'is_staff': False},
            {'name': 'researcher', 'discord_role_id': 1519058500670455929, 'is_staff': False},
            {'name': 'staff', 'discord_role_id': 1519059369830912152, 'is_staff': True},
            {'name': 'explorer', 'discord_role_id': 1519084719114027159, 'is_staff': False},
        ],
    )


def downgrade() -> None:
    op.drop_table('server_roles')

    role_enum = sa.Enum('ENTITY', 'RESEARCHER', 'STAFF', name='role')
    role_enum.create(op.get_bind())
    op.execute("UPDATE users SET cached_role = 'entity' WHERE cached_role NOT IN ('entity', 'researcher', 'staff')")
    op.alter_column(
        'users',
        'cached_role',
        type_=role_enum,
        postgresql_using='upper(cached_role)::role',
    )
    op.drop_column('users', 'cached_is_staff')
