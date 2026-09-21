# API Phase 2 — Agent Chat Contract

## Mục tiêu

Phase 2A tạo HTTP boundary thật cho Web Chat nhưng chưa gọi LLM, credential,
tool hoặc provider API.

Endpoint chính:

POST /api/v1/agent/chat

## Request

{
  "message": "Tôi có những tài khoản Google nào?",
  "conversation_id": "optional-id",
  "account_hint": "optional-exact-account"
}

- message: bắt buộc.
- conversation_id: nếu không gửi, backend tạo ID.
- account_hint: hint chính xác cho account resolver; không phải quyền truy cập.

## Response contract

{
  "status": "ok",
  "conversation_id": "...",
  "message": "Backend HTTP contract đã nhận yêu cầu.",
  "execution": {
    "intent": "not_classified",
    "capability": null,
    "account": {
      "status": "not_evaluated",
      "hint": null
    },
    "authorization": {
      "status": "not_evaluated"
    },
    "provider_called": false
  }
}

## Boundary

Phase 2A chỉ chứng minh:

Web Chat
  ↓
POST /api/v1/agent/chat
  ↓
HTTP schema
  ↓
Application contract

Chưa được coi là:
- Authentication hoàn chỉnh.
- AccountResolver runtime.
- Authorization runtime.
- Credential resolution.
- Provider call.
- LLM intent classification.

## Phase kế tiếp

2A HTTP contract = DONE
2B AccountResolver runtime = NEXT
2C Authorization runtime
2D Web Chat → real API
2E Debug execution metadata

Không được bỏ qua Authorization để gọi credential/provider.
account_hint chỉ là dữ liệu đầu vào cho resolver; LLM không được tự quyết định
account hoặc permission.
