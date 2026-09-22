from __future__ import annotations

from app.agent_runtime.runtime import AgentRuntime, AgentRuntimeDependencies


def test_agent_runtime_routes_classified_request_without_secret_state() -> None:
    calls: list[tuple[str, str | None, str | None]] = []

    def classify(request):
        return "calendar", "calendar.read", "read"

    def execute_calendar(state):
        calls.append((state["intent"], state["capability"], state["action"]))
        assert state["route"] == "calendar.read"
        assert "credential" not in state
        assert "access_token" not in state
        return {"status": "ok"}

    runtime = AgentRuntime(
        AgentRuntimeDependencies(
            classify=classify,
            route_handlers={"calendar.read": execute_calendar},
        )
    )

    result = runtime.run(request={"message": "đọc lịch"})

    assert result == {"status": "ok"}
    assert calls == [("calendar", "calendar.read", "read")]


def test_agent_runtime_uses_default_handler_when_capability_is_unknown() -> None:
    calls: list[str] = []

    def classify(request):
        return "chat", None, None

    def execute_default(state):
        calls.append(state["intent"])
        assert state["route"] == "default"
        return {"status": "default"}

    runtime = AgentRuntime(
        AgentRuntimeDependencies(
            classify=classify,
            route_handlers={"default": execute_default},
        )
    )

    assert runtime.run(request={"message": "xin chào"}) == {"status": "default"}
    assert calls == ["chat"]


def test_agent_runtime_returns_unsupported_without_default_handler() -> None:
    def classify(request):
        return "unknown", "unknown.capability", "read"

    runtime = AgentRuntime(
        AgentRuntimeDependencies(
            classify=classify,
            route_handlers={"calendar.read": lambda state: {"status": "wrong"}},
        )
    )

    result = runtime.run(request={"message": "không xác định"})

    assert result == {
        "status": "unsupported_action",
        "provider_called": False,
    }
