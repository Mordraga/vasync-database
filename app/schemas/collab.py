from datetime import date, datetime

from pydantic import BaseModel

from app.models.enums import Status


class MatchWindow(BaseModel):
    date: date
    status: Status
    start_unix: int
    end_unix: int


class CollabMatchOut(BaseModel):
    discord_ids: list[int]
    windows: list[MatchWindow]


class CollabConfirmIn(BaseModel):
    discord_ids: list[int]
    start_at_utc: datetime


class CollabOut(BaseModel):
    id: int
    discord_ids: list[int]
    start_at_utc: datetime
    reminder_sent: bool
