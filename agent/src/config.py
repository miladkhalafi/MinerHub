"""Agent configuration from environment."""
import os


def get_config():
    """Load config from environment."""
    return {
        "AGENT_TOKEN": os.getenv("AGENT_TOKEN", ""),
        "SERVER_URL": os.getenv("SERVER_URL", "http://localhost:8000").rstrip("/"),
        "INFLUXDB_URL": os.getenv("INFLUXDB_URL", "http://localhost:8086").rstrip("/"),
        "INFLUXDB_TOKEN": os.getenv("INFLUXDB_TOKEN", ""),
        "INFLUXDB_ORG": os.getenv("INFLUXDB_ORG", "miner-org"),
        "INFLUXDB_BUCKET": os.getenv("INFLUXDB_BUCKET", "miner-metrics"),
        "SCAN_RANGE": os.getenv("SCAN_RANGE", ""),  # e.g. 192.168.1.0/24
        "WHATSMINER_PORT": int(os.getenv("WHATSMINER_PORT", "4028")),
    }
