from datetime import date, time

from pydantic import BaseModel

from app.models.enums import Recurrence, Status


class RecurringRuleIn(BaseModel):
    weekday: int
    recurrence: Recurrence = Recurrence.WEEKLY
    anchor_date: date | None = None
    status: Status
    window_start: time
    window_end: time


class RecurringRuleOut(RecurringRuleIn):
    id: int

    model_config = {"from_attributes": True}


class RecurringRulesReplace(BaseModel):
    """Full replacement of a user's recurring rule set (dashboard save)."""

    rules: list[RecurringRuleIn]


class OverrideIn(BaseModel):
    override_date: date
    status: Status
    window_start: time
    window_end: time


class OverrideOut(OverrideIn):
    id: int

    model_config = {"from_attributes": True}
