from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_service_token, require_staff
from app.repositories import settings_repository
from app.schemas.settings import BotSettingsOut, BotSettingsUpdate

router = APIRouter(prefix="/settings", tags=["settings"])


def _to_settings_out(settings) -> BotSettingsOut:
    return BotSettingsOut(
        reminder_lead_minutes=settings.reminder_lead_minutes,
        match_window_days=settings.match_window_days,
        live_poll_interval_minutes=settings.live_poll_interval_minutes,
        live_announce_channel_id=(
            str(settings.live_announce_channel_id) if settings.live_announce_channel_id is not None else None
        ),
    )


@router.get("", response_model=BotSettingsOut, dependencies=[Depends(require_service_token)])
async def get_bot_settings(db: AsyncSession = Depends(get_db)) -> BotSettingsOut:
    """Read-only for any trusted caller (bot + dashboard) - no staff check,
    since reading the current reminder lead/match window isn't sensitive."""
    settings = await settings_repository.get_settings(db)
    return _to_settings_out(settings)


@router.put("", response_model=BotSettingsOut, dependencies=[Depends(require_staff)])
async def update_bot_settings(
    payload: BotSettingsUpdate, db: AsyncSession = Depends(get_db)
) -> BotSettingsOut:
    settings = await settings_repository.update_settings(db, payload)
    return _to_settings_out(settings)
