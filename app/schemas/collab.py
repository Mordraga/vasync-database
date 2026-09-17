from datetime import date, datetime

from pydantic import BaseModel

from app.models.enums import CollabStatus, Status


class MatchWindow(BaseModel):
    date: date
    status: Status
    start_unix: int
    end_unix: int


class CollabMatchOut(BaseModel):
    discord_ids: list[int]
    windows: list[MatchWindow]


class CollabProposeIn(BaseModel):
    initiator_discord_id: int
    other_discord_ids: list[int]
    start_at_utc: datetime
    thread_id: int | None = None


class CollabRespondIn(BaseModel):
    discord_id: int
    accept: bool


class CollabRespondOut(BaseModel):
    pending: bool
    status: CollabStatus | None
    accepted_discord_ids: list[int]
    declined_discord_ids: list[int]
    thread_id: int | None


class CollabCancelIn(BaseModel):
    discord_id: int


class CollabCancelOut(BaseModel):
    fully_cancelled: bool
    remaining_discord_ids: list[int]
    thread_id: int | None


class CollabOut(BaseModel):
    id: int
    discord_ids: list[int]
    start_at_utc: datetime
    reminder_sent: bool
    status: CollabStatus
    thread_id: int | None
