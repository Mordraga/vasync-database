from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_service_token
from app.repositories import collab_repository
from app.repositories.collab_repository import CollabPermissionError
from app.services.availability_matcher import find_shared_windows
from app.schemas.collab import (
    CollabCancelIn,
    CollabCancelOut,
    CollabMatchOut,
    CollabOut,
    CollabProposeIn,
    CollabRespondIn,
    CollabRespondOut,
)

router = APIRouter(prefix="/collab", tags=["collab"], dependencies=[Depends(require_service_token)])


@router.get("/match", response_model=CollabMatchOut)
async def match_collab(
    discord_ids: str,
    start_date: date,
    end_date: date,
    db: AsyncSession = Depends(get_db),
) -> CollabMatchOut:
    """``discord_ids`` is a comma-separated list, e.g. from
    ``/collab @Mordraga @Grem`` (spec section 4)."""
    ids = [int(discord_id) for discord_id in discord_ids.split(",") if discord_id]
    windows = await find_shared_windows(db, ids, start_date, end_date)
    return CollabMatchOut(discord_ids=ids, windows=windows)


@router.post("/propose", response_model=CollabOut)
async def propose_collab(payload: CollabProposeIn, db: AsyncSession = Depends(get_db)) -> CollabOut:
    """The initiator picked a window - this creates a PENDING collab. It
    only becomes CONFIRMED once every other invited participant has
    responded via /collab/{id}/respond (spec: mutual confirmation)."""
    try:
        collab = await collab_repository.create_pending_collab(
            db, payload.initiator_discord_id, payload.other_discord_ids, payload.start_at_utc, payload.thread_id
        )
    except CollabPermissionError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
    discord_ids = await collab_repository.get_participant_discord_ids(db, collab)
    return CollabOut(
        id=collab.id,
        discord_ids=discord_ids,
        start_at_utc=collab.start_at_utc,
        reminder_sent=collab.reminder_sent,
        status=collab.status,
        thread_id=collab.thread_id,
    )


@router.post("/{collab_id}/respond", response_model=CollabRespondOut)
async def respond_to_collab(
    collab_id: int, payload: CollabRespondIn, db: AsyncSession = Depends(get_db)
) -> CollabRespondOut:
    try:
        result = await collab_repository.respond_to_collab(db, collab_id, payload.discord_id, payload.accept)
    except CollabPermissionError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc

    return CollabRespondOut(
        pending=result.pending,
        status=result.status,
        accepted_discord_ids=result.accepted_discord_ids,
        declined_discord_ids=result.declined_discord_ids,
        thread_id=result.thread_id,
    )


@router.post("/{collab_id}/cancel", response_model=CollabCancelOut)
async def cancel_collab(
    collab_id: int, payload: CollabCancelIn, db: AsyncSession = Depends(get_db)
) -> CollabCancelOut:
    try:
        result = await collab_repository.cancel_collab(db, collab_id, payload.discord_id)
    except CollabPermissionError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc

    return CollabCancelOut(
        fully_cancelled=result.fully_cancelled,
        remaining_discord_ids=result.remaining_discord_ids,
        thread_id=result.thread_id,
    )


@router.get("/upcoming", response_model=list[CollabOut])
async def upcoming_collabs(db: AsyncSession = Depends(get_db)) -> list[CollabOut]:
    """Lets the bot rehydrate reminders on startup after a restart."""
    collabs = await collab_repository.list_upcoming_unreminded(db, datetime.now(timezone.utc))
    results = []
    for collab in collabs:
        discord_ids = await collab_repository.get_participant_discord_ids(db, collab)
        results.append(
            CollabOut(
                id=collab.id,
                discord_ids=discord_ids,
                start_at_utc=collab.start_at_utc,
                reminder_sent=collab.reminder_sent,
                status=collab.status,
                thread_id=collab.thread_id,
            )
        )
    return results


@router.get("/upcoming/{discord_id}", response_model=list[CollabOut])
async def upcoming_collabs_for_user(discord_id: int, db: AsyncSession = Depends(get_db)) -> list[CollabOut]:
    """Feeds /cancel-collab's picker: the confirmed, future collabs this
    Discord user currently participates in."""
    collabs = await collab_repository.list_upcoming_for_user(db, discord_id, datetime.now(timezone.utc))
    results = []
    for collab in collabs:
        discord_ids = await collab_repository.get_participant_discord_ids(db, collab)
        results.append(
            CollabOut(
                id=collab.id,
                discord_ids=discord_ids,
                start_at_utc=collab.start_at_utc,
                reminder_sent=collab.reminder_sent,
                status=collab.status,
                thread_id=collab.thread_id,
            )
        )
    return results


@router.get("/{collab_id}", response_model=CollabOut)
async def get_collab(collab_id: int, db: AsyncSession = Depends(get_db)) -> CollabOut:
    """Lets the reminder scheduler re-check live state right before it
    fires, in case a participant withdrew via /cancel-collab after the
    reminder was scheduled."""
    collab = await collab_repository.get_collab(db, collab_id)
    if collab is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "collab not found")

    discord_ids = await collab_repository.get_participant_discord_ids(db, collab)
    return CollabOut(
        id=collab.id,
        discord_ids=discord_ids,
        start_at_utc=collab.start_at_utc,
        reminder_sent=collab.reminder_sent,
        status=collab.status,
        thread_id=collab.thread_id,
    )


@router.post("/{collab_id}/reminder-sent", status_code=204)
async def mark_reminder_sent(collab_id: int, db: AsyncSession = Depends(get_db)) -> None:
    await collab_repository.mark_reminder_sent(db, collab_id)
