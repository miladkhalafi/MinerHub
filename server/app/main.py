"""FastAPI application."""
import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import init_db, async_session_maker
from app.routers import farms, agents, miners, ws, influx, auth, users
from app.models import Farm, Agent, Miner, Command, User  # noqa: F401 - ensure models are registered
from app.services import user_service


async def bootstrap_admin():
    """Create default admin user if no users exist."""
    async with async_session_maker() as db:
        count = await user_service.count_users(db)
        if count > 0:
            return
        admin_email = os.getenv("ADMIN_EMAIL", "admin@localhost")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin")
        await user_service.create_user(db, admin_email, admin_password, role="admin")
        await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: init DB, bootstrap admin. Shutdown: nothing."""
    await init_db()
    await bootstrap_admin()
    yield


app = FastAPI(
    title="Miner Agent API",
    description="Crypto miner monitoring - farms, agents, miners",
    version="0.1.0",
    lifespan=lifespan,
)

_cors_origins = os.getenv("CORS_ORIGINS", "*")
_cors_origins_list = [o.strip() for o in _cors_origins.split(",") if o.strip()] if _cors_origins != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(farms.router, prefix="/api")
app.include_router(agents.router, prefix="/api")
app.include_router(miners.router, prefix="/api")
app.include_router(ws.router, prefix="/api")
app.include_router(influx.router, prefix="/api")

# Serve frontend static files if built
_frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if _frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="frontend")


@app.get("/health")
async def health_check():
    """Health check."""
    return {"status": "ok"}
