from datetime import date, time

from sqlalchemy import Date, ForeignKey, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import Recurrence, Status


class RecurringAvailability(Base):
    """One recurring day-of-week rule for a user (spec section 3).

    Each row is a single preferred window on a single weekday. Biweekly
    rules additionally carry an anchor date used to determine which of the
    two alternating weeks the rule falls on.
    """

    __tablename__ = "recurring_availability"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    weekday: Mapped[int]  # 0 = Monday .. 6 = Sunday, matches date.weekday()
    recurrence: Mapped[Recurrence] = mapped_column(default=Recurrence.WEEKLY)
    anchor_date: Mapped[date | None] = mapped_column(Date, default=None)

    status: Mapped[Status]
    window_start: Mapped[time] = mapped_column(Time)
    window_end: Mapped[time] = mapped_column(Time)
