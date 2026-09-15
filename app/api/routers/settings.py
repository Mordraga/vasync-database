from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_service_token, require_staff
from app.repositories import settings_repository
from app.schemas.settings import BotSettingsOut, BotSettingsUpdate

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=BotSettingsOut, dependencies=[Depends(require_service_token)])
async def get_bot_settings(db: AsyncSession = Depends(get_db)) -> BotSettingsOut:
    """Read-only for any trusted caller (bot + dashboard) - no staff check,
    since reading the current reminder lead/match window isn't sensitive."""
    settings = await settings_repository.get_settings(db)
    return BotSettingsOut.model_validate(settings)


@router.put("", response_model=BotSettingsOut, dependencies=[Depends(require_staff)])
async def update_bot_settings(
    payload: BotSettingsUpdate, db: AsyncSession = Depends(get_db)
) -> BotSettingsOut:
    settings = await settings_repository.update_settings(db, payload)
    return BotSettingsOut.model_validate(settings)
