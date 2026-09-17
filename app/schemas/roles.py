from pydantic import BaseModel


class ServerRoleOut(BaseModel):
    id: int
    name: str
    discord_role_id: int
    is_staff: bool

    model_config = {"from_attributes": True}


class ServerRoleCreate(BaseModel):
    name: str
    discord_role_id: int
    is_staff: bool = False
