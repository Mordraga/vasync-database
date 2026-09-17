from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.collab import CollabParticipant, ConfirmedCollab
from app.models.enums import CollabStatus
from app.models.user import User
from app.services.domain import is_collab_still_viable, resolve_collab_outcome


class CollabPermissionError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class RespondResult:
    pending: bool
    status: CollabStatus | None
    accepted_discord_ids: list[int]
    declined_discord_ids: list[int]
    thread_id: int | None


@dataclass(frozen=True, slots=True)
class CancelResult:
    fully_cancelled: bool
    remaining_discord_ids: list[int]
    thread_id: int | None


async def _get_with_participants(session: AsyncSession, collab_id: int) -> ConfirmedCollab | None:
    result = await session.execute(
        select(ConfirmedCollab)
        .options(selectinload(ConfirmedCollab.participants))
        .where(ConfirmedCollab.id == collab_id)
    )
    return result.scalar_one_or_none()


async def _discord_ids_by_user_id(session: AsyncSession, user_ids: list[int]) -> dict[int, int]:
    result = await session.execute(select(User.id, User.discord_id).where(User.id.in_(user_ids)))
    return dict(result.all())


async def create_pending_collab(
    session: AsyncSession,
    initiator_discord_id: int,
    other_discord_ids: list[int],
    start_at_utc: datetime,
    thread_id: int | None,
) -> ConfirmedCollab:
    all_discord_ids = [initiator_discord_id, *other_discord_ids]
    result = await session.execute(select(User).where(User.discord_id.in_(all_discord_ids)))
    users_by_discord_id = {user.discord_id: user for user in result.scalars().all()}

    if initiator_discord_id not in users_by_discord_id:
        # The initiator needn't be one of the matched participants (e.g.
        # staff proposing a time for two entities) but they do need a User
        # row, since they're the one CollabParticipant.is_initiator=True
        # row resolve_collab_outcome anchors on - silently dropping them
        # here would leave the collab with no initiator to notify.
        raise CollabPermissionError("initiator is not a registered vasync user")

    collab = ConfirmedCollab(start_at_utc=start_at_utc, status=CollabStatus.PENDING, thread_id=thread_id)
    collab.participants = [
        CollabParticipant(
            user_id=users_by_discord_id[discord_id].id,
            is_initiator=discord_id == initiator_discord_id,
            accepted=True if discord_id == initiator_discord_id else None,
        )
        for discord_id in all_discord_ids
        if discord_id in users_by_discord_id
    ]

    session.add(collab)
    await session.commit()
    await session.refresh(collab)
    return collab


async def respond_to_collab(session: AsyncSession, collab_id: int, discord_id: int, accept: bool) -> RespondResult:
    collab = await _get_with_participants(session, collab_id)
    if collab is None:
        raise CollabPermissionError("collab not found")

    user_ids = [p.user_id for p in collab.participants]
    discord_ids_by_user_id = await _discord_ids_by_user_id(session, user_ids)

    target = next(
        (p for p in collab.participants if discord_ids_by_user_id.get(p.user_id) == discord_id and not p.is_initiator),
        None,
    )
    if target is None:
        raise CollabPermissionError("caller is not an invited (non-initiator) participant of this collab")

    target.accepted = accept

    participants = [
        (discord_ids_by_user_id[p.user_id], p.is_initiator, p.accepted) for p in collab.participants
    ]
    outcome = resolve_collab_outcome(participants)
    if outcome is None:
        await session.commit()
        return RespondResult(
            pending=True, status=None, accepted_discord_ids=[], declined_discord_ids=[], thread_id=collab.thread_id
        )

    collab.status = outcome.status
    collab.participants = [
        p for p in collab.participants if discord_ids_by_user_id[p.user_id] in outcome.accepted_discord_ids
    ]
    await session.commit()

    return RespondResult(
        pending=False,
        status=outcome.status,
        accepted_discord_ids=outcome.accepted_discord_ids,
        declined_discord_ids=outcome.declined_discord_ids,
        thread_id=collab.thread_id,
    )


async def cancel_collab(session: AsyncSession, collab_id: int, discord_id: int) -> CancelResult:
    collab = await _get_with_participants(session, collab_id)
    if collab is None or collab.status is not CollabStatus.CONFIRMED:
        raise CollabPermissionError("collab not found or not confirmed")

    user_ids = [p.user_id for p in collab.participants]
    discord_ids_by_user_id = await _discord_ids_by_user_id(session, user_ids)

    target = next((p for p in collab.participants if discord_ids_by_user_id.get(p.user_id) == discord_id), None)
    if target is None:
        raise CollabPermissionError("caller is not a participant of this collab")

    collab.participants = [p for p in collab.participants if p is not target]
    remaining_discord_ids = [discord_ids_by_user_id[p.user_id] for p in collab.participants]

    fully_cancelled = not is_collab_still_viable(remaining_discord_ids)
    if fully_cancelled:
        collab.status = CollabStatus.CANCELLED

    await session.commit()
    return CancelResult(
        fully_cancelled=fully_cancelled, remaining_discord_ids=remaining_discord_ids, thread_id=collab.thread_id
    )


async def get_collab(session: AsyncSession, collab_id: int) -> ConfirmedCollab | None:
    return await _get_with_participants(session, collab_id)


async def list_upcoming_unreminded(session: AsyncSession, now: datetime) -> list[ConfirmedCollab]:
    """Collabs the bot should (re-)schedule a reminder for, e.g. on
    startup after a restart."""
    result = await session.execute(
        select(ConfirmedCollab)
        .options(selectinload(ConfirmedCollab.participants))
        .where(
            ConfirmedCollab.status == CollabStatus.CONFIRMED,
            ConfirmedCollab.reminder_sent.is_(False),
            ConfirmedCollab.start_at_utc >= now,
        )
    )
    return list(result.scalars().all())


async def list_upcoming_for_user(session: AsyncSession, discord_id: int, now: datetime) -> list[ConfirmedCollab]:
    user_result = await session.execute(select(User.id).where(User.discord_id == discord_id))
    user_id = user_result.scalar_one_or_none()
    if user_id is None:
        return []

    result = await session.execute(
        select(ConfirmedCollab)
        .join(CollabParticipant)
        .options(selectinload(ConfirmedCollab.participants))
        .where(
            ConfirmedCollab.status == CollabStatus.CONFIRMED,
            ConfirmedCollab.start_at_utc >= now,
            CollabParticipant.user_id == user_id,
        )
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
