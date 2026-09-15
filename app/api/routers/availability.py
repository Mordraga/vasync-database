from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import Caller, get_caller, get_db
from app.core.security import can_modify_user
from app.repositories import availability_repository, user_repository
from app.schemas.availability import (
    OverrideIn,
    OverrideOut,
    RecurringRuleOut,
    RecurringRulesReplace,
)

router = APIRouter(prefix="/users/{discord_id}/availability", tags=["availability"])


async def _resolve_user_id(db: AsyncSession, discord_id: int, caller: Caller) -> int:
    if not can_modify_user(caller.discord_id, caller.role, discord_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "cannot modify another user's availability")

    user = await user_repository.get_by_discord_id(db, discord_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "user not registered")
    return user.id


@router.get("", response_model=list[RecurringRuleOut])
async def list_recurring(
    discord_id: int, db: AsyncSession = Depends(get_db), caller: Caller = Depends(get_caller)
) -> list[RecurringRuleOut]:
    user_id = await _resolve_user_id(db, discord_id, caller)
    rules = await availability_repository.list_recurring_for_user(db, user_id)
    return [RecurringRuleOut.model_validate(rule) for rule in rules]


@router.put("", response_model=list[RecurringRuleOut])
async def replace_recurring(
    discord_id: int,
    payload: RecurringRulesReplace,
    db: AsyncSession = Depends(get_db),
    caller: Caller = Depends(get_caller),
) -> list[RecurringRuleOut]:
    user_id = await _resolve_user_id(db, discord_id, caller)
    rules = await availability_repository.replace_recurring_for_user(db, user_id, payload.rules)
    return [RecurringRuleOut.model_validate(rule) for rule in rules]


@router.put("/overrides/{override_date}", response_model=OverrideOut)
async def upsert_override(
    discord_id: int,
    override_date: date,
    payload: OverrideIn,
    db: AsyncSession = Depends(get_db),
    caller: Caller = Depends(get_caller),
) -> OverrideOut:
    if payload.override_date != override_date:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "path/body override_date mismatch")

    user_id = await _resolve_user_id(db, discord_id, caller)
    override = await availability_repository.upsert_override(db, user_id, payload)
    return OverrideOut.model_validate(override)


@router.delete("/overrides/{override_date}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_override(
    discord_id: int,
    override_date: date,
    db: AsyncSession = Depends(get_db),
    caller: Caller = Depends(get_caller),
) -> None:
    user_id = await _resolve_user_id(db, discord_id, caller)
    await availability_repository.delete_override(db, user_id, override_date)
