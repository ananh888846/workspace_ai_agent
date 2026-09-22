from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, TypedDict

from langgraph.graph import END, START, StateGraph


class AgentRuntimeState(TypedDict, total=False):
    """State của Agent Super-Graph; không chứa credential/secret."""

    request: Any
    context: Any
    intent: str
    capability: str | None
    action: str | None
    route: str
    result: Any


@dataclass(frozen=True)
class AgentRuntimeDependencies:
    """Dependency injection cho classification và capability handlers."""

    classify: Callable[[Any], tuple[str, str | None, str | None]]
    route_handlers: dict[str, Callable[[AgentRuntimeState], Any]]


class AgentRuntime:
    """Application entry cho Agent Run và LangGraph Super-Graph.

    Phase 2 đưa capability routing thành node/edge thật trong Super-Graph.
    Handler vẫn được inject từ Application boundary để Graph không biết
    SQL, credential secret hoặc provider API.
    """

    def __init__(self, dependencies: AgentRuntimeDependencies) -> None:
        self._graph = self._build_graph(dependencies)

    @staticmethod
    def _build_graph(dependencies: AgentRuntimeDependencies):
        handlers = dict(dependencies.route_handlers)

        def classify_request(state: AgentRuntimeState) -> AgentRuntimeState:
            intent, capability, action = dependencies.classify(state["request"])
            return {
                "intent": intent,
                "capability": capability,
                "action": action,
            }

        def route_request(state: AgentRuntimeState) -> AgentRuntimeState:
            capability = state.get("capability")
            if capability in handlers:
                return {"route": capability}
            if "default" in handlers:
                return {"route": "default"}
            return {"route": "unsupported"}

        graph = StateGraph(AgentRuntimeState)
        graph.add_node("classify_request", classify_request)
        graph.add_node("route_request", route_request)

        for route_name, handler in handlers.items():
            graph.add_node(
                f"execute_{route_name.replace('.', '_')}",
                lambda state, handler=handler: {"result": handler(state)},
            )

        if "default" not in handlers:
            graph.add_node(
                "execute_unsupported",
                lambda state: {
                    "result": {
                        "status": "unsupported_action",
                        "provider_called": False,
                    }
                },
            )

        graph.add_edge(START, "classify_request")
        graph.add_edge("classify_request", "route_request")

        def next_node(state: AgentRuntimeState) -> str:
            route = state.get("route", "unsupported")
            if route in handlers:
                return f"execute_{route.replace('.', '_')}"
            return "execute_unsupported"

        graph.add_conditional_edges("route_request", next_node)

        for route_name in handlers:
            graph.add_edge(f"execute_{route_name.replace('.', '_')}", END)
        if "default" not in handlers:
            graph.add_edge("execute_unsupported", END)

        return graph.compile()

    def run(self, *, request: Any, context: Any = None) -> Any:
        """Chạy Super-Graph với context không chứa secret."""
        state: AgentRuntimeState = {
            "request": request,
            "context": context,
        }
        result = self._graph.invoke(state)
        return result["result"]
