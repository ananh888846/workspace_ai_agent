from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, TypedDict

from langgraph.graph import END, START, StateGraph

from app.services.calendar_free_busy import BusyPeriod
from app.services.scheduling import AvailableSlot, SchedulingService


class SchedulingState(TypedDict, total=False):
    """State tối thiểu của Scheduling Graph V1, không chứa credential secret."""

    intent: str
    action: str
    search_start: datetime
    search_end: datetime
    duration_minutes: int
    max_results: int
    calendar_ids: list[str]
    busy_periods: list[BusyPeriod]
    available_slots: list[AvailableSlot]
    conflicts: list[BusyPeriod]
    status: str
    error: str


@dataclass(frozen=True)
class SchedulingGraphDependencies:
    """Các dependency runtime được tiêm vào Graph, tránh Graph biết provider."""

    resolve_calendar: Callable[[SchedulingState], list[str]]
    get_free_busy: Callable[[SchedulingState, list[str]], list[BusyPeriod]]


def build_scheduling_graph(
    *,
    dependencies: SchedulingGraphDependencies,
    scheduling_service: SchedulingService | None = None,
):
    """Tạo Scheduling Graph V1 với dependency injection ở boundary."""
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
        slots = service.find_available_slots(
            search_start=state["search_start"],
            search_end=state["search_end"],
            duration_minutes=state["duration_minutes"],
            busy_periods=state.get("busy_periods", []),
            max_results=state.get("max_results", 5),
        )
        return {
            "available_slots": slots,
            "status": "available" if slots else "no_slot",
        }

    def format_result(state: SchedulingState) -> SchedulingState:
        return state

    graph = StateGraph(SchedulingState)
    graph.add_node("classify_request", classify_request)
    graph.add_node("resolve_calendar", resolve_calendar)
    graph.add_node("get_free_busy", get_free_busy)
    graph.add_node("find_available_slots", find_available_slots)
    graph.add_node("format_result", format_result)

    graph.add_edge(START, "classify_request")
    graph.add_edge("classify_request", "resolve_calendar")
    graph.add_edge("resolve_calendar", "get_free_busy")
    graph.add_edge("get_free_busy", "find_available_slots")
    graph.add_edge("find_available_slots", "format_result")
    graph.add_edge("format_result", END)

    return graph.compile()


def run_scheduling_graph(
    *,
    search_start: datetime,
    search_end: datetime,
    duration_minutes: int,
    dependencies: SchedulingGraphDependencies,
    max_results: int = 5,
) -> SchedulingState:
    """Chạy Scheduling Graph V1 với input đã được chuẩn hóa ở application boundary."""
    initial: SchedulingState = {
        "search_start": search_start,
        "search_end": search_end,
        "duration_minutes": duration_minutes,
        "max_results": max_results,
    }
    return build_scheduling_graph(dependencies=dependencies).invoke(initial)
