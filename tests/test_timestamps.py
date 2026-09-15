from datetime import date, datetime, time, timezone

from app.services.timestamps import to_unix


def test_to_unix_utc_matches_stdlib_calculation():
    expected = int(datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc).timestamp())
    assert to_unix(date(2026, 6, 1), time(12, 0), "UTC") == expected


def test_to_unix_accounts_for_non_utc_offset():
    # Chicago is UTC-5 during daylight saving (June), so noon there is
    # 17:00 UTC - a 5 hour / 18000 second difference from the UTC case.
    utc_noon = to_unix(date(2026, 6, 1), time(12, 0), "UTC")
    chicago_noon = to_unix(date(2026, 6, 1), time(12, 0), "America/Chicago")
    assert chicago_noon - utc_noon == 5 * 3600
