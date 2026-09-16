from datetime import datetime

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ConfirmedCollab(Base):
    """A confirmed collab the bot has committed to reminding participants
    about (spec section 4)."""

    __tablename__ = "confirmed_collabs"

    id: Mapped[int] = mapped_column(primary_key=True)
    # timezone=True: this column is compared against datetime.now(timezone.utc)
    # in collab_repository.list_upcoming_unreminded - a naive column would
    # raise "can't subtract offset-naive and offset-aware datetimes" at query time.
    start_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    reminder_sent: Mapped[bool] = mapped_column(default=False)

    participants: Mapped[list["CollabParticipant"]] = relationship(
        back_populates="collab", cascade="all, delete-orphan"
    )


class CollabParticipant(Base):
    __tablename__ = "collab_participants"

    id: Mapped[int] = mapped_column(primary_key=True)
    collab_id: Mapped[int] = mapped_column(ForeignKey("confirmed_collabs.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    collab: Mapped[ConfirmedCollab] = relationship(back_populates="participants")
