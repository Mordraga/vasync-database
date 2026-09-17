import enum


class Status(enum.IntEnum):
    """Availability contract from the MVP spec, ordered by severity.

    Lower value wins when combining statuses: any NO dominates, any
    remaining MAYBE dominates, all YES is the best case. Keeping this an
    IntEnum lets both the per-day degrade logic and the cross-user match
    logic reuse a single ``min()``-based combine function.
    """

    NO = 0
    MAYBE = 1
    YES = 2


class Recurrence(enum.StrEnum):
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"


class CollabStatus(enum.StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
