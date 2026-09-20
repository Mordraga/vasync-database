from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    discord_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(100))

    # IANA tz name (e.g. "America/Chicago"); availability windows for this
    # user are entered and resolved in this timezone before being converted
    # to absolute Unix timestamps.
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")

    # Best-effort cache of the user's role name/staff bit, refreshed on each
    # login. Authorization decisions still re-derive the role from live
    # Discord role IDs against the server_roles table (see
    # app.core.security) rather than trusting these columns, which exist
    # for display/debugging only.
    cached_role: Mapped[str] = mapped_column(String(64))
    cached_is_staff: Mapped[bool] = mapped_column(default=False)

    # Self-registered via the dashboard; null until the user sets one.
    twitch_username: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Pushed by vasync-bot's live poller (entities with a twitch_username
    # set only) - not something a caller sets directly.
    is_live: Mapped[bool] = mapped_column(default=False)
