from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

SETTINGS_SINGLETON_ID = 1


class BotSettings(Base):
    """Singleton row (id is always 1) holding the bot-tunable knobs staff
    can change from the dashboard admin panel, instead of hardcoded
    constants in vasync-bot."""

    __tablename__ = "bot_settings"

    id: Mapped[int] = mapped_column(primary_key=True, default=SETTINGS_SINGLETON_ID)
    reminder_lead_minutes: Mapped[int] = mapped_column(default=15)
    match_window_days: Mapped[int] = mapped_column(default=14)
