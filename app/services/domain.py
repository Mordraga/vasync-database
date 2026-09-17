"""Pure, side-effect-free scheduling logic.

Nothing in this module touches the database, the clock, or FastAPI. Every
function is a small, independently testable unit so the availability
contract (spec section 2) stays correct without needing an integration
test harness.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import time

from app.models.enums import CollabStatus, Status

DAY_START = time.min
DAY_END = time.max


@dataclass(frozen=True, slots=True)
class TimeSegment:
    start: time
    end: time
    status: Status


def combine_statuses(statuses: Iterable[Status]) -> Status:
    """Any NO kills a slot, any MAYBE makes it possible, all YES is best."""
    return min(statuses)


def expand_day_segments(status: Status, window_start: time, window_end: time) -> list[TimeSegment]:
    """Turn one day's base status + preferred window into ordered segments
    spanning the full day, applying the degrade rule from spec section 2:

    - YES day: inside the window stays YES, outside degrades to MAYBE.
    - MAYBE day: inside the window stays MAYBE, outside degrades to NO.
    - NO day: NO all day regardless of window.
    """
    if status is Status.NO:
        return [TimeSegment(DAY_START, DAY_END, Status.NO)]

    outside_status = Status.MAYBE if status is Status.YES else Status.NO

    segments: list[TimeSegment] = []
    if window_start > DAY_START:
        segments.append(TimeSegment(DAY_START, window_start, outside_status))
    if window_end > window_start:
        segments.append(TimeSegment(window_start, window_end, status))
    if window_end < DAY_END:
        segments.append(TimeSegment(window_end, DAY_END, outside_status))
    return segments


def _breakpoints(segment_lists: Iterable[list[TimeSegment]]) -> list[time]:
    points = {DAY_START, DAY_END}
    for segments in segment_lists:
        for segment in segments:
            points.add(segment.start)
            points.add(segment.end)
    return sorted(points)


def _status_at(segments: list[TimeSegment], moment: time) -> Status:
    for segment in segments:
        if segment.start <= moment < segment.end:
            return segment.status
    return Status.NO


def intersect_segments(segment_lists: list[list[TimeSegment]]) -> list[TimeSegment]:
    """Sweep every participant's day segments and combine them into a
    single timeline of the effective (dominant-lowest) status per
    sub-interval."""
    if not segment_lists:
        return []

    points = _breakpoints(segment_lists)
    raw: list[TimeSegment] = []
    for start, end in zip(points, points[1:]):
        combined = combine_statuses(_status_at(segments, start) for segments in segment_lists)
        raw.append(TimeSegment(start, end, combined))
    return merge_adjacent(raw)


def merge_adjacent(segments: list[TimeSegment]) -> list[TimeSegment]:
    """Collapse consecutive segments that share a status into one span."""
    merged: list[TimeSegment] = []
    for segment in segments:
        if merged and merged[-1].status is segment.status and merged[-1].end == segment.start:
            merged[-1] = TimeSegment(merged[-1].start, segment.end, segment.status)
        else:
            merged.append(segment)
    return merged


def drop_excluded(segments: list[TimeSegment]) -> list[TimeSegment]:
    """Any-NO slots are not matches at all; keep only MAYBE/YES spans."""
    return [segment for segment in segments if segment.status is not Status.NO]


@dataclass(frozen=True, slots=True)
class CollabOutcome:
    """The resolved result of a proposed collab once every invited
    participant has responded (spec: mutual confirmation). Only ever
    CONFIRMED or CANCELLED - PENDING is represented by resolve_collab_outcome
    returning None instead of an instance of this class."""

    status: CollabStatus
    accepted_discord_ids: list[int]
    declined_discord_ids: list[int]


def resolve_collab_outcome(
    participants: list[tuple[int, bool, bool | None]],
) -> CollabOutcome | None:
    """``participants`` is (discord_id, is_initiator, accepted) tuples.

    Returns None while any non-initiator participant still hasn't responded
    (accepted is None). Once everyone has responded: CONFIRMED if at least
    one non-initiator accepted, CANCELLED if they all declined.
    """
    if any(not is_initiator and accepted is None for _, is_initiator, accepted in participants):
        return None

    accepted_ids = [discord_id for discord_id, _, accepted in participants if accepted]
    declined_ids = [
        discord_id for discord_id, is_initiator, accepted in participants if not is_initiator and not accepted
    ]
    status = CollabStatus.CONFIRMED if is_collab_still_viable(accepted_ids) else CollabStatus.CANCELLED
    return CollabOutcome(status=status, accepted_discord_ids=accepted_ids, declined_discord_ids=declined_ids)


def is_collab_still_viable(remaining_discord_ids: list[int]) -> bool:
    """A collab needs at least two people left to be worth keeping - used
    both when finalizing an initial proposal and when someone withdraws
    from an already-confirmed collab via /cancel-collab."""
    return len(remaining_discord_ids) >= 2
