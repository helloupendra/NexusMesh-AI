# Orchestrator Module (Python + LangGraph)

This module is the NexusMesh control-plane "brain".
It receives a user request, dispatches work to RabbitMQ (`task_queue`), waits for a worker response on `results_queue`, and returns a final orchestrator state.

## Directory Structure

```text
orchestrator/
├── README.md
├── main.py
├── requirements.txt
└── nexus_orchestrator/
    ├── __init__.py
    ├── config.py
    ├── application/
    │   ├── __init__.py
    │   ├── ports.py
    │   └── services.py
    ├── domain/
    │   ├── __init__.py
    │   └── models.py
    ├── infrastructure/
    │   ├── __init__.py
    │   └── rabbitmq_gateway.py
    └── presentation/
        ├── __init__.py
        └── graph.py
```

## Design Notes

- **Domain layer**: Pydantic models for orchestrator state and queue payloads.
- **Application layer**: orchestration use-cases (`dispatch`, `await_result`) plus messaging port abstraction.
- **Infrastructure layer**: RabbitMQ adapter using `pika`.
- **Presentation layer**: LangGraph wiring and executable graph.
- **Live API layer**: FastAPI + WebSocket status stream (`orchestrator/api_server.py`).

## Run Locally

1. Install dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r orchestrator/requirements.txt
   ```
2. Set environment variables (example values):
   ```bash
   export RABBITMQ_HOST=127.0.0.1
   export RABBITMQ_PORT=5672
   export RABBITMQ_USERNAME=guest
   export RABBITMQ_PASSWORD=guest
   export RABBITMQ_VHOST=/
   export TASK_QUEUE=task_queue
   export RESULTS_QUEUE=results_queue
   export RESULTS_TIMEOUT_SECONDS=120
   ```
3. Start the orchestrator:
   ```bash
   python orchestrator/main.py --task-type backtest --request "Run stock backtest for AAPL 5m"
   python orchestrator/main.py --task-type signal_generation --request "Generate intraday signal for NIFTY"
   python orchestrator/main.py --task-type risk_evaluation --request "Evaluate risk profile for NIFTY strategy"
   ```

## Example Output

```json
{
  "task_id": "52df71b38ca44f1ca89f4f4996f886d2",
  "status": "COMPLETED",
  "result": {
    "summary": "Backtest complete",
    "latency_ms": 2500
  },
  "user_request": "Run stock backtest for AAPL 5m",
  "task_type": "backtest",
  "error": null
}
```
