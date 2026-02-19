"""WebSocket endpoint for agents."""
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.database import async_session_maker
from app.services import agent_service
from app.models import Command, CommandStatus
from app.websocket import (
    register_agent,
    unregister_agent,
    complete_pending_response,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/agents/ws")
async def agent_websocket(websocket: WebSocket):
    """Handle agent WebSocket connection. Token via query: ?token=xxx"""
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return

    async with async_session_maker() as db:
        agent = await agent_service.get_agent_by_token(db, token)
        if not agent:
            await websocket.close(code=4001, reason="Invalid token")
            return
        agent_id = agent.id
        await agent_service.update_agent_last_seen(db, agent)
        await db.commit()

    register_agent(agent_id, websocket)

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)

            if msg.get("type") == "ping":
                async with async_session_maker() as db:
                    await agent_service.update_agent_last_seen(db, agent_id)
                    await db.commit()
                await websocket.send_json({"type": "pong"})
                continue

            if msg.get("type") == "scan_result":
                command_id = msg.get("command_id")
                discovered = msg.get("discovered", [])
                async with async_session_maker() as db:
                    from sqlalchemy import select
                    result = await db.execute(select(Command).where(Command.id == command_id))
                    cmd = result.scalar_one_or_none()
                    if cmd:
                        cmd.status = CommandStatus.COMPLETED.value
                        cmd.result = {"discovered": discovered}
                        await db.commit()
                complete_pending_response(agent_id, {"discovered": discovered})
                continue

            if msg.get("type") == "miner_upsert":
                async with async_session_maker() as db:
                    from app.services import miner_service
                    for m in msg.get("miners", []):
                        await miner_service.upsert_miner(
                            db, agent_id,
                            mac=m["mac"],
                            ip=m.get("ip"),
                            model=m.get("model"),
                        )
                    await db.commit()
                continue

            if msg.get("type") == "command_result":
                command_id = msg.get("command_id")
                result = msg.get("result")
                status = msg.get("status", "completed")
                async with async_session_maker() as db:
                    from sqlalchemy import select
                    res = await db.execute(select(Command).where(Command.id == command_id))
                    cmd = res.scalar_one_or_none()
                    if cmd:
                        cmd.status = status
                        cmd.result = result
                        await db.commit()
                continue

    except WebSocketDisconnect:
        pass
    except json.JSONDecodeError as e:
        logger.warning("Invalid JSON from agent %s: %s", agent_id, e)
    except Exception as e:
        logger.exception("Agent WS error: %s", e)
    finally:
        unregister_agent(agent_id)
