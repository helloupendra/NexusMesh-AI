from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "orchestrator"))

from nexus_orchestrator.application.services import OrchestrationService
from nexus_orchestrator.domain.models import (
    OrchestratorState,
    TaskDispatchMessage,
    TaskResultMessage,
    TaskStatus,
    TaskType,
)
from nexus_orchestrator.presentation.graph import build_orchestration_graph


class FakeMessageBus:
    def __init__(self) -> None:
        self.published: list[TaskDispatchMessage] = []

    def publish_task(self, message: TaskDispatchMessage) -> None:
        self.published.append(message)

    def await_result(self, task_id: str, timeout_seconds: int) -> TaskResultMessage:
        return TaskResultMessage(
            task_id=task_id,
            status=TaskStatus.COMPLETED.value,
            task_type=self.published[-1].task_type.value,
            result={"handled_by": self.published[-1].task_type.value},
            error=None,
        )

    def close(self) -> None:
        return None


class OrchestratorRoutingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.bus = FakeMessageBus()
        self.service = OrchestrationService(message_bus=self.bus, timeout_seconds=3)

    def test_dispatch_publishes_task_type(self) -> None:
        state = OrchestratorState(
            task_id="task-1",
            status=TaskStatus.CREATED,
            result=None,
            user_request="run signal generation",
            task_type=TaskType.SIGNAL_GENERATION,
            error=None,
        ).model_dump()

        update = self.service.dispatch(state)

        self.assertEqual(update["status"], TaskStatus.DISPATCHED.value)
        self.assertEqual(self.bus.published[0].task_type, TaskType.SIGNAL_GENERATION)

    def test_graph_routes_end_to_end(self) -> None:
        state = OrchestratorState(
            task_id="task-2",
            status=TaskStatus.CREATED,
            result=None,
            user_request="run backtest",
            task_type=TaskType.BACKTEST,
            error=None,
        ).model_dump()

        graph = build_orchestration_graph(self.service)
        final_state = graph.invoke(state)

        self.assertEqual(final_state["status"], TaskStatus.COMPLETED.value)
        self.assertEqual(final_state["result"]["handled_by"], TaskType.BACKTEST.value)

    def test_dispatch_supports_risk_evaluation_task_type(self) -> None:
        state = OrchestratorState(
            task_id="task-3",
            status=TaskStatus.CREATED,
            result=None,
            user_request="evaluate risk",
            task_type=TaskType.RISK_EVALUATION,
            error=None,
        ).model_dump()

        update = self.service.dispatch(state)

        self.assertEqual(update["status"], TaskStatus.DISPATCHED.value)
        self.assertEqual(self.bus.published[-1].task_type, TaskType.RISK_EVALUATION)


if __name__ == "__main__":
    unittest.main()
