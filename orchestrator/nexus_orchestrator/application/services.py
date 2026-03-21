from __future__ import annotations

from pydantic import ValidationError

from nexus_orchestrator.application.ports import MessageBus, MessageBusError, MessageTimeoutError
from nexus_orchestrator.domain.models import (
    OrchestratorGraphState,
    OrchestratorState,
    TaskDispatchMessage,
    TaskStatus,
    TaskType,
)


class OrchestrationService:
    """Application service that coordinates queue dispatch + result collection."""

    def __init__(self, message_bus: MessageBus, timeout_seconds: int) -> None:
        self._message_bus = message_bus
        self._timeout_seconds = timeout_seconds

    def dispatch(self, state: OrchestratorGraphState) -> OrchestratorGraphState:
        try:
            current = OrchestratorState.model_validate(state)
            outbound = TaskDispatchMessage(
                task_id=current.task_id,
                request=current.user_request,
                task_type=TaskType(current.task_type),
            )
            self._message_bus.publish_task(outbound)
            return {
                "status": TaskStatus.DISPATCHED.value,
                "error": None,
            }
        except (ValidationError, MessageBusError) as exc:
            return {
                "status": TaskStatus.FAILED.value,
                "error": f"Dispatcher failed: {exc}",
            }

    def await_result(self, state: OrchestratorGraphState) -> OrchestratorGraphState:
        try:
            current = OrchestratorState.model_validate(state)
        except ValidationError as exc:
            return {
                "status": TaskStatus.FAILED.value,
                "error": f"State validation failed before await_result: {exc}",
            }

        if current.status != TaskStatus.DISPATCHED:
            return {
                "status": TaskStatus.FAILED.value,
                "error": "Cannot wait for results because task is not in DISPATCHED state.",
            }

        try:
            result_message = self._message_bus.await_result(
                task_id=current.task_id,
                timeout_seconds=self._timeout_seconds,
            )
        except MessageTimeoutError as exc:
            return {
                "status": TaskStatus.TIMED_OUT.value,
                "error": str(exc),
            }
        except MessageBusError as exc:
            return {
                "status": TaskStatus.FAILED.value,
                "error": f"Result retrieval failed: {exc}",
            }

        status = result_message.status
        if status not in {TaskStatus.COMPLETED.value, TaskStatus.FAILED.value}:
            status = TaskStatus.COMPLETED.value

        return {
            "status": status,
            "result": result_message.result,
            "error": result_message.error,
        }
