from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_service_token
from app.repositories import user_repository
from app.schemas.user import UserOut, UserUpsert

router = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(require_service_token)])


@router.put("/{discord_id}", response_model=UserOut)
async def upsert_user(discord_id: int, payload: UserUpsert, db: AsyncSession = Depends(get_db)) -> UserOut:
    if payload.discord_id != discord_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "path/body discord_id mismatch")

    user = await user_repository.upsert_user(
        db, discord_id, payload.display_name, payload.timezone, payload.role
    )
    return UserOut(discord_id=user.discord_id, display_name=user.display_name, timezone=user.timezone, role=user.cached_role)


@router.get("/{discord_id}", response_model=UserOut)
async def get_user(discord_id: int, db: AsyncSession = Depends(get_db)) -> UserOut:
    user = await user_repository.get_by_discord_id(db, discord_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "user not registered")

    return UserOut(discord_id=user.discord_id, display_name=user.display_name, timezone=user.timezone, role=user.cached_role)
