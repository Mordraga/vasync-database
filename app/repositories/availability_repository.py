from datetime import date

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.availability import RecurringAvailability
from app.models.override import AvailabilityOverride
from app.schemas.availability import OverrideIn, RecurringRuleIn


async def list_recurring_for_user(session: AsyncSession, user_id: int) -> list[RecurringAvailability]:
    result = await session.execute(
        select(RecurringAvailability).where(RecurringAvailability.user_id == user_id)
    )
    return list(result.scalars().all())


async def replace_recurring_for_user(
    session: AsyncSession, user_id: int, rules: list[RecurringRuleIn]
) -> list[RecurringAvailability]:
    """Full replace so the dashboard can save a user's whole week in one
    call without reconciling individual row diffs."""
    await session.execute(delete(RecurringAvailability).where(RecurringAvailability.user_id == user_id))

    rows = [RecurringAvailability(user_id=user_id, **rule.model_dump()) for rule in rules]
    session.add_all(rows)
    await session.commit()

    for row in rows:
        await session.refresh(row)
    return rows


async def get_override(session: AsyncSession, user_id: int, target_date: date) -> AvailabilityOverride | None:
    result = await session.execute(
        select(AvailabilityOverride).where(
            AvailabilityOverride.user_id == user_id,
            AvailabilityOverride.override_date == target_date,
        )
    )
    return result.scalar_one_or_none()


async def upsert_override(
    session: AsyncSession, user_id: int, override: OverrideIn
) -> AvailabilityOverride:
    existing = await get_override(session, user_id, override.override_date)
    if existing is None:
        existing = AvailabilityOverride(user_id=user_id, **override.model_dump())
        session.add(existing)
    else:
        existing.status = override.status
        existing.window_start = override.window_start
        existing.window_end = override.window_end

    await session.commit()
    await session.refresh(existing)
    return existing


async def delete_override(session: AsyncSession, user_id: int, target_date: date) -> None:
    await session.execute(
        delete(AvailabilityOverride).where(
            AvailabilityOverride.user_id == user_id,
            AvailabilityOverride.override_date == target_date,
        )
    )
    await session.commit()


async def list_overrides_for_user(session: AsyncSession, user_id: int) -> list[AvailabilityOverride]:
    result = await session.execute(
        select(AvailabilityOverride).where(AvailabilityOverride.user_id == user_id)
    )
    return list(result.scalars().all())
