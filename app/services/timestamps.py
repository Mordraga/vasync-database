from datetime import date, datetime, time
from zoneinfo import ZoneInfo


def to_unix(target_date: date, moment: time, tz_name: str) -> int:
    """Resolve a wall-clock date+time in ``tz_name`` to a Unix timestamp.

    This is the one place timezone math happens in the whole system: the
    dashboard and bot only ever handle the resulting absolute timestamp
    (spec section 3 - "no timezone rendering logic" downstream).
    """
    localized = datetime.combine(target_date, moment, tzinfo=ZoneInfo(tz_name))
    return int(localized.timestamp())
