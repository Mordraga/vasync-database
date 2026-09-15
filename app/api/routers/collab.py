from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_service_token
from app.repositories import collab_repository
from app.services.availability_matcher import find_shared_windows
from app.schemas.collab import CollabConfirmIn, CollabMatchOut, CollabOut

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


@router.post("/confirm", response_model=CollabOut)
async def confirm_collab(payload: CollabConfirmIn, db: AsyncSession = Depends(get_db)) -> CollabOut:
    collab = await collab_repository.create_confirmed_collab(db, payload.discord_ids, payload.start_at_utc)
    return CollabOut(
        id=collab.id,
        discord_ids=payload.discord_ids,
        start_at_utc=collab.start_at_utc,
        reminder_sent=collab.reminder_sent,
    )


@router.get("/upcoming", response_model=list[CollabOut])
async def upcoming_collabs(db: AsyncSession = Depends(get_db)) -> list[CollabOut]:
    """Lets the bot rehydrate reminders on startup after a restart."""
    collabs = await collab_repository.list_upcoming_unreminded(db, datetime.now(timezone.utc))
    results = []
    for collab in collabs:
        discord_ids = await collab_repository.get_participant_discord_ids(db, collab)
        results.append(
            CollabOut(id=collab.id, discord_ids=discord_ids, start_at_utc=collab.start_at_utc, reminder_sent=collab.reminder_sent)
        )
    return results


@router.post("/{collab_id}/reminder-sent", status_code=204)
async def mark_reminder_sent(collab_id: int, db: AsyncSession = Depends(get_db)) -> None:
    await collab_repository.mark_reminder_sent(db, collab_id)
