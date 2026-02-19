"""WhatsMiner API client - read-only (summary) and optional write (with password)."""
import logging
from typing import Any

logger = logging.getLogger(__name__)


def get_summary(ip: str, port: int = 4028) -> dict | None:
    """
    Get WhatsMiner summary (read-only, no password).
    Returns dict with MAC, IP, Model, hashrate, temperature, etc. or None on error.
    """
    try:
        from whatsminer import WhatsminerAccessToken, WhatsminerAPI

        token = WhatsminerAccessToken(ip_address=ip, port=port)
        result = WhatsminerAPI.get_read_only_info(token, "summary")
        return result
    except Exception as e:
        logger.warning("WhatsMiner summary %s:%s failed: %s", ip, port, e)
        return None


def extract_miner_info(summary: dict) -> dict | None:
    """
    Extract mac, ip, model from WhatsMiner summary response.
    Summary structure: {"SUMMARY": [{"MAC": "xx:xx:...", "IP": "...", "Model": "M30S+"}]}
    """
    try:
        s = summary.get("SUMMARY")
        if not s or not isinstance(s, list):
            return None
        row = s[0] if s else {}
        mac = row.get("MAC") or row.get("mac")
        ip = row.get("IP") or row.get("ip")
        model = row.get("Model") or row.get("model") or ""
        if not mac:
            return None
        return {
            "mac": str(mac),
            "ip": str(ip) if ip else None,
            "model": str(model) if model else None,
            "hashrate": row.get("GHS 5s"),
            "temperature": row.get("Temperature"),
            "elapsed": row.get("Elapsed"),
            "accepted": row.get("Accepted"),
            "rejected": row.get("Rejected"),
        }
    except Exception as e:
        logger.warning("Extract miner info failed: %s", e)
        return None


def exec_command(ip: str, password: str, cmd: str, params: dict | None = None, port: int = 4028) -> dict | None:
    """
    Execute writable command (restart_btminer, power_off, power_on, update_pools).
    Requires admin password.
    """
    try:
        from whatsminer import WhatsminerAccessToken, WhatsminerAPI

        token = WhatsminerAccessToken(ip_address=ip, port=port, admin_password=password)
        additional = params or {}
        if cmd in ("power_off", "power_on", "restart_btminer"):
            additional["respbefore"] = "true"
        result = WhatsminerAPI.exec_command(token, cmd, additional_params=additional)
        return result
    except Exception as e:
        logger.warning("WhatsMiner exec %s on %s failed: %s", cmd, ip, e)
        return None


def update_pools(ip: str, password: str, worker1: str = "", worker2: str = "", worker3: str = "", port: int = 4028) -> dict | None:
    """Update pool workers. Pass empty string to leave pool unchanged."""
    params = {}
    if worker1:
        params["worker1"] = worker1
    if worker2:
        params["worker2"] = worker2
    if worker3:
        params["worker3"] = worker3
    return exec_command(ip, password, "update_pools", params, port) if params else {"status": "ok"}
