"""WebSocket handler for agent connections."""
import asyncio
import json
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)

# agent_id -> WebSocket
_agent_connections: dict[int, WebSocket] = {}
# agent_id -> asyncio.Future for pending scan/command response
_pending_responses: dict[int, asyncio.Future] = {}


def register_agent(agent_id: int, ws: WebSocket) -> None:
    """Register agent WebSocket connection."""
    _agent_connections[agent_id] = ws
    logger.info("Agent %s connected", agent_id)


def unregister_agent(agent_id: int) -> None:
    """Unregister agent WebSocket."""
    _agent_connections.pop(agent_id, None)
    future = _pending_responses.pop(agent_id, None)
    if future and not future.done():
        future.cancel()
    logger.info("Agent %s disconnected", agent_id)


def is_agent_online(agent_id: int) -> bool:
    """Check if agent has active WebSocket."""
    return agent_id in _agent_connections


async def send_command_to_agent(agent_id: int, payload: dict[str, Any]) -> Any | None:
    """
    Send command to agent via WebSocket. Returns response payload or None if offline.
    Used for rescan - waits for agent to scan and return discovered miners.
    """
    ws = _agent_connections.get(agent_id)
    if not ws:
        return None

    future: asyncio.Future = asyncio.get_running_loop().create_future()
    _pending_responses[agent_id] = future

    try:
        await ws.send_json(payload)
        result = await asyncio.wait_for(future, timeout=120.0)
        return result
    except asyncio.TimeoutError:
        logger.warning("Agent %s scan timeout", agent_id)
        return None
    except asyncio.CancelledError:
        return None
    except Exception as e:
        logger.exception("Error sending to agent %s: %s", agent_id, e)
        return None
    finally:
        _pending_responses.pop(agent_id, None)


def complete_pending_response(agent_id: int, result: Any) -> None:
    """Complete a pending command response from agent."""
    future = _pending_responses.get(agent_id)
    if future and not future.done():
        future.set_result(result)


async def broadcast_to_agent(agent_id: int, payload: dict[str, Any]) -> bool:
    """Send message to agent without waiting for response."""
    ws = _agent_connections.get(agent_id)
    if not ws:
        return False
    try:
        await ws.send_json(payload)
        return True
    except Exception as e:
        logger.exception("Error broadcasting to agent %s: %s", agent_id, e)
        return False
