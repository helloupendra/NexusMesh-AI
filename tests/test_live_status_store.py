from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "orchestrator"))

from nexus_orchestrator.domain.models import TaskResultMessage, TaskType
from nexus_orchestrator.presentation.live_status import LiveStatusStore


class LiveStatusStoreTests(unittest.TestCase):
    def test_dispatched_task_enters_active_list(self) -> None:
        store = LiveStatusStore(rabbitmq_endpoint="amqp://localhost:5672")
        store.add_dispatched_task("task-1", "run backtest", TaskType.BACKTEST)

        snapshot = store.snapshot()
        self.assertEqual(snapshot["metrics"]["active_count"], 1)
        self.assertEqual(snapshot["active_tasks"][0]["task_type"], "backtest")

    def test_apply_result_moves_task_to_recent(self) -> None:
        store = LiveStatusStore(rabbitmq_endpoint="amqp://localhost:5672")
        store.add_dispatched_task("task-2", "generate signal", TaskType.SIGNAL_GENERATION)
        store.apply_result(
            TaskResultMessage(
                task_id="task-2",
                status="COMPLETED",
                task_type="signal_generation",
                result={"summary": "done"},
                error=None,
            )
        )

        snapshot = store.snapshot()
        self.assertEqual(snapshot["metrics"]["active_count"], 0)
        self.assertEqual(snapshot["metrics"]["recent_count"], 1)
        self.assertEqual(snapshot["recent_tasks"][0]["task_id"], "task-2")


if __name__ == "__main__":
    unittest.main()
