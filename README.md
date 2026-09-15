# vasync-database

FastAPI + Postgres service that is the source of truth for the VAsync
Scheduling Daemon: user registration, recurring/override availability, the
`/collab` matching engine, and confirmed-collab state. See
`VAsync_Scheduling_Daemon_MVP_Spec.docx` (in `vasync-dashboard/`) for the
product spec.

## Layout

- `app/models` - SQLAlchemy ORM tables.
- `app/schemas` - Pydantic request/response DTOs.
- `app/repositories` - atomic DB access functions (no business logic).
- `app/services/domain.py` - pure, DB-free scheduling math (the
  YES/MAYBE/NO degrade rule + cross-user combine rule). Unit-test this
  directly.
- `app/services/availability_resolver.py` - per-user, per-date segment
  resolution (override-over-recurring).
- `app/services/availability_matcher.py` - multi-user intersection +
  timestamp resolution for `/collab`.
- `app/api/routers` - FastAPI route handlers; thin, delegate to services.
- `app/core/security.py` - Discord role -> internal Role, and the
  "can this caller edit this user" rule.

## Running locally

```bash
cp .env.example .env   # fill in DATABASE_URL, guild/role IDs, SERVICE_TOKEN
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

## Auth model

The bot and dashboard are the only two clients. Every request must carry:

- `X-Service-Token` - shared secret from `SERVICE_TOKEN`.
- `X-Discord-User-Id`, `X-Discord-Guild-Id`, `X-Discord-Role-Ids` - the
  caller's already-verified Discord identity (the bot reads this off the
  interaction; the dashboard reads it off its own OAuth session).

This service resolves those headers into a `Role` and enforces "entities/
researchers can only edit their own availability" itself, so that rule
lives in exactly one place.

## Tests

```bash
pytest
```

`tests/` covers the pure/DB-free logic: the availability degrade + combine
rules in `domain.py`, recurring-rule weekly/biweekly matching, timezone
resolution, and role/permission checks. No database is required to run
them. Matcher/repository code that hits Postgres isn't covered yet -
that needs an integration setup (e.g. a docker-compose Postgres).
