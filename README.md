# MinerHub

![MinerHub Logo](assets/logo.png)

Crypto miner monitoring system for WhatsMiner devices. Comprises:

- **Server** (Docker): FastAPI backend, PostgreSQL, InfluxDB, Web dashboard
- **Agent** (Raspberry Pi): Scans LAN for miners, sends metrics to InfluxDB, executes commands (restart, power off)

## Quick Start

### 1. Start the server stack

**Option A: Build locally**
```bash
git clone https://github.com/miladkhalafi/MinerHub.git
cd MinerHub
# With local InfluxDB (default):
docker-compose --profile local-influxdb up -d
# With external InfluxDB: create .env with INFLUXDB_URL, INFLUXDB_TOKEN, etc., then:
docker-compose up -d
```

**Option B: Use pre-built image from GitHub Container Registry**
```bash
# Pull the image
docker pull ghcr.io/miladkhalafi/minerhub:latest

# Or use docker-compose with the image
# Edit docker-compose.yml: change dashboard.build to dashboard.image: ghcr.io/miladkhalafi/minerhub:latest
```

Then:

- Dashboard: http://localhost:8000
- API: http://localhost:8000
- InfluxDB: http://localhost:8086

### 2. Create a farm and register an agent

1. Open the dashboard.
2. Create a farm (e.g. `My Farm`).
3. Open the farm and click **Add Agent**.
4. Copy the install script (curl command).

### 3. Install the agent on Raspberry Pi

On your Raspberry Pi (same network as the miners):

```bash
curl -sSL 'http://YOUR_SERVER_IP:8000/api/agents/install?token=YOUR_TOKEN' | bash
```

Replace `YOUR_SERVER_IP` with your server IP (or hostname) and use the token from step 2.

### 4. Scan for miners

With the agent running, open the farm in the dashboard and click **Scan for new miners**. Found miners can be registered and managed (restart, power off, edit worker/password).

## InfluxDB configuration

- **Local InfluxDB**: Run `docker-compose --profile local-influxdb up -d` to start the bundled InfluxDB.
- **External/cloud InfluxDB**: Create a `.env` file (copy from `.env.example`) and set `INFLUXDB_URL`, `INFLUXDB_TOKEN`, `INFLUXDB_ORG`, and `INFLUXDB_BUCKET`. Then run `docker-compose up -d` (no profile). Agents installed via the install script will use the same InfluxDB config from the server.

## Architecture

- **Farm**: Named group for one agent and its miners
- **Agent**: One per farm; runs on a Raspberry Pi; discovers WhatsMiner devices and reports metrics
- **Miners**: Identified by MAC address; IP may change (DHCP)

## Development

### Server (API + dashboard)

```bash
cd server
pip install -r requirements.txt
# Start PostgreSQL + InfluxDB via docker-compose
docker-compose --profile local-influxdb up -d postgres influxdb
# Run API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev  # http://localhost:3000, proxies API to :8000
```

### Agent (standalone)

```bash
cd agent
pip install -r requirements.txt
# Set env vars
export AGENT_TOKEN=your_token
export SERVER_URL=http://your-server:8000/api
export INFLUXDB_URL=http://your-server:8086
export INFLUXDB_TOKEN=minertoken1234567890
export INFLUXDB_ORG=miner-org
export INFLUXDB_BUCKET=miner-metrics
python src/main.py
```

## API overview

All API endpoints are under `/api`:

- `GET/POST /api/farms` – List/create farms
- `GET/POST /api/farms/{id}/agents` – Get agents, register agent
- `GET /api/agents/install?token=` – Install script
- `GET /api/agents/uninstall?token=` – Uninstall script
- `POST /api/agents/{id}/scan` – Trigger scan for new miners
- `GET/PATCH /api/miners` – List/update miners
- `POST /api/miners/{id}/restart` – Restart miner
- `POST /api/miners/{id}/power_off` – Power off miner

## Security notes

- Set `SECRET_KEY` for password encryption
- Use HTTPS (reverse proxy) in production
- Change default InfluxDB and PostgreSQL credentials
