# NexusMesh-AI

NexusMesh-AI is a distributed multi-agent project with a Python orchestrator, a .NET worker, RabbitMQ messaging, and a live React dashboard.

It is designed as an open-source portfolio project you can run locally on macOS (including M1/M2) and deploy worker services to Linux servers.

## What This Project Outputs

When you run the stack, you get:

- A live frontend Command Center at `http://localhost:5173`
- A live API at `http://localhost:8000`
- A WebSocket status stream at `ws://localhost:8000/ws/status`
- A worker pipeline where tasks are queued, processed, and reflected in the UI in real time

Example API snapshot:

```json
{
  "timestamp": "2026-03-22T09:34:53.766204+00:00",
  "rabbitmq_connection": {
    "online": true,
    "endpoint": "amqp://127.0.0.1:5672"
  },
  "active_tasks": [],
  "recent_tasks": [],
  "metrics": {
    "active_count": 0,
    "recent_count": 0
  },
  "node_status": {
    "orchestrator": "online",
    "csharp_worker": "online",
    "python_inference": "idle"
  }
}
```

## Architecture

```text
Frontend (React + Vite + React Flow)
            |
            | HTTP + WebSocket
            v
FastAPI Live API (Python)
            |
            | pika
            v
RabbitMQ (task_queue / results_queue / status_events_queue)
            |
            v
C# Worker (.NET 9 BackgroundService)
```

Core flow:

1. Frontend dispatches a task (`/api/tasks`)
2. Orchestrator publishes to `task_queue`
3. C# worker consumes and processes by `task_type`
4. Worker publishes to `results_queue` and `status_events_queue`
5. Live API updates snapshot
6. Frontend receives updates over `/ws/status`

## Tech Stack

- Python: FastAPI, LangGraph, Pydantic, pika
- C#: .NET 9 Worker Service, RabbitMQ.Client
- Messaging: RabbitMQ (management image)
- Frontend: React (Vite), Tailwind, Lucide, React Flow
- Infra: Docker Compose

## Repository Layout

```text
NexusMesh-AI/
├── README.md
├── CONTRIBUTING.md
├── .env.example
├── run_dev.sh
├── docs/
│   └── prompts/
│       └── algorithmic_trading_analyst_system_prompt.md
├── infrastructure/
│   └── docker/
│       └── docker-compose.yml
├── orchestrator/
│   ├── README.md
│   ├── api_server.py
│   ├── main.py
│   ├── requirements.txt
│   └── nexus_orchestrator/
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   └── components/AgentGraph.jsx
│   └── package.json
├── workers/
│   └── csharp_worker/
│       ├── README.md
│       ├── Program.cs
│       ├── Worker.cs
│       └── RabbitMq/
└── tests/
```

## Prerequisites

- Docker Desktop (running)
- Node.js + npm
- Python 3.11+

Quick checks:

```bash
docker info
node -v
npm -v
python3 --version
```

## Quick Start (Recommended)

1. Clone and enter repo

```bash
git clone https://github.com/helloupendra/NexusMesh-AI.git
cd NexusMesh-AI
```

2. Create environment file

```bash
cp .env.example .env
```

3. Start full stack

```bash
./run_dev.sh
```

4. Open dashboard

- Frontend: `http://localhost:5173`
- API docs: `http://localhost:8000/docs`

## `run_dev.sh` Behavior

This script starts all required dev services:

- Docker backend: `rabbitmq` + `csharp_worker`
- FastAPI API server
- Vite frontend

Useful flags:

```bash
FRONTEND_PORT=5174 ./run_dev.sh
API_PORT=8001 ./run_dev.sh
KEEP_BACKEND_RUNNING=1 ./run_dev.sh
API_RELOAD=1 ./run_dev.sh
AUTO_KILL_PORTS=0 ./run_dev.sh
DOCKER_BUILD=1 ./run_dev.sh
```

Notes:

- Default startup uses `docker compose up -d --no-build` for faster runs.
- If image is missing, script auto-falls back to `--build` once.

## How to Test the Project

### 1) Check service health

```bash
curl http://127.0.0.1:8000/api/status
```

### 2) Dispatch a task

```bash
curl -X POST http://127.0.0.1:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"request":"Run stock backtest for AAPL","task_type":"backtest"}'
```

### 3) Watch WebSocket stream

```bash
npx wscat -c ws://127.0.0.1:8000/ws/status
```

### 4) UI validation

In the dashboard right panel, verify:

- RabbitMQ connection is online
- Active tasks increases after dispatch
- Task cards update without layout break for long IDs

### 5) Run automated tests

```bash
./venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
```

### 6) Build frontend

```bash
cd frontend
npm run build
```

## How to See Running Logs

### Full backend logs

```bash
docker compose -f infrastructure/docker/docker-compose.yml logs -f rabbitmq csharp_worker
```

### Confirm ports are listening

```bash
lsof -nP -iTCP:8000 -sTCP:LISTEN
lsof -nP -iTCP:5173 -sTCP:LISTEN
```

### API quick ping

```bash
curl http://127.0.0.1:8000/api/status
```

### Docker container status

```bash
docker compose -f infrastructure/docker/docker-compose.yml ps
```

## Troubleshooting

### Frontend not opening

- Check if Vite is running on port 5173:
  - `lsof -nP -iTCP:5173 -sTCP:LISTEN`
- If not, rerun: `./run_dev.sh`
- If blocked by ports, script attempts to free them when `AUTO_KILL_PORTS=1`.

### Script seems stuck after "Starting backend services"

- This usually means Docker build/pull is still in progress.
- Use faster default path (already configured) and rebuild only when needed:
  - `DOCKER_BUILD=1 ./run_dev.sh` only when you changed worker image dependencies.

### Docker daemon not reachable

- Start Docker Desktop and wait until Engine is ready.
- Verify: `docker info`

### WebSocket reconnecting in UI

- Ensure API is up: `curl http://127.0.0.1:8000/api/status`
- Ensure `websockets` dependency is installed in venv (script auto-installs from requirements).

## Platform Notes (M1 Mac + Linux Server)

From `.env` and compose defaults:

- `RABBITMQ_PLATFORM=linux/arm64` for Apple Silicon local development
- `WORKER_PLATFORM=linux/amd64` for typical Linux x86_64 deployment

Adjust these values if your target architecture differs.

## Module Docs

- Orchestrator: [orchestrator/README.md](orchestrator/README.md)
- C# Worker: [workers/csharp_worker/README.md](workers/csharp_worker/README.md)
- Analyst prompt: [docs/prompts/algorithmic_trading_analyst_system_prompt.md](docs/prompts/algorithmic_trading_analyst_system_prompt.md)

## Open Source Workflow

- Contribution guide: [CONTRIBUTING.md](CONTRIBUTING.md)
- CI pipeline: [.github/workflows/ci.yml](.github/workflows/ci.yml)
- Suggested commit flow: [docs/open-source/commit_sequence.md](docs/open-source/commit_sequence.md)

## What Next (Recommended)

The current project is functional and demo-ready, but not final for production.

High-value next steps:

1. Persist task history in a database instead of in-memory snapshots.
2. Add auth + role-based access for the dashboard/API.
3. Add retry/dead-letter queue strategy in RabbitMQ.
4. Add structured logging + centralized observability (OpenTelemetry).
5. Add CI checks for frontend lint/test and backend integration test with RabbitMQ.
