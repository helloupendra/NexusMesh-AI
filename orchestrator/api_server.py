from __future__ import annotations

import asyncio

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .nexus_orchestrator.application.ports import MessageBusError
from .nexus_orchestrator.config import load_rabbitmq_config
from .nexus_orchestrator.domain.models import TaskType
from .nexus_orchestrator.presentation.live_status import (
    LiveStatusStore,
    StatusEventsConsumer,
    TaskDispatchService,
)

config = load_rabbitmq_config()
endpoint = f"amqp://{config.host}:{config.port}"
store = LiveStatusStore(rabbitmq_endpoint=endpoint)
dispatcher = TaskDispatchService(config=config, store=store)
status_consumer = StatusEventsConsumer(config=config, store=store)

app = FastAPI(title="NexusMesh Live API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CreateTaskRequest(BaseModel):
    request: str = Field(min_length=1)
    task_type: TaskType = TaskType.BACKTEST


@app.on_event("startup")
def on_startup() -> None:
    status_consumer.start()


@app.on_event("shutdown")
def on_shutdown() -> None:
    status_consumer.stop()


@app.get("/api/status")
def get_status() -> dict:
    return store.snapshot()


@app.get("/api/tasks/active")
def get_active_tasks() -> dict:
    return {"tasks": store.snapshot()["active_tasks"]}


@app.post("/api/tasks")
def create_task(payload: CreateTaskRequest) -> dict:
    try:
        task = dispatcher.dispatch(request=payload.request, task_type=payload.task_type)
        return task.__dict__
    except MessageBusError as exc:
        raise HTTPException(status_code=503, detail=f"Dispatch failed: {exc}") from exc


@app.websocket("/ws/status")
async def ws_status(websocket: WebSocket) -> None:
    await websocket.accept()

    try:
        while True:
            await websocket.send_json(store.snapshot())
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        return
