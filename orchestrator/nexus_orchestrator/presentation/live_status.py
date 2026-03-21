from __future__ import annotations

import time
import uuid
from collections import deque
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from threading import Event, Lock, Thread
from typing import Any

import pika
from pika.exceptions import AMQPError

from ..application.ports import MessageBusError
from ..config import RabbitMQConfig
from ..domain.models import TaskDispatchMessage, TaskResultMessage, TaskType
from ..infrastructure.rabbitmq_gateway import RabbitMQGateway


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(slots=True)
class TaskRuntimeView:
    task_id: str
    task_type: str
    request: str
    status: str
    updated_at: str
    error: str | None = None
    result: dict[str, Any] | None = None


class LiveStatusStore:
    """Thread-safe in-memory state for live dashboard APIs and WebSocket snapshots."""

    def __init__(self, rabbitmq_endpoint: str, max_recent: int = 50) -> None:
        self._lock = Lock()
        self._rabbitmq_endpoint = rabbitmq_endpoint
        self._rabbitmq_online = False
        self._active_tasks: dict[str, TaskRuntimeView] = {}
        self._recent_tasks: deque[TaskRuntimeView] = deque(maxlen=max_recent)

    def set_rabbitmq_online(self, online: bool) -> None:
        with self._lock:
            self._rabbitmq_online = online

    def add_dispatched_task(self, task_id: str, request: str, task_type: TaskType) -> TaskRuntimeView:
        with self._lock:
            task = TaskRuntimeView(
                task_id=task_id,
                task_type=task_type.value,
                request=request,
                status="DISPATCHED",
                updated_at=utc_now_iso(),
                error=None,
                result=None,
            )
            self._active_tasks[task_id] = task
            return task

    def apply_result(self, message: TaskResultMessage) -> None:
        with self._lock:
            current = self._active_tasks.pop(message.task_id, None)
            request_text = "unknown"
            if current is not None:
                request_text = current.request
            elif isinstance(message.result, dict) and isinstance(message.result.get("request"), str):
                request_text = str(message.result["request"])

            resolved = TaskRuntimeView(
                task_id=message.task_id,
                task_type=message.task_type or "unknown",
                request=request_text,
                status=message.status,
                updated_at=utc_now_iso(),
                error=message.error,
                result=message.result,
            )
            self._recent_tasks.appendleft(resolved)

    def mark_dispatch_failure(self, task_id: str, error: str) -> None:
        with self._lock:
            failed = self._active_tasks.pop(task_id, None)
            if failed is None:
                return
            failed.status = "FAILED"
            failed.error = error
            failed.updated_at = utc_now_iso()
            self._recent_tasks.appendleft(failed)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            active = [asdict(task) for task in self._active_tasks.values()]
            active.sort(key=lambda item: item["updated_at"], reverse=True)
            recent = [asdict(task) for task in self._recent_tasks]

            node_status = {
                "orchestrator": "online",
                "csharp_worker": "online" if self._rabbitmq_online else "offline",
                "python_inference": "idle",
            }

            return {
                "timestamp": utc_now_iso(),
                "rabbitmq_connection": {
                    "online": self._rabbitmq_online,
                    "endpoint": self._rabbitmq_endpoint,
                },
                "active_tasks": active,
                "recent_tasks": recent,
                "metrics": {
                    "active_count": len(active),
                    "recent_count": len(recent),
                },
                "node_status": node_status,
            }


class TaskDispatchService:
    def __init__(self, config: RabbitMQConfig, store: LiveStatusStore) -> None:
        self._config = config
        self._store = store

    def dispatch(self, request: str, task_type: TaskType) -> TaskRuntimeView:
        task_id = uuid.uuid4().hex
        outbound = TaskDispatchMessage(task_id=task_id, request=request, task_type=task_type)
        task_view = self._store.add_dispatched_task(task_id=task_id, request=request, task_type=task_type)

        gateway = RabbitMQGateway(self._config)
        try:
            gateway.publish_task(outbound)
            self._store.set_rabbitmq_online(True)
            return task_view
        except MessageBusError as exc:
            self._store.set_rabbitmq_online(False)
            self._store.mark_dispatch_failure(task_id=task_id, error=str(exc))
            raise
        finally:
            gateway.close()


class StatusEventsConsumer:
    """Background consumer for dashboard-only task completion events."""

    def __init__(self, config: RabbitMQConfig, store: LiveStatusStore) -> None:
        self._config = config
        self._store = store
        self._stop_event = Event()
        self._thread: Thread | None = None

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = Thread(target=self._run, name="status-events-consumer", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None

    def _run(self) -> None:
        while not self._stop_event.is_set():
            connection: pika.BlockingConnection | None = None
            channel = None
            try:
                params = pika.ConnectionParameters(
                    host=self._config.host,
                    port=self._config.port,
                    virtual_host=self._config.virtual_host,
                    credentials=pika.PlainCredentials(
                        username=self._config.username,
                        password=self._config.password,
                    ),
                    heartbeat=self._config.heartbeat_seconds,
                    blocked_connection_timeout=self._config.results_timeout_seconds,
                )
                connection = pika.BlockingConnection(params)
                channel = connection.channel()
                channel.queue_declare(queue=self._config.status_events_queue, durable=True)
                self._store.set_rabbitmq_online(True)

                while not self._stop_event.is_set():
                    method, _, body = channel.basic_get(
                        queue=self._config.status_events_queue,
                        auto_ack=False,
                    )
                    if method is None:
                        time.sleep(0.25)
                        continue

                    try:
                        message = TaskResultMessage.model_validate_json(body)
                        self._store.apply_result(message)
                    finally:
                        channel.basic_ack(method.delivery_tag)
            except (AMQPError, OSError):
                self._store.set_rabbitmq_online(False)
                time.sleep(1.5)
            finally:
                try:
                    if channel is not None and channel.is_open:
                        channel.close()
                except Exception:
                    pass
                try:
                    if connection is not None and connection.is_open:
                        connection.close()
                except Exception:
                    pass
