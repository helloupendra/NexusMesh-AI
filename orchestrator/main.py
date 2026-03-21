from __future__ import annotations

import argparse
import json
import uuid

from nexus_orchestrator.application.services import OrchestrationService
from nexus_orchestrator.config import load_rabbitmq_config
from nexus_orchestrator.domain.models import OrchestratorState, TaskStatus, TaskType
from nexus_orchestrator.infrastructure.rabbitmq_gateway import RabbitMQGateway
from nexus_orchestrator.presentation.graph import build_orchestration_graph


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="NexusMesh LangGraph orchestrator")
    parser.add_argument("--request", required=True, help="User request to dispatch")
    parser.add_argument(
        "--task-type",
        choices=[task_type.value for task_type in TaskType],
        default=TaskType.BACKTEST.value,
        help="Task routing hint for workers",
    )
    parser.add_argument(
        "--task-id",
        default=None,
        help="Optional explicit task id (defaults to generated UUID4 hex)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    task_id = args.task_id or uuid.uuid4().hex

    initial_state = OrchestratorState(
        task_id=task_id,
        status=TaskStatus.CREATED,
        result=None,
        user_request=args.request,
        task_type=TaskType(args.task_type),
        error=None,
    ).model_dump()

    config = load_rabbitmq_config()
    gateway = RabbitMQGateway(config=config)

    try:
        service = OrchestrationService(
            message_bus=gateway,
            timeout_seconds=config.results_timeout_seconds,
        )
        graph = build_orchestration_graph(service)
        final_state = graph.invoke(initial_state)
    finally:
        gateway.close()

    print(json.dumps(final_state, indent=2))


if __name__ == "__main__":
    main()
