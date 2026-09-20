from pydantic import BaseModel, Field


class UserUpsert(BaseModel):
    discord_id: int
    display_name: str
    timezone: str = "UTC"
    role_ids: list[int]


class UserOut(BaseModel):
    discord_id: int
    display_name: str
    timezone: str
    role: str
    is_staff: bool
    twitch_username: str | None
    is_live: bool

    model_config = {"from_attributes": True}


class TwitchLinkUpdate(BaseModel):
    # Twitch logins are 4-25 chars, letters/digits/underscore. None clears
    # a previously-registered link.
    twitch_username: str | None = Field(default=None, pattern=r"^[A-Za-z0-9_]{4,25}$")


class LiveStatusUpdate(BaseModel):
    is_live: bool


class TwitchLinkedUserOut(BaseModel):
    discord_id: int
    twitch_username: str

    model_config = {"from_attributes": True}


class LiveEntityOut(BaseModel):
    discord_id: int
    display_name: str
    twitch_username: str

    model_config = {"from_attributes": True}
