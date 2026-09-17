from sqlalchemy import BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ServerRole(Base):
    """A VAsync role, mapped to the Discord role that grants it. Staff
    manage these at runtime (POST/DELETE /roles) instead of each new role
    needing its own env var and a redeploy across every service."""

    __tablename__ = "server_roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    discord_role_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    is_staff: Mapped[bool] = mapped_column(default=False)
