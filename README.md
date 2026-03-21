# NexusMesh-AI

Distributed multi-agent architecture with:
- A Python + LangGraph orchestrator (control plane).
- A C#/.NET 9 background worker (execution plane).
- RabbitMQ for resilient task/result messaging.
- A reusable PhD-level analyst system prompt for algorithmic trading hypotheses.

## Repository Layout

```text
NexusMesh-AI/
├── README.md
├── CONTRIBUTING.md
├── .env.example
├── docs/
│   └── prompts/
│       └── algorithmic_trading_analyst_system_prompt.md
├── infrastructure/
│   └── docker/
│       └── docker-compose.yml
├── orchestrator/
│   ├── README.md
│   ├── main.py
│   ├── requirements.txt
│   └── nexus_orchestrator/
└── workers/
    └── csharp_worker/
        ├── README.md
        ├── Dockerfile
        ├── NexusMesh.Worker.csproj
        ├── Program.cs
        ├── Worker.cs
        └── RabbitMq/
```

## Module 1: Orchestrator (Python + LangGraph)

See [orchestrator/README.md](orchestrator/README.md).

Capabilities implemented:
- Pydantic state schema tracking `task_id`, `status`, and `result`.
- LangGraph flow: `Dispatcher -> AwaitResult`.
- RabbitMQ publish to `task_queue` using `pika`.
- Blocking wait on `results_queue` before graph completion.
- Worker routing via `task_type` (`backtest`, `signal_generation`, `risk_evaluation`).
- Clean architecture boundaries across domain/application/infrastructure/presentation.

## Module 2: Learning C# Worker (.NET 9)

See [workers/csharp_worker/README.md](workers/csharp_worker/README.md).

Capabilities implemented:
- `BackgroundService` consuming from `task_queue` using `RabbitMQ.Client`.
- Simulated heavy computation via `Task.Delay`.
- Handler-based routing by `task_type` for multi-agent expansion.
- Publishes JSON results to `results_queue`.
- Learning-focused comments on:
  - Dependency Injection in `Program.cs`.
  - `Task` vs `void` for async consumers.
  - Safe RabbitMQ connection lifecycle through singleton management.

## Module 3: PhD-Level Analyst Prompt

See [docs/prompts/algorithmic_trading_analyst_system_prompt.md](docs/prompts/algorithmic_trading_analyst_system_prompt.md).

It enforces strict JSON output with:
- Risk/Reward ratio.
- Alpha decay factors.
- Technical indicator requirements (including RSI/Bollinger options).
- A schema that is directly consumable by C# workers.

## Docker + Hardware Guidance

Compose file: [infrastructure/docker/docker-compose.yml](infrastructure/docker/docker-compose.yml)

Platform defaults:
- `RABBITMQ_PLATFORM=linux/arm64` for Apple Silicon (M1/M2) local dev.
- `WORKER_PLATFORM=linux/amd64` for typical x86_64 Linux server workers.

Adjust these in `.env` if your server architecture differs.

## Quick Start

1. Copy environment template:
   ```bash
   cp .env.example .env
   ```
2. Start RabbitMQ + C# worker:
   ```bash
   cd infrastructure/docker
   docker compose --env-file ../../.env up --build -d
   ```
3. Run the orchestrator from repo root:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r orchestrator/requirements.txt
   python orchestrator/main.py --task-type backtest --request "Run stock backtest for AAPL"
   python orchestrator/main.py --task-type signal_generation --request "Generate intraday signal for NIFTY"
   python orchestrator/main.py --task-type risk_evaluation --request "Evaluate risk profile for NIFTY mean-reversion strategy"
   ```

## One-Command Dev Run

Run frontend + backend together:

```bash
./run_dev.sh
```

What it starts:
- Backend: Docker Compose stack (`rabbitmq` + `csharp_worker`)
- Live API/WebSocket: FastAPI on `http://localhost:8000`
- Frontend: Vite dev server (`frontend`, default port `5173`)

Optional environment flags:
- `FRONTEND_PORT=5174 ./run_dev.sh`
- `API_PORT=8001 ./run_dev.sh`
- `KEEP_BACKEND_RUNNING=1 ./run_dev.sh`

## Dynamic Testing (Live API + WebSocket)

1. Start full stack:
   ```bash
   ./run_dev.sh
   ```
2. Open dashboard: `http://localhost:5173`
3. Dispatch tasks from the Status Panel form in UI.
4. Verify live updates:
   - RabbitMQ status toggles online/offline based on backend connectivity.
   - Active task count increases on dispatch.
   - Active tasks move out after worker completion (result event received).
5. Optional API checks:
   ```bash
   curl http://localhost:8000/api/status
   curl -X POST http://localhost:8000/api/tasks \
     -H "Content-Type: application/json" \
     -d '{"request":"smoke backtest","task_type":"backtest"}'
   ```

## Open Source Workflow

- Contribution guide: [CONTRIBUTING.md](CONTRIBUTING.md)
- CI pipeline: [.github/workflows/ci.yml](.github/workflows/ci.yml)
- Commit strategy: [docs/open-source/commit_sequence.md](docs/open-source/commit_sequence.md)
- Keep PRs small and include test output in descriptions.
