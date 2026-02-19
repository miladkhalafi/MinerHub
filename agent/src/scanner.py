"""LAN scanner for WhatsMiner devices on port 4028."""
import asyncio
import ipaddress
import socket
import logging
from typing import Iterable

logger = logging.getLogger(__name__)

DEFAULT_PORT = 4028
SCAN_TIMEOUT = 2.0
MAX_CONCURRENT = 50


def _get_default_scan_range() -> str:
    """Try to detect LAN range from default route. Fallback to common range."""
    try:
        import subprocess
        # On Linux/Raspberry Pi: ip route | grep default
        result = subprocess.run(
            ["ip", "route", "get", "8.8.8.8"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            parts = result.stdout.split()
            for i, p in enumerate(parts):
                if p == "src" and i + 1 < len(parts):
                    src_ip = parts[i + 1]
                    try:
                        ip = ipaddress.ip_address(src_ip)
                        if ip.version == 4:
                            # Use /24 for same subnet
                            net = ipaddress.ip_network(f"{src_ip}/24", strict=False)
                            return str(net)
                    except Exception:
                        pass
    except Exception as e:
        logger.debug("Could not detect scan range: %s", e)
    return "192.168.1.0/24"


def _parse_scan_range(spec: str) -> list[str]:
    """Parse CIDR or range spec to list of IP strings."""
    try:
        if "/" in spec:
            net = ipaddress.ip_network(spec.strip(), strict=False)
            return [str(ip) for ip in net.hosts()]
        if "-" in spec:
            # 192.168.1.1-192.168.1.50
            start_s, end_s = spec.split("-", 1)
            start_ip = ipaddress.ip_address(start_s.strip())
            end_ip = ipaddress.ip_address(end_s.strip())
            return [str(ipaddress.ip_address(i)) for i in range(int(start_ip), int(end_ip) + 1)]
    except Exception as e:
        logger.warning("Invalid scan range %s: %s", spec, e)
    return []


def _sync_connect(ip: str, port: int) -> str | None:
    """Synchronous port check. Returns IP if connect succeeds."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(SCAN_TIMEOUT)
        sock.connect((ip, port))
        sock.close()
        return ip
    except Exception:
        return None


async def _check_port(ip: str, port: int, semaphore: asyncio.Semaphore) -> str | None:
    """Try to connect to IP:port. Returns IP if successful."""
    async with semaphore:
        loop = asyncio.get_event_loop()
        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(None, _sync_connect, ip, port),
                timeout=SCAN_TIMEOUT + 1,
            )
            return result
        except asyncio.TimeoutError:
            return None
        except Exception as e:
            logger.debug("Scan %s:%s failed: %s", ip, port, e)
            return None


async def scan_for_miners(
    scan_range: str | None = None,
    port: int = DEFAULT_PORT,
) -> list[str]:
    """
    Scan LAN for devices with port open (WhatsMiner API port).
    Returns list of IP addresses.
    """
    spec = scan_range or _get_default_scan_range()
    ips = _parse_scan_range(spec)
    if not ips:
        return []

    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    tasks = [_check_port(ip, port, semaphore) for ip in ips]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    found = []
    for r in results:
        if isinstance(r, str):
            found.append(r)
        elif isinstance(r, Exception):
            logger.debug("Scan error: %s", r)
    return found
