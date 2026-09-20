from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import Caller, get_caller, get_db, require_service_token
from app.core.security import IdentityError, can_modify_user, pick_role
from app.repositories import roles_repository, user_repository
from app.schemas.user import (
    LiveEntityOut,
    LiveStatusUpdate,
    TwitchLinkedUserOut,
    TwitchLinkUpdate,
    UserOut,
    UserUpsert,
)

router = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(require_service_token)])


def _to_user_out(user) -> UserOut:
    return UserOut(
        discord_id=user.discord_id,
        display_name=user.display_name,
        timezone=user.timezone,
        role=user.cached_role,
        is_staff=user.cached_is_staff,
        twitch_username=user.twitch_username,
        is_live=user.is_live,
    )


# Registered before /{discord_id} - a literal path segment like "live"
# would otherwise be swallowed by the parameterized route and fail int
# coercion instead of matching here.
@router.get("/live", response_model=list[LiveEntityOut])
async def list_live_entities(db: AsyncSession = Depends(get_db)) -> list[LiveEntityOut]:
    """Read-only for any trusted caller - same trust level as /settings."""
    entities = await user_repository.list_live_entities(db)
    return [LiveEntityOut.model_validate(user) for user in entities]


@router.get("/twitch-linked", response_model=list[TwitchLinkedUserOut])
async def list_twitch_linked(db: AsyncSession = Depends(get_db)) -> list[TwitchLinkedUserOut]:
    """vasync-bot's live poller calls this each cycle to know who to check
    against Twitch's Get Streams API."""
    entities = await user_repository.list_twitch_linked_entities(db)
    return [TwitchLinkedUserOut.model_validate(user) for user in entities]


@router.put("/{discord_id}", response_model=UserOut)
async def upsert_user(discord_id: int, payload: UserUpsert, db: AsyncSession = Depends(get_db)) -> UserOut:
    if payload.discord_id != discord_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "path/body discord_id mismatch")

    configured_roles = await roles_repository.list_roles(db)
    try:
        role = pick_role(set(payload.role_ids), configured_roles)
    except IdentityError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc

    user = await user_repository.upsert_user(
        db, discord_id, payload.display_name, payload.timezone, role.name, role.is_staff
    )
    return _to_user_out(user)


@router.get("/{discord_id}", response_model=UserOut)
async def get_user(discord_id: int, db: AsyncSession = Depends(get_db)) -> UserOut:
    user = await user_repository.get_by_discord_id(db, discord_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "user not registered")
    return _to_user_out(user)


@router.put("/{discord_id}/twitch", response_model=UserOut)
async def update_twitch_link(
    discord_id: int,
    payload: TwitchLinkUpdate,
    db: AsyncSession = Depends(get_db),
    caller: Caller = Depends(get_caller),
) -> UserOut:
    if not can_modify_user(caller.discord_id, caller.is_staff, discord_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "cannot modify another user's Twitch link")

    user = await user_repository.set_twitch_username(db, discord_id, payload.twitch_username)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "user not registered")
    return _to_user_out(user)


@router.put("/{discord_id}/live-status", response_model=UserOut)
async def update_live_status(
    discord_id: int, payload: LiveStatusUpdate, db: AsyncSession = Depends(get_db)
) -> UserOut:
    """vasync-bot only (service token, no per-user caller identity) - this
    is machine-pushed state from the Twitch poller, not a user action."""
    user = await user_repository.set_live_status(db, discord_id, payload.is_live)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "user not registered")
    return _to_user_out(user)
