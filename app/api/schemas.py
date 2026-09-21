from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ChatRequest:
    message: str
    conversation_id: str | None = None
    account_hint: str | None = None
    capability: str | None = None
    action: str | None = None
    target_resource: str | None = None


@dataclass(frozen=True)
class ChatResponse:
    status: str
    conversation_id: str
    message: str
    execution: dict[str, Any]
