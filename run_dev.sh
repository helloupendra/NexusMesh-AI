#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"
COMPOSE_FILE="$ROOT_DIR/infrastructure/docker/docker-compose.yml"
ENV_FILE="$ROOT_DIR/.env"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
API_PORT="${API_PORT:-8000}"
KEEP_BACKEND_RUNNING="${KEEP_BACKEND_RUNNING:-0}"
COMPOSE_IMPL=""
BACKEND_STARTED=0
VENV_DIR="$ROOT_DIR/venv"
VENV_PYTHON="$VENV_DIR/bin/python"

for cmd in npm docker python3; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "error: '$cmd' is required but not installed." >&2
    exit 1
  fi
done

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  COMPOSE_IMPL="docker-compose-plugin"
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_IMPL="docker-compose-binary"
else
  echo "error: neither 'docker compose' nor 'docker-compose' is available." >&2
  exit 1
fi

# On macOS, some Docker installs expose the socket in ~/.docker/run/docker.sock.
if [[ -z "${DOCKER_HOST:-}" && "$(uname -s)" == "Darwin" && -S "$HOME/.docker/run/docker.sock" ]]; then
  export DOCKER_HOST="unix://$HOME/.docker/run/docker.sock"
fi

if ! docker info >/dev/null 2>&1; then
  echo "error: Docker daemon is not reachable." >&2
  echo "hint: Start Docker Desktop and wait until Engine is running." >&2
  echo "hint: Verify with: docker info" >&2
  exit 1
fi

if [[ ! -f "$FRONTEND_DIR/package.json" ]]; then
  echo "error: frontend/package.json not found." >&2
  exit 1
fi

if [[ ! -f "$VENV_PYTHON" ]]; then
  echo "Creating Python virtual environment..."
  python3 -m venv "$VENV_DIR"
fi

if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "error: docker compose file not found at $COMPOSE_FILE" >&2
  exit 1
fi

if ! "$VENV_PYTHON" -c "import fastapi,uvicorn,pika,pydantic,langgraph" >/dev/null 2>&1; then
  echo "Installing backend dependencies..."
  "$VENV_PYTHON" -m pip install -r "$ROOT_DIR/orchestrator/requirements.txt"
fi

if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
  echo "Installing frontend dependencies..."
  (cd "$FRONTEND_DIR" && npm install)
fi

compose() {
  if [[ "$COMPOSE_IMPL" == "docker-compose-plugin" ]]; then
    if [[ -f "$ENV_FILE" ]]; then
      docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$@"
    else
      docker compose -f "$COMPOSE_FILE" "$@"
    fi
    return
  fi

  if [[ -f "$ENV_FILE" ]]; then
    docker-compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$@"
  else
    docker-compose -f "$COMPOSE_FILE" "$@"
  fi
}

cleanup() {
  local exit_code=$?

  if [[ -n "${API_PID:-}" ]]; then
    kill "$API_PID" >/dev/null 2>&1 || true
    wait "$API_PID" 2>/dev/null || true
  fi

  if [[ -n "${FRONTEND_PID:-}" ]]; then
    kill "$FRONTEND_PID" >/dev/null 2>&1 || true
    wait "$FRONTEND_PID" 2>/dev/null || true
  fi

  if [[ "$KEEP_BACKEND_RUNNING" != "1" && "$BACKEND_STARTED" == "1" ]]; then
    echo "Stopping backend services..."
    compose down >/dev/null 2>&1 || true
  fi

  exit "$exit_code"
}
trap cleanup EXIT INT TERM

echo "Starting backend services (RabbitMQ + C# worker)..."
compose up -d --build
BACKEND_STARTED=1

# Give services a moment before opening UI.
sleep 2

echo "Starting live API server on http://localhost:${API_PORT} ..."
(
  cd "$ROOT_DIR"
  "$VENV_PYTHON" -m uvicorn orchestrator.api_server:app --host 0.0.0.0 --port "$API_PORT" --reload
) &
API_PID=$!

echo "Starting frontend on http://localhost:${FRONTEND_PORT} ..."
(
  cd "$FRONTEND_DIR"
  VITE_API_BASE="http://localhost:${API_PORT}" npm run dev -- --host 0.0.0.0 --port "$FRONTEND_PORT"
) &
FRONTEND_PID=$!

wait -n "$API_PID" "$FRONTEND_PID"
