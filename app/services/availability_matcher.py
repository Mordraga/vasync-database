from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories import user_repository as user_repo
from app.services.availability_resolver import get_user_day_segments
from app.services.domain import drop_excluded, intersect_segments
from app.services.timestamps import to_unix
from app.schemas.collab import MatchWindow


def _iter_dates(start_date: date, end_date: date):
    current = start_date
    while current <= end_date:
        yield current
        current += timedelta(days=1)


async def find_matches_for_date(
    session: AsyncSession, users: list[User], target_date: date
) -> list[MatchWindow]:
    per_user_segments = [
        await get_user_day_segments(session, user.id, target_date) for user in users
    ]
    shared = drop_excluded(intersect_segments(per_user_segments))

    # A single reference timezone is required to turn each segment into an
    # absolute timestamp; using the first participant's timezone is the
    # simplest MVP choice and matches how the confirmed time will actually
    # be announced to that group.
    reference_tz = users[0].timezone

    return [
        MatchWindow(
            date=target_date,
            status=segment.status,
            start_unix=to_unix(target_date, segment.start, reference_tz),
            end_unix=to_unix(target_date, segment.end, reference_tz),
        )
        for segment in shared
    ]


async def find_shared_windows(
    session: AsyncSession, discord_ids: list[int], start_date: date, end_date: date
) -> list[MatchWindow]:
    users = [await user_repo.get_by_discord_id(session, discord_id) for discord_id in discord_ids]
    known_users = [user for user in users if user is not None]
    if not known_users:
        return []

    windows: list[MatchWindow] = []
    for target_date in _iter_dates(start_date, end_date):
        windows.extend(await find_matches_for_date(session, known_users, target_date))
    return windows
