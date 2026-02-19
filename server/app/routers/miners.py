"""Miner CRUD and actions (restart, power_off, power_on, realtime)."""
import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.auth import get_current_user
from app.models import User
from app.services import miner_service
from app.services.miner_service import get_miner_password
from app.models import Miner, Command, CommandType, CommandStatus
from app.websocket import broadcast_to_agent

router = APIRouter(prefix="/miners", tags=["miners"])


class MinerUpdate(BaseModel):
    worker1: str | None = None
    worker2: str | None = None
    worker3: str | None = None
    password: str | None = None


def _miner_to_dict(m: Miner) -> dict:
    return {
        "id": m.id,
        "mac": m.mac,
        "ip": m.ip,
        "model": m.model,
        "worker1": m.worker1,
        "worker2": m.worker2,
        "worker3": m.worker3,
        "web_ui_url": f"http://{m.ip}" if m.ip else None,
    }


@router.get("")
async def list_miners(
    farm_id: int | None = Query(None),
    agent_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List miners, optionally filtered by farm_id or agent_id."""
    miners = await miner_service.list_miners(db, farm_id=farm_id, agent_id=agent_id)
    return [_miner_to_dict(m) for m in miners]


@router.get("/{miner_id}")
async def get_miner(
    miner_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get miner detail (includes web_ui_url)."""
    miner = await miner_service.get_miner_by_id(db, miner_id)
    if not miner:
        raise HTTPException(status_code=404, detail="Miner not found")
    d = _miner_to_dict(miner)
    d["has_password"] = bool(miner.password_encrypted)
    return d


@router.patch("/{miner_id}")
async def update_miner(
    miner_id: int,
    data: MinerUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update miner (worker, password)."""
    miner = await miner_service.get_miner_by_id(db, miner_id)
    if not miner:
        raise HTTPException(status_code=404, detail="Miner not found")
    miner = await miner_service.update_miner(
        db, miner,
        worker1=data.worker1,
        worker2=data.worker2,
        worker3=data.worker3,
        password=data.password,
    )
    return _miner_to_dict(miner)


def _queue_command(db: AsyncSession, agent_id: int, miner_id: int, cmd_type: str, params: dict | None = None) -> Command:
    """Queue a command for the agent."""
    cmd = Command(
        agent_id=agent_id,
        miner_id=miner_id,
        type=cmd_type,
        params=params or {},
        status=CommandStatus.PENDING.value,
    )
    db.add(cmd)
    return cmd


def _broadcast_command(agent_id: int, miner: Miner, cmd_id: int, cmd_type: str):
    """Broadcast command to agent if connected."""
    payload = {
        "type": cmd_type,
        "command_id": cmd_id,
        "miner_mac": miner.mac,
        "password": get_miner_password(miner) or "",
    }
    asyncio.create_task(broadcast_to_agent(agent_id, payload))


@router.post("/{miner_id}/restart")
async def restart_miner(
    miner_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Trigger miner restart (queues command for agent)."""
    import asyncio

    miner = await miner_service.get_miner_by_id(db, miner_id)
    if not miner:
        raise HTTPException(status_code=404, detail="Miner not found")
    cmd = _queue_command(db, miner.agent_id, miner_id, CommandType.RESTART.value)
    await db.flush()
    _broadcast_command(miner.agent_id, miner, cmd.id, "restart")
    return {"status": "queued", "command_id": cmd.id}


@router.post("/{miner_id}/power_off")
async def power_off_miner(
    miner_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Power off miner (queues command for agent)."""
    miner = await miner_service.get_miner_by_id(db, miner_id)
    if not miner:
        raise HTTPException(status_code=404, detail="Miner not found")
    cmd = _queue_command(db, miner.agent_id, miner_id, CommandType.POWER_OFF.value)
    await db.flush()
    _broadcast_command(miner.agent_id, miner, cmd.id, "power_off")
    return {"status": "queued", "command_id": cmd.id}


@router.post("/{miner_id}/power_on")
async def power_on_miner(
    miner_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Power on miner (queues command for agent)."""
    miner = await miner_service.get_miner_by_id(db, miner_id)
    if not miner:
        raise HTTPException(status_code=404, detail="Miner not found")
    cmd = _queue_command(db, miner.agent_id, miner_id, CommandType.POWER_ON.value)
    await db.flush()
    _broadcast_command(miner.agent_id, miner, cmd.id, "power_on")
    return {"status": "queued", "command_id": cmd.id}


@router.get("/{miner_id}/realtime")
async def get_realtime(
    miner_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get live miner status (queues get_realtime; agent will respond)."""
    miner = await miner_service.get_miner_by_id(db, miner_id)
    if not miner:
        raise HTTPException(status_code=404, detail="Miner not found")
    # Queue command; in full impl, WebSocket would push result back
    # For now return placeholder - agent will update command result
    cmd = _queue_command(db, miner.agent_id, miner_id, CommandType.GET_REALTIME.value)
    await db.flush()
    return {"status": "queued", "command_id": cmd.id, "message": "Poll /commands/{id} for result"}
