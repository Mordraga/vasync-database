from pydantic import BaseModel, Field


class BotSettingsOut(BaseModel):
    reminder_lead_minutes: int
    match_window_days: int
    live_poll_interval_minutes: int
    # str, not int: Discord channel snowflakes exceed JS's
    # Number.MAX_SAFE_INTEGER, so the dashboard needs this as a string to
    # round-trip without precision loss. Pydantic coerces the ORM column's
    # plain int for us here (lax mode allows int -> str).
    live_announce_channel_id: str | None

    model_config = {"from_attributes": True}


class BotSettingsUpdate(BaseModel):
    reminder_lead_minutes: int = Field(ge=1, le=24 * 60)
    match_window_days: int = Field(ge=1, le=90)
    live_poll_interval_minutes: int = Field(ge=1, le=60)
    live_announce_channel_id: str | None = None
