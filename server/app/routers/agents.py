"""Agent CRUD, install/uninstall scripts."""
import os
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import get_current_user
from app.models import User
from app.services import agent_service, farm_service
from app.models import Agent

router = APIRouter(tags=["agents"])


def _get_server_url() -> str:
    return os.getenv("SERVER_URL", "http://localhost:8000").rstrip("/")


# --- Agent registration ---

@router.post("/farms/{farm_id}/agents", status_code=201)
async def register_agent(
    farm_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Register a new agent for a farm. Returns token and agent_id."""
    farm = await farm_service.get_farm(db, farm_id)
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    # Check if farm already has an agent
    existing = await agent_service.get_agent_for_farm(db, farm_id)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Farm already has an agent (id={existing.id}). One agent per farm.",
        )

    agent = await agent_service.create_agent(db, farm_id)
    return {
        "id": agent.id,
        "token": agent.token,
        "install_url": f"{_get_server_url()}/agents/install?token={agent.token}",
        "uninstall_url": f"{_get_server_url()}/agents/uninstall?token={agent.token}",
        "install_script": f"curl -sSL '{_get_server_url()}/agents/install?token={agent.token}' | bash",
        "uninstall_script": f"curl -sSL '{_get_server_url()}/agents/uninstall?token={agent.token}' | bash",
    }


# --- Install / Uninstall scripts ---

@router.get("/agents/download")
async def download_agent(
    token: str = Query(..., description="Agent token"),
    db: AsyncSession = Depends(get_db),
):
    """Download agent source as tarball."""
    import tarfile
    import io
    from fastapi.responses import Response

    agent = await agent_service.get_agent_by_token(db, token)
    if not agent:
        raise HTTPException(status_code=404, detail="Invalid or expired token")

    # Bundle agent directory
    agent_dir = os.path.join(os.path.dirname(__file__), "..", "..", "agent")
    if not os.path.isdir(agent_dir):
        raise HTTPException(status_code=500, detail="Agent source not found")

    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        src_dir = os.path.join(agent_dir, "src")
        if os.path.isdir(src_dir):
            for f in os.listdir(src_dir):
                if f.endswith(".py"):
                    path = os.path.join(src_dir, f)
                    tf.add(path, arcname=f"src/{f}")

    buf.seek(0)
    return Response(
        content=buf.getvalue(),
        media_type="application/gzip",
        headers={"Content-Disposition": "attachment; filename=miner-agent.tar.gz"},
    )


@router.get("/agents/install", response_class=PlainTextResponse)
async def get_install_script(
    token: str = Query(..., description="Agent token"),
    db: AsyncSession = Depends(get_db),
):
    """Return bash script to install agent on Raspberry Pi."""
    agent = await agent_service.get_agent_by_token(db, token)
    if not agent:
        raise HTTPException(status_code=404, detail="Invalid or expired token")

    server_url = _get_server_url()
    influx_url = os.getenv("INFLUXDB_URL", "http://localhost:8086").rstrip("/")
    influx_token = os.getenv("INFLUXDB_TOKEN", "minertoken1234567890")
    influx_org = os.getenv("INFLUXDB_ORG", "miner-org")
    influx_bucket = os.getenv("INFLUXDB_BUCKET", "miner-metrics")

    script = f"""#!/bin/bash
set -e
echo "Installing Miner Agent..."

# Check requirements
MISSING=""
command -v python3 >/dev/null 2>&1 || MISSING="$MISSING python3"
python3 -m venv --help >/dev/null 2>&1 || MISSING="$MISSING python3-venv"
command -v curl >/dev/null 2>&1 || MISSING="$MISSING curl"
command -v tar >/dev/null 2>&1 || MISSING="$MISSING tar"
command -v sudo >/dev/null 2>&1 || MISSING="$MISSING sudo"
command -v systemctl >/dev/null 2>&1 || MISSING="$MISSING systemd"

if [ -n "$MISSING" ]; then
  echo "Missing requirements:$MISSING"
  echo "On Debian/Raspberry Pi OS, run: sudo apt update && sudo apt install -y python3 python3-venv curl tar"
  exit 1
fi

# Create install dir
INSTALL_DIR="${{INSTALL_DIR:-$HOME/miner-agent}}"
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Create venv and install deps
python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install whatsminer influxdb-client websockets aiohttp

# Create config
mkdir -p src
cat > src/.env << 'ENVEOF'
AGENT_TOKEN={agent.token}
SERVER_URL={server_url}
INFLUXDB_URL={influx_url}
INFLUXDB_TOKEN={influx_token}
INFLUXDB_ORG={influx_org}
INFLUXDB_BUCKET={influx_bucket}
ENVEOF

# Download and extract agent source
curl -sSL "{server_url}/agents/download?token={agent.token}" -o /tmp/agent.tar.gz
tar -xzf /tmp/agent.tar.gz -C "$INSTALL_DIR" 2>/dev/null || true
rm -f /tmp/agent.tar.gz
# Fallback: create minimal runner if download failed
if [ ! -f "$INSTALL_DIR/src/main.py" ]; then
  mkdir -p "$INSTALL_DIR/src"
  echo 'import time
while True: time.sleep(60)' > "$INSTALL_DIR/src/main.py"
fi

# Create systemd service
sudo tee /etc/systemd/system/miner-agent.service << SVCEOF
[Unit]
Description=Miner Agent
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR/src
EnvironmentFile=$INSTALL_DIR/src/.env
ExecStart=$INSTALL_DIR/venv/bin/python main.py
Restart=always
RestartSec=10
Environment=PATH=$INSTALL_DIR/venv/bin:/usr/bin

[Install]
WantedBy=multi-user.target
SVCEOF

sudo systemctl daemon-reload
sudo systemctl enable miner-agent
sudo systemctl start miner-agent

echo "Agent installed. Run: systemctl status miner-agent"
"""
    return PlainTextResponse(script)


@router.get("/agents/uninstall", response_class=PlainTextResponse)
async def get_uninstall_script(
    token: str = Query(..., description="Agent token"),
    db: AsyncSession = Depends(get_db),
):
    """Return bash script to uninstall agent."""
    agent = await agent_service.get_agent_by_token(db, token)
    if not agent:
        raise HTTPException(status_code=404, detail="Invalid or expired token")

    script = f"""#!/bin/bash
set -e
echo "Uninstalling Miner Agent..."

sudo systemctl stop miner-agent 2>/dev/null || true
sudo systemctl disable miner-agent 2>/dev/null || true
sudo rm -f /etc/systemd/system/miner-agent.service
sudo systemctl daemon-reload

INSTALL_DIR="${{INSTALL_DIR:-$HOME/miner-agent}}"
rm -rf "$INSTALL_DIR"

echo "Agent uninstalled."
"""
    return PlainTextResponse(script)


# --- Agent self-info (for agent process) ---

@router.get("/agents/me")
async def get_agent_me(
    token: str = Query(..., alias="token", description="Agent token"),
    db: AsyncSession = Depends(get_db),
):
    """Get current agent's info (farm_id, farm_name) by token. Used by agent for InfluxDB tags."""
    agent = await agent_service.get_agent_by_token(db, token)
    if not agent:
        raise HTTPException(status_code=404, detail="Invalid token")
    return {
        "agent_id": agent.id,
        "farm_id": agent.farm_id,
        "farm_name": agent.farm.name if agent.farm else "",
    }


# --- Agent list / detail ---

@router.get("/agents")
async def list_agents(
    farm_id: int | None = Query(None, description="Filter by farm"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List agents."""
    agents = await agent_service.list_agents(db, farm_id)
    return [
        {
            "id": a.id,
            "farm_id": a.farm_id,
            "name": a.name,
            "last_seen": a.last_seen.isoformat() if a.last_seen else None,
            "miner_count": len(a.miners),
        }
        for a in agents
    ]


@router.get("/agents/{agent_id}")
async def get_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get agent detail with miners."""
    agent = await agent_service.get_agent_by_id(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return {
        "id": agent.id,
        "farm_id": agent.farm_id,
        "farm_name": agent.farm.name if agent.farm else None,
        "name": agent.name,
        "last_seen": agent.last_seen.isoformat() if agent.last_seen else None,
        "install_script": f"curl -sSL '{_get_server_url()}/agents/install?token={agent.token}' | bash",
        "uninstall_script": f"curl -sSL '{_get_server_url()}/agents/uninstall?token={agent.token}' | bash",
        "miners": [
            {
                "id": m.id,
                "mac": m.mac,
                "ip": m.ip,
                "model": m.model,
                "worker1": m.worker1,
                "worker2": m.worker2,
                "worker3": m.worker3,
            }
            for m in agent.miners
        ],
    }


# --- Commands and Scan ---

class CommandCreate(BaseModel):
    type: str  # restart, update_worker, power_off, power_on, get_realtime
    miner_id: int | None = None
    params: dict | None = None


@router.post("/agents/{agent_id}/commands")
async def queue_command(
    agent_id: int,
    command: CommandCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Queue a command for the agent (restart, update_worker, power_off, power_on, get_realtime)."""
    from app.models import Command, CommandStatus, CommandType

    agent = await agent_service.get_agent_by_id(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    cmd_type = command.type
    miner_id = command.miner_id
    params = command.params or {}

    if cmd_type not in [t.value for t in CommandType]:
        raise HTTPException(status_code=400, detail=f"Invalid command type: {cmd_type}")

    if cmd_type != CommandType.RESCAN.value and not miner_id:
        raise HTTPException(status_code=400, detail="miner_id required for this command")

    cmd = Command(
        agent_id=agent_id,
        miner_id=miner_id,
        type=cmd_type,
        params=params,
        status=CommandStatus.PENDING.value,
    )
    db.add(cmd)
    await db.flush()
    return {"status": "queued", "command_id": cmd.id}


@router.post("/agents/{agent_id}/scan")
async def trigger_scan(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Trigger scan for new miners. Agent must be online (WebSocket) to respond."""
    from app.models import Command, CommandStatus, CommandType

    agent = await agent_service.get_agent_by_id(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    cmd = Command(
        agent_id=agent_id,
        miner_id=None,
        type=CommandType.RESCAN.value,
        params={},
        status=CommandStatus.PENDING.value,
    )
    db.add(cmd)
    await db.flush()

    # Try to forward to WebSocket if agent is connected
    from app.websocket import send_command_to_agent
    result = await send_command_to_agent(agent_id, {"type": "rescan", "command_id": cmd.id})
    discovered = result.get("discovered", []) if result else None
    if discovered is not None:
        return {"status": "completed", "discovered": discovered or []}

    return {
        "status": "queued",
        "command_id": cmd.id,
        "message": "Agent offline - scan will run when agent connects",
    }


class RegisterMinerRequest(BaseModel):
    mac: str
    ip: str | None = None
    model: str | None = None


@router.post("/agents/{agent_id}/miners/register", status_code=201)
async def register_discovered_miners(
    agent_id: int,
    miners: list[RegisterMinerRequest],
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Register discovered miners to the agent (add to farm)."""
    from app.services import miner_service

    agent = await agent_service.get_agent_by_id(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    result = []
    for m in miners:
        miner = await miner_service.upsert_miner(
            db, agent_id,
            mac=m.mac,
            ip=m.ip,
            model=m.model,
        )
        result.append({
            "id": miner.id,
            "mac": miner.mac,
            "ip": miner.ip,
            "model": miner.model,
        })
    return {"registered": result}
