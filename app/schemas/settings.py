from pydantic import BaseModel, Field


class BotSettingsOut(BaseModel):
    reminder_lead_minutes: int
    match_window_days: int
    live_poll_interval_minutes: int

    model_config = {"from_attributes": True}


class BotSettingsUpdate(BaseModel):
    reminder_lead_minutes: int = Field(ge=1, le=24 * 60)
    match_window_days: int = Field(ge=1, le=90)
    live_poll_interval_minutes: int = Field(ge=1, le=60)
