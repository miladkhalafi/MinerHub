"""Write miner metrics to InfluxDB."""
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


def write_metrics(
    url: str,
    token: str,
    org: str,
    bucket: str,
    points: list[dict],
) -> bool:
    """
    Write metrics to InfluxDB.
    Each point: {measurement, tags: {farm_id, farm_name, agent_id, miner_mac, ...}, fields: {hashrate, temp, ...}, timestamp}
    """
    if not points:
        return True

    try:
        from influxdb_client import InfluxDBClient, Point
        from influxdb_client.client.write_api import SYNCHRONOUS

        with InfluxDBClient(url=url, token=token, org=org) as client:
            write_api = client.write_api(write_options=SYNCHRONOUS)
            influx_points = []
            for p in points:
                pt = Point(p.get("measurement", "miner_metrics"))
                for k, v in (p.get("tags") or {}).items():
                    if v is not None:
                        pt = pt.tag(k, str(v))
                for k, v in (p.get("fields") or {}).items():
                    if v is not None:
                        pt = pt.field(k, float(v) if isinstance(v, (int, float)) else v)
                ts = p.get("timestamp") or datetime.now(timezone.utc)
                pt = pt.time(ts)
                influx_points.append(pt)
            write_api.write(bucket=bucket, org=org, record=influx_points)
        return True
    except Exception as e:
        logger.exception("InfluxDB write failed: %s", e)
        return False


def build_point(
    miner_mac: str,
    miner_ip: str | None,
    miner_model: str | None,
    worker: str | None,
    farm_id: str | int,
    farm_name: str,
    agent_id: str | int,
    hashrate: float | None,
    temperature: float | None,
    elapsed: int | None,
    accepted: int | None,
    rejected: int | None,
    **kwargs,
) -> dict:
    """Build a single InfluxDB point for miner metrics."""
    return {
        "measurement": "miner_metrics",
        "tags": {
            "farm_id": str(farm_id),
            "farm_name": farm_name,
            "agent_id": str(agent_id),
            "miner_mac": miner_mac,
            "miner_ip": miner_ip or "",
            "miner_model": miner_model or "",
            "worker": worker or "",
        },
        "fields": {
            "hashrate": hashrate,
            "temperature": temperature,
            "elapsed": elapsed,
            "accepted": accepted,
            "rejected": rejected,
            **{k: v for k, v in kwargs.items() if v is not None},
        },
    }
