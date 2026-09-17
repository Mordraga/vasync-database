from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.roles import ServerRole


async def list_roles(session: AsyncSession) -> list[ServerRole]:
    result = await session.execute(select(ServerRole).order_by(ServerRole.name))
    return list(result.scalars().all())


async def create_role(session: AsyncSession, name: str, discord_role_id: int, is_staff: bool) -> ServerRole:
    role = ServerRole(name=name, discord_role_id=discord_role_id, is_staff=is_staff)
    session.add(role)
    await session.commit()
    await session.refresh(role)
    return role


async def delete_role(session: AsyncSession, role_id: int) -> bool:
    role = await session.get(ServerRole, role_id)
    if role is None:
        return False
    await session.delete(role)
    await session.commit()
    return True
