from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import CollabStatus


class ConfirmedCollab(Base):
    """A proposed or confirmed collab the bot has committed to reminding
    participants about (spec section 4). Despite the table/class name (kept
    to avoid a disruptive rename), a row starts life PENDING - it only
    becomes worth reminding anyone about once resolve_collab_outcome finds
    it CONFIRMED."""

    __tablename__ = "confirmed_collabs"

    id: Mapped[int] = mapped_column(primary_key=True)
    # timezone=True: this column is compared against datetime.now(timezone.utc)
    # in collab_repository.list_upcoming_unreminded - a naive column would
    # raise "can't subtract offset-naive and offset-aware datetimes" at query time.
    start_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    reminder_sent: Mapped[bool] = mapped_column(default=False)
    status: Mapped[CollabStatus] = mapped_column(default=CollabStatus.PENDING)
    # The private Discord thread scoped to this collab's participants, if
    # one was created. BigInteger: Discord snowflakes exceed 32-bit ints.
    thread_id: Mapped[int | None] = mapped_column(BigInteger, default=None)

    participants: Mapped[list["CollabParticipant"]] = relationship(
        back_populates="collab", cascade="all, delete-orphan"
    )


class CollabParticipant(Base):
    __tablename__ = "collab_participants"

    id: Mapped[int] = mapped_column(primary_key=True)
    collab_id: Mapped[int] = mapped_column(ForeignKey("confirmed_collabs.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    is_initiator: Mapped[bool] = mapped_column(default=False)
    # None = awaiting response, True = accepted, False = declined.
    accepted: Mapped[bool | None] = mapped_column(default=None)

    collab: Mapped[ConfirmedCollab] = relationship(back_populates="participants")
