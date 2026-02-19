"""Server WebSocket client and REST fallback for agent."""
import asyncio
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


async def run_websocket(
    server_url: str,
    token: str,
    on_command: callable,
    on_connected: callable = None,
) -> None:
    """
    Connect to server WebSocket and process commands.
    on_command(cmd_dict) -> result dict to send back.
    """
    import websockets

    ws_url = server_url.replace("http://", "ws://").replace("https://", "wss://")
    url = f"{ws_url}/agents/ws?token={token}"

    while True:
        try:
            async with websockets.connect(url, ping_interval=20, ping_timeout=10) as ws:
                logger.info("Connected to server")
                if on_connected:
                    on_connected()

                async def send_pong():
                    await ws.send(json.dumps({"type": "pong"}))

                while True:
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=35)
                        data = json.loads(msg)

                        if data.get("type") == "ping":
                            await ws.send(json.dumps({"type": "pong"}))
                            continue

                        # Handle commands from server
                        cmd = data
                        res = on_command(cmd)
                        result = await res if asyncio.iscoroutine(res) else res
                        if result is not None:
                            await ws.send(json.dumps(result))
                    except asyncio.TimeoutError:
                        await ws.send(json.dumps({"type": "ping"}))

        except Exception as e:
            logger.warning("WebSocket disconnected: %s", e)
        await asyncio.sleep(5)


async def poll_commands(
    server_url: str,
    token: str,
    execute_command: callable,
) -> list[dict]:
    """
    Poll server for pending commands (fallback when WebSocket down).
    Returns list of executed command results.
    """
    import aiohttp

    url = f"{server_url}/agents/me/commands"
    # Note: server needs to implement GET /agents/me/commands with token auth
    # For now we'll use the WebSocket as primary
    return []
