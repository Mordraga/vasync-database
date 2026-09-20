from sqlalchemy.ext.asyncio import AsyncSession

from app.models.settings import SETTINGS_SINGLETON_ID, BotSettings
from app.schemas.settings import BotSettingsUpdate


async def get_settings(session: AsyncSession) -> BotSettings:
    settings = await session.get(BotSettings, SETTINGS_SINGLETON_ID)
    if settings is None:
        settings = BotSettings(id=SETTINGS_SINGLETON_ID)
        session.add(settings)
        await session.commit()
        await session.refresh(settings)
    return settings


async def update_settings(session: AsyncSession, update: BotSettingsUpdate) -> BotSettings:
    settings = await get_settings(session)
    settings.reminder_lead_minutes = update.reminder_lead_minutes
    settings.match_window_days = update.match_window_days
    settings.live_poll_interval_minutes = update.live_poll_interval_minutes
    await session.commit()
    await session.refresh(settings)
    return settings
