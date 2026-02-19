#!/usr/bin/env python3
"""
Miner Agent - runs on Raspberry Pi, scans LAN for WhatsMiners, sends metrics to InfluxDB.
"""
import asyncio
import json
import logging
import sys
from datetime import datetime, timezone

from config import get_config
from scanner import scan_for_miners
from miner_client import get_summary, extract_miner_info, exec_command
from influx_writer import write_metrics, build_point
from server_client import run_websocket

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# Global state: known miners {mac: {ip, model, ...}}
_miners_cache: dict = {}
_agent_info: dict = {}  # farm_id, farm_name, agent_id from server


async def collect_metrics_and_send(config: dict):
    """Scan miners, get summary, write to InfluxDB."""
    port = config["WHATSMINER_PORT"]
    scan_range = config["SCAN_RANGE"] or None

    ips = await scan_for_miners(scan_range, port)
    points = []
    miners_to_report = []

    for ip in ips:
        summary = get_summary(ip, port)
        if not summary:
            continue

        info = extract_miner_info(summary)
        if not info or not info.get("mac"):
            continue

        mac = info["mac"]
        _miners_cache[mac] = {"ip": ip, "model": info.get("model"), **info}
        miners_to_report.append({"mac": mac, "ip": ip, "model": info.get("model")})

        if not _agent_info:
            continue  # Not yet registered with server

        pt = build_point(
            miner_mac=mac,
            miner_ip=ip,
            miner_model=info.get("model"),
            worker=info.get("worker"),
            farm_id=_agent_info.get("farm_id", ""),
            farm_name=_agent_info.get("farm_name", ""),
            agent_id=_agent_info.get("agent_id", ""),
            hashrate=info.get("hashrate"),
            temperature=info.get("temperature"),
            elapsed=info.get("elapsed"),
            accepted=info.get("accepted"),
            rejected=info.get("rejected"),
        )
        pt["timestamp"] = datetime.now(timezone.utc)
        points.append(pt)

    if points and config.get("INFLUXDB_TOKEN"):
        ok = write_metrics(
            config["INFLUXDB_URL"],
            config["INFLUXDB_TOKEN"],
            config["INFLUXDB_ORG"],
            config["INFLUXDB_BUCKET"],
            points,
        )
        logger.info("Wrote %d points to InfluxDB: %s", len(points), "ok" if ok else "failed")

    return miners_to_report


async def handle_command(cmd: dict) -> dict | None:
    """Handle command from server. Returns response to send."""
    cmd_type = cmd.get("type")
    command_id = cmd.get("command_id")

    if cmd_type == "rescan":
        config = get_config()
        miners = await collect_metrics_and_send(config)
        return {"type": "scan_result", "command_id": command_id, "discovered": miners}

    if cmd_type in ("restart", "power_off", "power_on"):
        miner_mac = cmd.get("miner_mac")
        password = cmd.get("password")
        if not miner_mac:
            return {"type": "command_result", "command_id": command_id, "status": "failed", "result": {"error": "no mac"}}

        miner = _miners_cache.get(miner_mac)
        if not miner:
            return {"type": "command_result", "command_id": command_id, "status": "failed", "result": {"error": "miner not in cache"}}

        ip = miner.get("ip")
        if not ip:
            return {"type": "command_result", "command_id": command_id, "status": "failed", "result": {"error": "no ip"}}

        api_cmd = "restart_btminer" if cmd_type == "restart" else cmd_type
        # Password may be empty for some miners
        result = exec_command(ip, password or "admin", api_cmd) if password or cmd_type == "restart" else None
        if result is None and (password or cmd_type == "restart"):
            return {"type": "command_result", "command_id": command_id, "status": "failed", "result": {"error": "exec failed"}}
        return {"type": "command_result", "command_id": command_id, "status": "completed", "result": result or {}}

    if cmd_type == "update_worker":
        miner_mac = cmd.get("miner_mac")
        password = cmd.get("password")
        worker1 = cmd.get("worker1", "")
        worker2 = cmd.get("worker2", "")
        worker3 = cmd.get("worker3", "")
        miner = _miners_cache.get(miner_mac)
        if not miner:
            return {"type": "command_result", "command_id": command_id, "status": "failed", "result": {"error": "miner not in cache"}}
        from miner_client import update_pools

        result = update_pools(miner["ip"], password or "admin", worker1, worker2, worker3)
        return {"type": "command_result", "command_id": command_id, "status": "completed", "result": result or {}}

    if cmd_type == "get_realtime":
        miner_mac = cmd.get("miner_mac")
        miner = _miners_cache.get(miner_mac)
        if not miner:
            return {"type": "command_result", "command_id": command_id, "status": "failed", "result": {"error": "miner not in cache"}}
        ip = miner.get("ip")
        summary = get_summary(ip) if ip else None
        info = extract_miner_info(summary) if summary else None
        return {"type": "command_result", "command_id": command_id, "status": "completed", "result": info or {}}

    return None


async def metrics_loop(config: dict):
    """Every 2 minutes: collect and send metrics."""
    while True:
        try:
            await collect_metrics_and_send(config)
        except Exception as e:
            logger.exception("Metrics loop error: %s", e)
        await asyncio.sleep(120)


async def fetch_agent_info(config: dict):
    """Fetch agent's farm_id, farm_name from server (needed for InfluxDB tags)."""
    try:
        import aiohttp
        url = f"{config['SERVER_URL']}/agents/me?token={config['AGENT_TOKEN']}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    _agent_info.update({
                        "farm_id": str(data.get("farm_id", "")),
                        "farm_name": data.get("farm_name", "default"),
                        "agent_id": str(data.get("agent_id", "")),
                    })
                    logger.info("Agent info: farm=%s", _agent_info.get("farm_name"))
    except Exception as e:
        logger.warning("Could not fetch agent info: %s", e)


async def main():
    config = get_config()
    if not config["AGENT_TOKEN"]:
        logger.error("AGENT_TOKEN not set")
        sys.exit(1)

    # Fetch agent info for InfluxDB tags
    await fetch_agent_info(config)

    # Start metrics loop in background
    asyncio.create_task(metrics_loop(config))

    # WebSocket to server
    async def on_cmd(cmd):
        return await handle_command(cmd)

    await run_websocket(
        config["SERVER_URL"],
        config["AGENT_TOKEN"],
        on_command=on_cmd,
    )


if __name__ == "__main__":
    asyncio.run(main())
