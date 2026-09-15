from pydantic import BaseModel

from app.models.enums import Role


class UserUpsert(BaseModel):
    discord_id: int
    display_name: str
    timezone: str = "UTC"
    role: Role


class UserOut(BaseModel):
    discord_id: int
    display_name: str
    timezone: str
    role: Role

    model_config = {"from_attributes": True}
