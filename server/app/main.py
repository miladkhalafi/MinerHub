"""FastAPI application."""
import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.routers import farms, agents, miners, ws, influx
from app.models import Farm, Agent, Miner, Command  # noqa: F401 - ensure models are registered


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: init DB. Shutdown: nothing."""
    await init_db()
    yield


app = FastAPI(
    title="Miner Agent API",
    description="Crypto miner monitoring - farms, agents, miners",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(farms.router)
app.include_router(agents.router)
app.include_router(miners.router)
app.include_router(ws.router)
app.include_router(influx.router)

# Serve frontend static files if built
_frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if _frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="frontend")


@app.get("/health")
async def health_check():
    """Health check."""
    return {"status": "ok"}
