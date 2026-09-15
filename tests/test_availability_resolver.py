from datetime import date, time

from app.models.availability import RecurringAvailability
from app.models.enums import Recurrence, Status
from app.services.availability_resolver import pick_recurring_rule, rule_applies_on


def make_rule(**overrides) -> RecurringAvailability:
    defaults = dict(
        weekday=0,
        recurrence=Recurrence.WEEKLY,
        anchor_date=None,
        status=Status.YES,
        window_start=time(18, 0),
        window_end=time(22, 0),
    )
    defaults.update(overrides)
    return RecurringAvailability(**defaults)


def test_weekly_rule_applies_on_any_matching_weekday():
    rule = make_rule(weekday=0, recurrence=Recurrence.WEEKLY)  # Monday
    assert rule_applies_on(rule, date(2026, 1, 5))  # a Monday
    assert rule_applies_on(rule, date(2026, 1, 12))  # the following Monday


def test_weekly_rule_does_not_apply_on_other_weekdays():
    rule = make_rule(weekday=0, recurrence=Recurrence.WEEKLY)
    assert not rule_applies_on(rule, date(2026, 1, 6))  # Tuesday


def test_biweekly_rule_applies_only_every_other_week():
    anchor = date(2026, 1, 5)  # Monday, "on" week
    rule = make_rule(weekday=0, recurrence=Recurrence.BIWEEKLY, anchor_date=anchor)

    assert rule_applies_on(rule, anchor)
    assert not rule_applies_on(rule, anchor.replace(day=12))  # one week later: "off" week
    assert rule_applies_on(rule, anchor.replace(day=19))  # two weeks later: "on" again


def test_pick_recurring_rule_returns_first_match_or_none():
    monday_rule = make_rule(weekday=0)
    tuesday_rule = make_rule(weekday=1)

    assert pick_recurring_rule([monday_rule, tuesday_rule], date(2026, 1, 6)) is tuesday_rule
    assert pick_recurring_rule([monday_rule], date(2026, 1, 7)) is None
