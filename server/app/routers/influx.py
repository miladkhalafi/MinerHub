"""Optional InfluxDB metrics query endpoint for charts."""
import os
from fastapi import APIRouter, Depends, Query

from app.auth import get_current_user
from app.models import User

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("")
async def query_metrics(
    user: User = Depends(get_current_user),
    farm_id: str | None = Query(None),
    miner_mac: str | None = Query(None),
    limit: int = Query(100, le=1000),
):
    """Query InfluxDB for miner metrics. Use with Grafana or custom charts."""
    url = os.getenv("INFLUXDB_URL", "http://localhost:8086")
    token = os.getenv("INFLUXDB_TOKEN", "")
    org = os.getenv("INFLUXDB_ORG", "miner-org")
    bucket = os.getenv("INFLUXDB_BUCKET", "miner-metrics")

    if not token:
        return {"error": "InfluxDB not configured", "points": []}

    try:
        from influxdb_client import InfluxDBClient
        from datetime import datetime, timedelta, timezone

        query = f'from(bucket: "{bucket}") |> range(start: -1h)'
        if farm_id:
            query += f' |> filter(fn: (r) => r["farm_id"] == "{farm_id}")'
        if miner_mac:
            query += f' |> filter(fn: (r) => r["miner_mac"] == "{miner_mac}")'
        query += f" |> limit(n: {limit})"

        with InfluxDBClient(url=url, token=token, org=org) as client:
            tables = client.query_api().query(query, org=org)
            points = []
            for table in tables:
                for record in table.records:
                    points.append({
                        "time": record.get_time().isoformat() if record.get_time() else None,
                        "measurement": record.get_measurement(),
                        "field": record.get_field(),
                        "value": record.get_value(),
                        **record.values,
                    })
            return {"points": points[:limit]}
    except Exception as e:
        return {"error": str(e), "points": []}
