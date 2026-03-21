from __future__ import annotations

from typing import Protocol

from nexus_orchestrator.domain.models import TaskDispatchMessage, TaskResultMessage


class MessageBusError(RuntimeError):
    """Generic RabbitMQ transport-level failure."""


class MessageTimeoutError(MessageBusError):
    """Raised when the orchestrator does not receive a matching result in time."""


class MessageBus(Protocol):
    def publish_task(self, message: TaskDispatchMessage) -> None:
        """Publish a task to the queue used by workers."""

    def await_result(self, task_id: str, timeout_seconds: int) -> TaskResultMessage:
        """Block until a matching task result is returned or timeout is reached."""

    def close(self) -> None:
        """Close open transport resources."""
