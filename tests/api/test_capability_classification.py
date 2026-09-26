from app.api.chat import classify_chat_request
from app.api.schemas import ChatRequest


def test_explicit_knowledge_capability_classifies_as_knowledge_read():
    intent, capability, action = classify_chat_request(
        ChatRequest(
            message="Find information in Knowledge.",
            capability="knowledge.read",
        )
    )

    assert intent == "knowledge"
    assert capability == "knowledge.read"
    assert action == "read"


def test_explicit_calendar_write_still_classifies_as_calendar_write():
    intent, capability, action = classify_chat_request(
        ChatRequest(
            message="Create an event.",
            capability="calendar.write",
        )
    )

    assert intent == "calendar"
    assert capability == "calendar.write"
    assert action == "write"
