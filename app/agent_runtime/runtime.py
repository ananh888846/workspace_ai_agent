from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, TypedDict

from langgraph.graph import END, START, StateGraph


class AgentRuntimeState(TypedDict, total=False):
    """State tối thiểu của Agent Super-Graph; không chứa credential/secret."""

    request: Any
    context: Any
    intent: str
    capability: str | None
    action: str | None
    result: Any


@dataclass(frozen=True)
class AgentRuntimeDependencies:
    """Dependency injection cho Super-Graph."""

    classify: Callable[[Any], tuple[str, str | None, str | None]]
    execute: Callable[[AgentRuntimeState], Any]


class AgentRuntime:
    """Application entry cho Agent Run.

    Phase 1 chỉ tạo orchestration seam. Capability execution hiện tại được
    tiêm từ application callback để giữ regression baseline và tránh rewrite.
    """

    def __init__(self, dependencies: AgentRuntimeDependencies) -> None:
        self._graph = self._build_graph(dependencies)

    @staticmethod
    def _build_graph(dependencies: AgentRuntimeDependencies):
        def classify_request(state: AgentRuntimeState) -> AgentRuntimeState:
            intent, capability, action = dependencies.classify(state["request"])
            return {
                "intent": intent,
                "capability": capability,
                "action": action,
            }

        def execute_route(state: AgentRuntimeState) -> AgentRuntimeState:
            return {"result": dependencies.execute(state)}

        graph = StateGraph(AgentRuntimeState)
        graph.add_node("classify_request", classify_request)
        graph.add_node("execute_route", execute_route)
        graph.add_edge(START, "classify_request")
        graph.add_edge("classify_request", "execute_route")
        graph.add_edge("execute_route", END)
        return graph.compile()

    def run(self, *, request: Any, context: Any = None) -> Any:
        """Chạy Agent Super-Graph với context không chứa secret."""
        state: AgentRuntimeState = {
            "request": request,
            "context": context,
        }
        result = self._graph.invoke(state)
        return result["result"]
