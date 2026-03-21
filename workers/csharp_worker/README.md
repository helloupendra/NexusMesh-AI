# C# Worker Module (.NET 9)

This module is the NexusMesh "muscle" worker.
It consumes jobs from RabbitMQ (`task_queue`), simulates heavy computation, and publishes JSON results to `results_queue`.

## Directory Structure

```text
workers/csharp_worker/
├── README.md
├── Dockerfile
├── NexusMesh.Worker.csproj
├── Program.cs
├── Worker.cs
├── appsettings.json
├── Processing/
│   ├── BacktestTaskProcessor.cs
│   ├── ITaskProcessor.cs
│   ├── RiskEvaluationTaskProcessor.cs
│   └── SignalGenerationTaskProcessor.cs
└── RabbitMq/
    ├── IRabbitMqConnectionManager.cs
    ├── RabbitMqConnectionManager.cs
    ├── RabbitMqOptions.cs
    ├── TaskMessage.cs
    └── TaskResultMessage.cs
```

## Routing Modes

- `backtest`: simulates heavy backtest compute using `Task.Delay`.
- `signal_generation`: simulates fast signal hypothesis generation.
- `risk_evaluation`: simulates portfolio/strategy risk scoring.

Set `task_type` in the incoming JSON:

```json
{
  "task_id": "abc123",
  "task_type": "risk_evaluation",
  "request": "Evaluate risk profile for intraday mean-reversion strategy"
}
```

## Learning-Oriented Design

- `Program.cs` demonstrates .NET dependency injection and service lifetimes.
- `Worker.cs` uses `AsyncEventingBasicConsumer` so processing uses `Task` (not `void`) for reliable async error propagation.
- RabbitMQ connection is managed as a singleton service for safer, reusable lifecycle handling.

## Run with .NET CLI

```bash
cd workers/csharp_worker
dotnet restore
dotnet run
```

## Run with Docker

```bash
docker build -t nexusmesh-csharp-worker workers/csharp_worker
docker run --rm \
  -e RabbitMq__Host=host.docker.internal \
  -e RabbitMq__Username=guest \
  -e RabbitMq__Password=guest \
  nexusmesh-csharp-worker
```
