from __future__ import annotations

import time
from typing import Final

import pika
from pika.adapters.blocking_connection import BlockingChannel
from pika.exceptions import AMQPError
from pydantic import ValidationError

from ..application.ports import MessageBusError, MessageTimeoutError
from ..config import RabbitMQConfig
from ..domain.models import TaskDispatchMessage, TaskResultMessage


_POLL_INTERVAL_SECONDS: Final[float] = 0.20


class RabbitMQGateway:
    """RabbitMQ adapter implementing dispatch/wait semantics over two queues."""

    def __init__(self, config: RabbitMQConfig) -> None:
        self._config = config
        self._connection: pika.BlockingConnection | None = None
        self._channel: BlockingChannel | None = None

    def publish_task(self, message: TaskDispatchMessage) -> None:
        channel = self._get_or_create_channel()
        payload = message.model_dump_json().encode("utf-8")

        try:
            channel.basic_publish(
                exchange="",
                routing_key=self._config.task_queue,
                body=payload,
                properties=pika.BasicProperties(
                    content_type="application/json",
                    delivery_mode=2,
                    correlation_id=message.task_id,
                ),
                mandatory=False,
            )
        except AMQPError as exc:
            raise MessageBusError(f"Failed to publish task {message.task_id}: {exc}") from exc

    def await_result(self, task_id: str, timeout_seconds: int) -> TaskResultMessage:
        channel = self._get_or_create_channel()
        deadline = time.monotonic() + timeout_seconds

        while time.monotonic() < deadline:
            try:
                method, properties, body = channel.basic_get(
                    queue=self._config.results_queue,
                    auto_ack=False,
                )
            except AMQPError as exc:
                raise MessageBusError(f"Failed while polling results queue: {exc}") from exc

            if method is None:
                time.sleep(_POLL_INTERVAL_SECONDS)
                continue

            try:
                message = TaskResultMessage.model_validate_json(body)
            except ValidationError:
                # Discard malformed messages so orchestration cannot deadlock forever.
                channel.basic_ack(method.delivery_tag)
                continue

            if message.task_id != task_id:
                # Keep other task messages in-flight for a matching orchestrator.
                channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                time.sleep(_POLL_INTERVAL_SECONDS)
                continue

            channel.basic_ack(method.delivery_tag)
            return message

        raise MessageTimeoutError(
            f"Timed out after {timeout_seconds}s waiting for task_id={task_id} on {self._config.results_queue}."
        )

    def close(self) -> None:
        if self._channel is not None and self._channel.is_open:
            self._channel.close()
            self._channel = None
        if self._connection is not None and self._connection.is_open:
            self._connection.close()
            self._connection = None

    def _get_or_create_channel(self) -> BlockingChannel:
        if self._channel is not None and self._channel.is_open:
            return self._channel

        parameters = pika.ConnectionParameters(
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

        try:
            self._connection = pika.BlockingConnection(parameters)
            self._channel = self._connection.channel()
            self._channel.queue_declare(queue=self._config.task_queue, durable=True)
            self._channel.queue_declare(queue=self._config.results_queue, durable=True)
        except AMQPError as exc:
            self.close()
            raise MessageBusError(f"RabbitMQ connection setup failed: {exc}") from exc

        return self._channel
