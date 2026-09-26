from app.api.chat import classify_chat_request
from app.api.schemas import ChatRequest


def test_workspace_ecosystem_question_routes_to_knowledge():
    request = ChatRequest(message="Workspace AI Agent ecosystem này dùng để làm gì?")

    assert classify_chat_request(request) == ("knowledge", "knowledge.read", "read")


def test_qdrant_question_routes_to_knowledge():
    request = ChatRequest(message="Qdrant dùng để làm gì trong hệ thống này?")

    assert classify_chat_request(request) == ("knowledge", "knowledge.read", "read")


def test_calendar_question_still_routes_to_calendar():
    request = ChatRequest(message="Hôm nay tôi có cuộc họp nào?")

    assert classify_chat_request(request) == ("calendar", "calendar.read", "read")
