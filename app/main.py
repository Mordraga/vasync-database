import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi import FastAPI

from app.api.routers import availability, collab, roles, settings, users

REPO_ROOT = Path(__file__).resolve().parent.parent


def _upgrade_database() -> None:
    """Blocking - alembic's env.py drives its own asyncio.run(), so this
    must run off the event loop thread (see lifespan below)."""
    cfg = Config(str(REPO_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(REPO_ROOT / "migrations"))
    command.upgrade(cfg, "head")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs on every boot regardless of how the process was started, since
    # Railway's start command isn't a reliable place to chain this (its
    # config-as-code file isn't honored by GitHub-triggered deploys here).
    await asyncio.to_thread(_upgrade_database)
    yield


app = FastAPI(title="VAsync Scheduling Daemon", version="0.1.0", lifespan=lifespan)

app.include_router(users.router)
app.include_router(availability.router)
app.include_router(collab.router)
app.include_router(settings.router)
app.include_router(roles.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
