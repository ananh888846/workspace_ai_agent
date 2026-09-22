from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, TypedDict

from langgraph.graph import END, START, StateGraph

from app.services.calendar_free_busy import BusyPeriod
from app.services.scheduling import AvailableSlot, SchedulingService


class SchedulingState(TypedDict, total=False):
    """Scheduling Graph V1: không chứa credential hoặc secret."""

    intent: str
    action: str
    search_start: datetime
    search_end: datetime
    duration_minutes: int
    max_results: int
    timezone: str
    calendar_ids: list[str]
    busy_periods: list[BusyPeriod]
    available_slots: list[AvailableSlot]
    conflicts: list[BusyPeriod]
    confirmation_state: str
    status: str
    error: str


@dataclass(frozen=True)
class SchedulingGraphDependencies:
    """Dependency runtime được tiêm vào Graph, không để Graph biết provider."""

    resolve_calendar: Callable[[SchedulingState], list[str]]
    get_free_busy: Callable[[SchedulingState, list[str]], list[BusyPeriod]]


def build_scheduling_graph(
    *,
    dependencies: SchedulingGraphDependencies,
    scheduling_service: SchedulingService | None = None,
):
    """Tạo Scheduling Graph V1 với dependency injection tại boundary."""
    service = scheduling_service or SchedulingService()

    def classify_request(state: SchedulingState) -> SchedulingState:
        return {"intent": "calendar", "action": "schedule"}

    def resolve_calendar(state: SchedulingState) -> SchedulingState:
        calendar_ids = dependencies.resolve_calendar(state)
        if not calendar_ids:
            return {"status": "error", "error": "calendar_not_resolved"}
        return {"calendar_ids": calendar_ids}

    def get_free_busy(state: SchedulingState) -> SchedulingState:
        periods = dependencies.get_free_busy(state, state["calendar_ids"])
        return {"busy_periods": periods}

    def find_available_slots(state: SchedulingState) -> SchedulingState:
        busy_periods = state.get("busy_periods", [])
        slots = service.find_available_slots(
            search_start=state["search_start"],
            search_end=state["search_end"],
            duration_minutes=state["duration_minutes"],
            busy_periods=busy_periods,
            max_results=state.get("max_results", 5),
        )
        conflicts = service.find_conflicts(
            search_start=state["search_start"],
            search_end=state["search_end"],
            busy_periods=busy_periods,
        )
        return {
            "available_slots": slots,
            "conflicts": conflicts,
            "status": "available" if slots else "no_slot",
        }

    def confirm(state: SchedulingState) -> SchedulingState:
        # V1 không có side effect nên không yêu cầu xác nhận.
        return {"confirmation_state": "not_required"}

    def format_result(state: SchedulingState) -> SchedulingState:
        return {"status": state.get("status", "ok")}

    graph = StateGraph(SchedulingState)
    graph.add_node("classify_request", classify_request)
    graph.add_node("resolve_calendar", resolve_calendar)
    graph.add_node("get_free_busy", get_free_busy)
    graph.add_node("find_available_slots", find_available_slots)
    graph.add_node("confirm", confirm)
    graph.add_node("format_result", format_result)

    graph.add_edge(START, "classify_request")
    graph.add_edge("classify_request", "resolve_calendar")
    graph.add_edge("resolve_calendar", "get_free_busy")
    graph.add_edge("get_free_busy", "find_available_slots")
    graph.add_edge("find_available_slots", "confirm")
    graph.add_edge("confirm", "format_result")
    graph.add_edge("format_result", END)

    return graph.compile()


def run_scheduling_graph(
    *,
    search_start: datetime,
    search_end: datetime,
    duration_minutes: int,
    dependencies: SchedulingGraphDependencies,
    max_results: int = 5,
    timezone: str = "Asia/Ho_Chi_Minh",
) -> SchedulingState:
    """Chạy Scheduling Graph V1 với input đã chuẩn hóa ở Application boundary."""
    initial: SchedulingState = {
        "search_start": search_start,
        "search_end": search_end,
        "duration_minutes": duration_minutes,
        "max_results": max_results,
        "timezone": timezone,
    }
    return build_scheduling_graph(dependencies=dependencies).invoke(initial)


# Biến này để LangGraph Studio nhận diện đồ thị khi chạy local.
def _dummy_resolve_calendar(state: SchedulingState) -> list[str]:
    return ["primary"]


def _dummy_get_free_busy(state: SchedulingState, calendar_ids: list[str]) -> list[BusyPeriod]:
    return []


graph = build_scheduling_graph(
    dependencies=SchedulingGraphDependencies(
        resolve_calendar=_dummy_resolve_calendar,
        get_free_busy=_dummy_get_free_busy,
    )
)
