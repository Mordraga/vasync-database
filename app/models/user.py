from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import Role


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    discord_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(100))

    # IANA tz name (e.g. "America/Chicago"); availability windows for this
    # user are entered and resolved in this timezone before being converted
    # to absolute Unix timestamps.
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")

    # Best-effort cache of the user's highest guild role, refreshed on each
    # authenticated request. Authorization decisions still re-derive the
    # role from live Discord role IDs (see app.core.security) rather than
    # trusting this column, which exists for display/debugging only.
    cached_role: Mapped[Role] = mapped_column(default=Role.ENTITY)
