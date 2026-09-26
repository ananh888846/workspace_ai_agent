from app.api.chat import classify_chat_request
from app.api.schemas import ChatRequest


def classify(message: str):
    return classify_chat_request(ChatRequest(message=message))


def test_natural_language_knowledge_queries_route_to_knowledge_read():
    assert classify("Qdrant dùng để làm gì trong hệ thống này?") == (
        "knowledge",
        "knowledge.read",
        "read",
    )
    assert classify("Tài liệu nội bộ về kiến trúc AI ở đâu?") == (
        "knowledge",
        "knowledge.read",
        "read",
    )
    assert classify("Ollama tạo embedding như thế nào?") == (
        "knowledge",
        "knowledge.read",
        "read",
    )


def test_calendar_routing_remains_calendar_specific():
    assert classify("Hôm nay tôi có cuộc họp nào?") == (
        "calendar",
        "calendar.read",
        "read",
    )
    assert classify("Tìm thời gian trống ngày mai") == (
        "calendar",
        "calendar.read",
        "schedule",
    )
