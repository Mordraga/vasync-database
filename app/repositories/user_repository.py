from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def get_by_discord_id(session: AsyncSession, discord_id: int) -> User | None:
    result = await session.execute(select(User).where(User.discord_id == discord_id))
    return result.scalar_one_or_none()


async def upsert_user(
    session: AsyncSession, discord_id: int, display_name: str, timezone: str, role_name: str, is_staff: bool
) -> User:
    user = await get_by_discord_id(session, discord_id)
    if user is None:
        user = User(
            discord_id=discord_id,
            display_name=display_name,
            timezone=timezone,
            cached_role=role_name,
            cached_is_staff=is_staff,
        )
        session.add(user)
    else:
        user.display_name = display_name
        user.timezone = timezone
        user.cached_role = role_name
        user.cached_is_staff = is_staff

    await session.commit()
    await session.refresh(user)
    return user
