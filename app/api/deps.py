from collections.abc import AsyncIterator
from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.core.security import IdentityError, assert_guild, resolve_role
from app.db.session import get_session
from app.models.enums import Role


async def get_db() -> AsyncIterator[AsyncSession]:
    async for session in get_session():
        yield session


@dataclass(frozen=True, slots=True)
class Caller:
    discord_id: int
    role: Role


async def require_service_token(
    x_service_token: str = Header(...), settings: Settings = Depends(get_settings)
) -> None:
    if x_service_token != settings.service_token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid service token")


async def get_caller(
    x_discord_user_id: int = Header(...),
    x_discord_guild_id: int = Header(...),
    x_discord_role_ids: str = Header(default=""),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_service_token),
) -> Caller:
    role_ids = {int(role_id) for role_id in x_discord_role_ids.split(",") if role_id}
    try:
        assert_guild(x_discord_guild_id, settings)
        role = resolve_role(role_ids, settings)
    except IdentityError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc)) from exc

    return Caller(discord_id=x_discord_user_id, role=role)


async def require_staff(caller: Caller = Depends(get_caller)) -> Caller:
    if caller.role is not Role.STAFF:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "staff role required")
    return caller
