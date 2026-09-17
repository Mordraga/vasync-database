from datetime import time

from app.models.enums import CollabStatus, Status
from app.services.domain import (
    DAY_END,
    DAY_START,
    TimeSegment,
    combine_statuses,
    drop_excluded,
    expand_day_segments,
    intersect_segments,
    is_collab_still_viable,
    merge_adjacent,
    resolve_collab_outcome,
)


def test_combine_statuses_any_no_wins():
    assert combine_statuses([Status.NO, Status.MAYBE, Status.YES]) is Status.NO


def test_combine_statuses_any_maybe_without_no():
    assert combine_statuses([Status.MAYBE, Status.YES]) is Status.MAYBE


def test_combine_statuses_all_yes_is_best():
    assert combine_statuses([Status.YES, Status.YES]) is Status.YES


def test_expand_day_segments_no_ignores_window():
    segments = expand_day_segments(Status.NO, time(18, 0), time(22, 0))
    assert segments == [TimeSegment(DAY_START, DAY_END, Status.NO)]


def test_expand_day_segments_yes_degrades_to_maybe_outside_window():
    segments = expand_day_segments(Status.YES, time(18, 0), time(22, 0))
    assert segments == [
        TimeSegment(DAY_START, time(18, 0), Status.MAYBE),
        TimeSegment(time(18, 0), time(22, 0), Status.YES),
        TimeSegment(time(22, 0), DAY_END, Status.MAYBE),
    ]


def test_expand_day_segments_maybe_degrades_to_no_outside_window():
    segments = expand_day_segments(Status.MAYBE, time(18, 0), time(22, 0))
    assert segments == [
        TimeSegment(DAY_START, time(18, 0), Status.NO),
        TimeSegment(time(18, 0), time(22, 0), Status.MAYBE),
        TimeSegment(time(22, 0), DAY_END, Status.NO),
    ]


def test_expand_day_segments_window_touching_start_skips_leading_segment():
    segments = expand_day_segments(Status.YES, DAY_START, time(22, 0))
    assert segments == [
        TimeSegment(DAY_START, time(22, 0), Status.YES),
        TimeSegment(time(22, 0), DAY_END, Status.MAYBE),
    ]


def test_intersect_segments_any_no_excludes_that_span():
    # User A is YES all day; user B is NO until noon, then YES.
    user_a = [TimeSegment(DAY_START, DAY_END, Status.YES)]
    user_b = [TimeSegment(DAY_START, time(12, 0), Status.NO), TimeSegment(time(12, 0), DAY_END, Status.YES)]

    combined = intersect_segments([user_a, user_b])

    assert combined == [
        TimeSegment(DAY_START, time(12, 0), Status.NO),
        TimeSegment(time(12, 0), DAY_END, Status.YES),
    ]


def test_drop_excluded_keeps_only_maybe_and_yes():
    segments = [
        TimeSegment(DAY_START, time(12, 0), Status.NO),
        TimeSegment(time(12, 0), time(18, 0), Status.MAYBE),
        TimeSegment(time(18, 0), DAY_END, Status.YES),
    ]
    assert drop_excluded(segments) == segments[1:]


def test_merge_adjacent_collapses_equal_consecutive_statuses():
    segments = [
        TimeSegment(time(9, 0), time(12, 0), Status.MAYBE),
        TimeSegment(time(12, 0), time(15, 0), Status.MAYBE),
        TimeSegment(time(15, 0), time(18, 0), Status.YES),
    ]
    assert merge_adjacent(segments) == [
        TimeSegment(time(9, 0), time(15, 0), Status.MAYBE),
        TimeSegment(time(15, 0), time(18, 0), Status.YES),
    ]


def test_resolve_collab_outcome_none_while_someone_pending():
    participants = [(1, True, True), (2, False, True), (3, False, None)]
    assert resolve_collab_outcome(participants) is None


def test_resolve_collab_outcome_confirmed_with_a_decline():
    participants = [(1, True, True), (2, False, True), (3, False, False)]
    outcome = resolve_collab_outcome(participants)
    assert outcome.status is CollabStatus.CONFIRMED
    assert outcome.accepted_discord_ids == [1, 2]
    assert outcome.declined_discord_ids == [3]


def test_resolve_collab_outcome_cancelled_when_everyone_declines():
    participants = [(1, True, True), (2, False, False), (3, False, False)]
    outcome = resolve_collab_outcome(participants)
    assert outcome.status is CollabStatus.CANCELLED
    assert outcome.accepted_discord_ids == [1]
    assert outcome.declined_discord_ids == [2, 3]


def test_is_collab_still_viable_needs_two_or_more():
    assert is_collab_still_viable([1, 2]) is True
    assert is_collab_still_viable([1]) is False
    assert is_collab_still_viable([]) is False
