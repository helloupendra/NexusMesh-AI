# Clean Commit Sequence (Suggested)

Use this sequence to keep history reviewable and profile-friendly on GitHub.

## Commit 1: Orchestrator architecture

```bash
git add orchestrator/main.py orchestrator/requirements.txt orchestrator/README.md orchestrator/nexus_orchestrator/
git commit -m "feat(orchestrator): add LangGraph RabbitMQ dispatcher with clean architecture"
```

## Commit 2: C# worker + task routing

```bash
git add workers/csharp_worker/Program.cs workers/csharp_worker/Worker.cs workers/csharp_worker/NexusMesh.Worker.csproj workers/csharp_worker/Dockerfile workers/csharp_worker/appsettings.json workers/csharp_worker/RabbitMq/ workers/csharp_worker/Processing/
git commit -m "feat(worker): add .NET 9 task router with backtest, signal, and risk handlers"
```

## Commit 3: Infrastructure and env defaults

```bash
git add infrastructure/docker/docker-compose.yml .env.example
git commit -m "chore(infra): add docker compose stack and cross-arch platform settings"
```

## Commit 4: Tests and CI

```bash
git add tests/ .github/workflows/ci.yml
git commit -m "test(ci): add orchestrator routing tests and GitHub Actions pipeline"
```

## Commit 5: OSS docs and contribution workflow

```bash
git add README.md CONTRIBUTING.md docs/prompts/ docs/open-source/ .gitignore .github/pull_request_template.md
git commit -m "docs: improve onboarding, prompts, and contribution workflow"
```

## Push Strategy

```bash
git push origin <branch-name>
```

If you are preparing a release-style PR, keep this sequence and avoid squashing.
