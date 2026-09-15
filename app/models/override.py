from datetime import date, time

from sqlalchemy import Date, ForeignKey, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import Status


class AvailabilityOverride(Base):
    """A single-date override that supersedes recurring rules without
    changing any future occurrence (spec section 3)."""

    __tablename__ = "availability_overrides"
    __table_args__ = (UniqueConstraint("user_id", "override_date", name="uq_override_user_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    override_date: Mapped[date] = mapped_column(Date)
    status: Mapped[Status]
    window_start: Mapped[time] = mapped_column(Time)
    window_end: Mapped[time] = mapped_column(Time)
