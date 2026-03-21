from __future__ import annotations

from enum import StrEnum
from typing import Any, TypedDict

from pydantic import BaseModel, Field


class TaskStatus(StrEnum):
    CREATED = "CREATED"
    DISPATCHED = "DISPATCHED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"


class TaskType(StrEnum):
    BACKTEST = "backtest"
    SIGNAL_GENERATION = "signal_generation"
    RISK_EVALUATION = "risk_evaluation"


class OrchestratorState(BaseModel):
    task_id: str = Field(min_length=1)
    status: TaskStatus = TaskStatus.CREATED
    result: dict[str, Any] | None = None
    user_request: str = Field(min_length=1)
    task_type: TaskType = TaskType.BACKTEST
    error: str | None = None


class OrchestratorGraphState(TypedDict, total=False):
    task_id: str
    status: str
    result: dict[str, Any] | None
    user_request: str
    task_type: str
    error: str | None


class TaskDispatchMessage(BaseModel):
    task_id: str = Field(min_length=1)
    request: str = Field(min_length=1)
    task_type: TaskType = TaskType.BACKTEST


class TaskResultMessage(BaseModel):
    task_id: str = Field(min_length=1)
    status: str = Field(min_length=1)
    task_type: str | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
