from pydantic import BaseModel


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

    model_config = {"from_attributes": True}
