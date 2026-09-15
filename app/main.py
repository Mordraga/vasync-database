from fastapi import FastAPI

from app.api.routers import availability, collab, settings, users

app = FastAPI(title="VAsync Scheduling Daemon", version="0.1.0")

app.include_router(users.router)
app.include_router(availability.router)
app.include_router(collab.router)
app.include_router(settings.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
