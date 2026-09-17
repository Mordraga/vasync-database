from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_service_token, require_staff
from app.repositories import roles_repository
from app.schemas.roles import ServerRoleCreate, ServerRoleOut

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("", response_model=list[ServerRoleOut], dependencies=[Depends(require_service_token)])
async def list_roles(db: AsyncSession = Depends(get_db)) -> list[ServerRoleOut]:
    """Read-only for any trusted caller - the bot and dashboard both need
    this to resolve a member's role, and the mapping itself isn't sensitive."""
    roles = await roles_repository.list_roles(db)
    return [ServerRoleOut.model_validate(role) for role in roles]


@router.post("", response_model=ServerRoleOut, dependencies=[Depends(require_staff)])
async def create_role(payload: ServerRoleCreate, db: AsyncSession = Depends(get_db)) -> ServerRoleOut:
    try:
        role = await roles_repository.create_role(db, payload.name, payload.discord_role_id, payload.is_staff)
    except IntegrityError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "a role with that name or Discord role ID already exists"
        ) from exc
    return ServerRoleOut.model_validate(role)


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_staff)])
async def delete_role(role_id: int, db: AsyncSession = Depends(get_db)) -> None:
    deleted = await roles_repository.delete_role(db, role_id)
    if not deleted:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "role not found")
