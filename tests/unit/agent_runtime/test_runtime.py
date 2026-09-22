from __future__ import annotations

from app.agent_runtime.runtime import AgentRuntime, AgentRuntimeDependencies


def test_agent_runtime_routes_classified_request_without_secret_state() -> None:
    calls: list[tuple[str, str | None, str | None]] = []

    def classify(request):
        return "calendar", "calendar.read", "read"

    def execute(state):
        calls.append((state["intent"], state["capability"], state["action"]))
        assert "credential" not in state
        assert "access_token" not in state
        return {"status": "ok"}

    runtime = AgentRuntime(
        AgentRuntimeDependencies(classify=classify, execute=execute)
    )

    result = runtime.run(request={"message": "đọc lịch"})

    assert result == {"status": "ok"}
    assert calls == [("calendar", "calendar.read", "read")]
