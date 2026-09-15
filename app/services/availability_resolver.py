from datetime import date, time

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.availability import RecurringAvailability
from app.models.enums import Recurrence, Status
from app.repositories import availability_repository as availability_repo
from app.services.domain import TimeSegment, expand_day_segments


def rule_applies_on(rule: RecurringAvailability, target_date: date) -> bool:
    """Weekday + weekly/biweekly parity check (spec section 3)."""
    if rule.weekday != target_date.weekday():
        return False
    if rule.recurrence is Recurrence.WEEKLY or rule.anchor_date is None:
        return True

    weeks_since_anchor = (target_date - rule.anchor_date).days // 7
    return weeks_since_anchor % 2 == 0


def pick_recurring_rule(rules: list[RecurringAvailability], target_date: date) -> RecurringAvailability | None:
    return next((rule for rule in rules if rule_applies_on(rule, target_date)), None)


async def get_user_day_segments(session: AsyncSession, user_id: int, target_date: date) -> list[TimeSegment]:
    """Effective segments for one user on one date: an override wins over
    the matching recurring rule, and no rule at all means unavailable."""
    override = await availability_repo.get_override(session, user_id, target_date)
    if override is not None:
        return expand_day_segments(override.status, override.window_start, override.window_end)

    rules = await availability_repo.list_recurring_for_user(session, user_id)
    rule = pick_recurring_rule(rules, target_date)
    if rule is not None:
        return expand_day_segments(rule.status, rule.window_start, rule.window_end)

    return expand_day_segments(Status.NO, time.min, time.min)
