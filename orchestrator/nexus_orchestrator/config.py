from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RabbitMQConfig:
    host: str
    port: int
    username: str
    password: str
    virtual_host: str
    task_queue: str
    results_queue: str
    results_timeout_seconds: int
    heartbeat_seconds: int


def load_rabbitmq_config() -> RabbitMQConfig:
    """Load RabbitMQ configuration from environment variables."""
    return RabbitMQConfig(
        host=os.getenv("RABBITMQ_HOST", "127.0.0.1"),
        port=int(os.getenv("RABBITMQ_PORT", "5672")),
        username=os.getenv("RABBITMQ_USERNAME", "guest"),
        password=os.getenv("RABBITMQ_PASSWORD", "guest"),
        virtual_host=os.getenv("RABBITMQ_VHOST", "/"),
        task_queue=os.getenv("TASK_QUEUE", "task_queue"),
        results_queue=os.getenv("RESULTS_QUEUE", "results_queue"),
        results_timeout_seconds=int(os.getenv("RESULTS_TIMEOUT_SECONDS", "120")),
        heartbeat_seconds=int(os.getenv("RABBITMQ_HEARTBEAT_SECONDS", "60")),
    )
