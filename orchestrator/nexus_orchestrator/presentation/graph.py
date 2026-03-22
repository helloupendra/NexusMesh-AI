from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from ..application.services import OrchestrationService
from ..domain.models import OrchestratorGraphState


def build_orchestration_graph(service: OrchestrationService):
    """Build and compile the LangGraph state machine."""
    workflow = StateGraph(OrchestratorGraphState)

    workflow.add_node("Dispatcher", service.dispatch)
    workflow.add_node("AwaitResult", service.await_result)

    workflow.add_edge(START, "Dispatcher")
    workflow.add_edge("Dispatcher", "AwaitResult")
    workflow.add_edge("AwaitResult", END)

    return workflow.compile()
