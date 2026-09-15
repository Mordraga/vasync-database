from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.collab import CollabParticipant, ConfirmedCollab
from app.models.user import User


async def create_confirmed_collab(
    session: AsyncSession, discord_ids: list[int], start_at_utc: datetime
) -> ConfirmedCollab:
    result = await session.execute(select(User).where(User.discord_id.in_(discord_ids)))
    users = result.scalars().all()

    collab = ConfirmedCollab(start_at_utc=start_at_utc)
    collab.participants = [CollabParticipant(user_id=user.id) for user in users]

    session.add(collab)
    await session.commit()
    await session.refresh(collab)
    return collab


async def list_upcoming_unreminded(session: AsyncSession, now: datetime) -> list[ConfirmedCollab]:
    """Collabs the bot should (re-)schedule a reminder for, e.g. on
    startup after a restart."""
    result = await session.execute(
        select(ConfirmedCollab)
        .options(selectinload(ConfirmedCollab.participants))
        .where(ConfirmedCollab.reminder_sent.is_(False), ConfirmedCollab.start_at_utc >= now)
    )
    return list(result.scalars().all())


async def mark_reminder_sent(session: AsyncSession, collab_id: int) -> None:
    collab = await session.get(ConfirmedCollab, collab_id)
    if collab is not None:
        collab.reminder_sent = True
        await session.commit()


async def get_participant_discord_ids(session: AsyncSession, collab: ConfirmedCollab) -> list[int]:
    user_ids = [participant.user_id for participant in collab.participants]
    result = await session.execute(select(User.discord_id).where(User.id.in_(user_ids)))
    return list(result.scalars().all())
