
# API_CONTRACT_LARAVEL_AGENT_V1.md

> Trạng thái: **API CONTRACT V1 — DESIGN LOCK**
>
> Tài liệu này chốt boundary HTTP giữa project Laravel Web độc lập và workspace_ai_agent.

## 1. Mục tiêu

API Contract V1 là hợp đồng giao tiếp giữa Laravel Web và Workspace AI Agent. Hai project/repository độc lập, có thể chạy trên hai server khác nhau.

Mục tiêu:
- Laravel gọi Agent qua HTTPS server-to-server.
- Browser không gọi Agent trực tiếp.
- Agent xác thực Laravel trước khi tạo execution context.
- Laravel truyền User/Organization context.
- Agent tự thực hiện authorization.
- Agent sở hữu capability routing, account resolution, credential resolution và provider execution.
- Contract có thể mở rộng cho Calendar, Gmail, Knowledge, Smart Home, MCP và Webhook.

Authentication chi tiết nằm ở docs/AUTHENTICATION_LARAVEL_AGENT_V1.md.

## 2. Boundary

```
Browser
   ↓ HTTPS
Laravel Web
   ↓ HTTPS + server-to-server authentication
Workspace AI Agent
   ├── AgentContext
   ├── Classification
   ├── Capability Routing
   ├── Authorization
   ├── Account Resolver
   ├── Credential Resolver
   └── Tool / Provider
```

Quy tắc:
1. Browser chỉ giao tiếp với Laravel.
2. Laravel gọi Agent bằng server-to-server authentication.
3. Browser không biết Agent server token.
4. Laravel không gọi Google/provider trực tiếp khi capability thuộc Agent.
5. Laravel không truy cập Agent DB.
6. Agent không truy cập Laravel DB.
7. LLM không quyết định permission.
8. Provider chỉ được gọi sau Authorization = allow.
9. Credential/secret không vào prompt, graph state, log hoặc response.
10. X-User-Id/X-Organization-Id là identity/tenant context, không thay thế authorization.

## 3. Version và endpoint

API prefix:

```
/api/v1
```

Endpoint chuẩn:

```
POST /api/v1/agent/chat
```

Breaking change phải tạo V2; không âm thầm đổi semantics của V1.

## 4. Transport

Production dùng HTTPS.

Local có thể dùng http://127.0.0.1:8000 nhưng vẫn phải kiểm tra server-to-server authentication.

```
Content-Type: application/json
```

UTF-8.

## 5. Authentication headers

Laravel → Agent:

```
Authorization: Bearer <server-to-server-token>
Content-Type: application/json
X-Request-Id: <uuid>
X-User-Id: <user-id>
X-Organization-Id: <organization-id>
```

| Header | Required | Ý nghĩa |
|---|---:|---|
| Authorization | Có | xác thực Laravel với Agent |
| Content-Type | Có | JSON |
| X-Request-Id | Có | trace request |
| X-User-Id | Có | user context do Laravel xác định |
| X-Organization-Id | Có | organization/tenant context |

Browser không được tự đặt identity để gọi Agent.

V1 server authentication:

```
Laravel:
WORKSPACE_AI_AGENT_URL=https://ai.example.com
WORKSPACE_AI_AGENT_TOKEN=<long-random-secret>

Agent:
AGENT_SERVER_TOKEN=<same-secret>
```

Token không commit Git, không đưa vào frontend/prompt/chat/log/response.

## 6. POST /api/v1/agent/chat

Mục đích: nhận user command, classify, route capability, resolve account, authorize, resolve credential và thực thi provider khi được phép.

### Request core

```json
{
  "message": "Ngày mai tôi có lịch gì?",
  "conversation_id": "conv-01",
  "account_hint": "google-work",
  "capability": "calendar.read",
  "action": "read",
  "target_resource": null
}
```

### Core fields

| Field | Type | Required | Ý nghĩa |
|---|---|---:|---|
| message | string | Có | user message, không rỗng |
| conversation_id | string/null | Không | conversation đang dùng |
| account_hint | string/null | Không | gợi ý external account |
| capability | string/null | Không | capability hint |
| action | string/null | Không | action hint |
| target_resource | string/null | Không | resource cụ thể |

Client có thể chỉ gửi message để Agent tự classify. Nếu client truyền capability/action, đó vẫn chỉ là hint và không bypass authorization.

## 7. Conversation

Ví dụ:

```json
{
  "message": "Ngày mai tôi có lịch gì?",
  "conversation_id": "conv-01"
}
```

Nếu chưa có conversation_id, client có thể bỏ field hoặc gửi null. Agent có thể tạo ID và phải trả lại ID đó.

Laravel phải lưu conversation_id để dùng cho message tiếp theo.

Không dùng Laravel session ID làm conversation ID.

## 8. Calendar extension fields V1

Code hiện tại có các field Calendar:

```json
{
  "event_id": null,
  "summary": null,
  "start": null,
  "end": null,
  "description": null,
  "location": null,
  "confirmed": false,
  "search_start": null,
  "search_end": null,
  "duration_minutes": 60,
  "max_results": 5,
  "recurrence": null
}
```

| Field | Type | Default | Dùng cho |
|---|---|---|---|
| event_id | string/null | null | update/delete |
| summary | string/null | null | create/update |
| start | string/null | null | read/create/update/free_busy |
| end | string/null | null | read/create/update/free_busy |
| description | string/null | null | create/update |
| location | string/null | null | create/update |
| confirmed | boolean | false | write confirmation |
| search_start | string/null | null | schedule |
| search_end | string/null | null | schedule |
| duration_minutes | integer | 60 | schedule |
| max_results | integer | 5 | schedule |
| recurrence | string/null | null | create/update |

duration_minutes: 1–1440. max_results: 1–20.

## 9. Capability/action contract V1

| Capability | Action | Ý nghĩa |
|---|---|---|
| calendar.read | read | đọc calendar/event |
| calendar.read | schedule | tìm khoảng thời gian |
| calendar.read | free_busy | kiểm tra bận/rảnh |
| calendar.write | create | tạo event |
| calendar.write | update | cập nhật event |
| calendar.write | delete | xóa event |

Capability tương lai có thể thêm gmail.read, gmail.write, knowledge.read, knowledge.write, smart_home.read, smart_home.write, mcp.execute, webhook.execute.

Thêm capability không được phá client V1.

## 10. Classification và routing

Natural language:

```
"Ngày mai tôi có lịch gì?"
        ↓
intent=calendar
capability=calendar.read
action=read
```

Client hint:

```json
{
  "message": "Đọc lịch",
  "capability": "calendar.read",
  "action": "read"
}
```

Agent vẫn validate tất cả hint.

Runtime order:

```
Classify
  ↓
Route
  ↓
Resolve Account
  ↓
Authorization
  ↓
Resolve Credential
  ↓
Provider
```

Không được gọi provider trước authorization.

## 11. AgentContext

Sau transport authentication, Agent tạo execution context gồm:

```
request_id
user_id
organization_id
session_id
device_id
capability
action
target_account
target_resource
target_package
metadata
```

Không đưa access token, refresh token hoặc secret vào AgentContext/Graph state.

## 12. Success response envelope

Contract mục tiêu:

```json
{
  "status": "ok",
  "conversation_id": "conv-01",
  "message": "Ngày mai bạn có 2 lịch.",
  "execution": {
    "intent": "calendar",
    "capability": "calendar.read",
    "action": "read",
    "account": {
      "status": "resolved",
      "account_id": "google-work",
      "provider": "google"
    },
    "authorization": {
      "status": "allow"
    },
    "credential": {
      "status": "ready"
    },
    "provider_called": true
  },
  "request_id": "req-123"
}
```

Top-level contract:

| Field | Type | Ý nghĩa |
|---|---|---|
| status | string | trạng thái tổng thể |
| conversation_id | string | conversation ID |
| message | string | câu trả lời |
| execution | object | execution metadata |
| request_id | string | trace ID |

Code hiện tại đã có status, conversation_id, message và execution. request_id trong response là contract target cần implementation hoàn thiện.

## 13. Execution contract

Tối thiểu:

```json
{
  "intent": "calendar",
  "capability": "calendar.read",
  "action": "read",
  "account": {},
  "authorization": {},
  "credential": {},
  "provider_called": false
}
```

Account có thể expose trạng thái an toàn:

```json
{
  "status": "resolved",
  "account_id": "google-work",
  "provider": "google",
  "display_name": "Work Google",
  "email": "work@example.com"
}
```

Không trả credential.

Authorization:

```json
{"status":"allow"}
```

hoặc:

```json
{"status":"deny","code":"authorization_denied"}
```

Credential chỉ expose status:

```json
{"status":"ready"}
```

hoặc:

```json
{"status":"oauth_required"}
```

Không expose access_token, refresh_token, client_secret hoặc encryption key.

provider_called:
- false = provider chưa được gọi;
- true = provider boundary đã được gọi.

Authorization deny hoặc credential chưa ready phải giữ provider_called=false.

## 14. OAuth required

Khi Google account tồn tại nhưng credential chưa sẵn sàng:

```json
{
  "account": {"status": "resolved"},
  "authorization": {"status": "allow"},
  "credential": {"status": "oauth_required"},
  "provider_called": false
}
```

Laravel/UI có thể dùng trạng thái này để hiển thị flow kết nối Google.

OAuth details nằm ở docs/AUTHENTICATION_LARAVEL_AGENT_V1.md.

## 15. Authorization denied

HTTP:

```
403 Forbidden
```

Structured error:

```json
{
  "status": "error",
  "error": {
    "code": "AUTHORIZATION_DENIED",
    "message": "Bạn không có quyền sử dụng capability này."
  },
  "request_id": "req-123"
}
```

Nếu execution envelope được trả, authorization phải là deny và provider_called=false.

Authorization deny tuyệt đối không gọi provider.

## 16. Account resolution

Một user có thể có nhiều Google accounts:

```
User 100
 ├── google-personal
 ├── google-work
 └── google-company
```

Request có thể có account_hint.

Nếu nhiều account phù hợp mà policy không thể chọn an toàn, Agent yêu cầu user chọn account; LLM không tự đoán account có quyền.

## 17. Error contract

Structured error:

```json
{
  "status": "error",
  "error": {
    "code": "ERROR_CODE",
    "message": "Thông báo an toàn cho client."
  },
  "request_id": "req-123"
}
```

HTTP status:

| HTTP | Ý nghĩa |
|---:|---|
| 400 | bad request/context |
| 401 | server-to-server authentication thất bại |
| 403 | authorization denied |
| 404 | resource/account không tồn tại hoặc không expose |
| 409 | conflict/confirmation/state conflict |
| 422 | validation error |
| 429 | rate limit |
| 502 | upstream/provider boundary error |
| 504 | timeout |

Không trả stack trace, secret, OAuth token, filesystem path, database credential hoặc environment nội bộ.

## 18. Confirmation và side effect

Các action có side effect như calendar.write:create/update/delete phải có confirmation policy phù hợp.

Calendar V1 có:

```json
{"confirmed": false}
```

confirmed=true không bypass authorization.

Confirmation là execution condition; Authorization vẫn do Agent quyết định.

## 19. Idempotency

Side-effect request dùng:

```http
Idempotency-Key: <uuid>
```

Ví dụ:

```
POST /api/v1/agent/chat
Authorization: Bearer ...
X-Request-Id: req-123
Idempotency-Key: idem-456
```

Mục tiêu: retry sau network timeout không tạo side effect trùng.

Implementation persistence/handling là contract target; client nên hỗ trợ ngay từ đầu.

Không retry mù side effect nếu không biết provider đã thực thi hay chưa.

## 20. Timeout và retry

Laravel config theo Authentication Architecture:

```env
WORKSPACE_AI_AGENT_CONNECT_TIMEOUT=5
WORKSPACE_AI_AGENT_TIMEOUT=30
```

Retry chỉ cho lỗi xác định retryable.

Không retry vô hạn.

Không retry mù create/update/delete event, gửi mail hoặc device command.

Nếu side effect có trạng thái không chắc chắn, dùng idempotency/reconciliation.

## 21. Request ID

Laravel tạo:

```http
X-Request-Id: req-<uuid>
```

Trace xuyên:

```
Laravel
  ↓
Agent Request
  ↓
Agent Run
  ↓
Capability Handler
  ↓
Tool
  ↓
Provider
```

Response contract trả request_id.

## 22. Laravel client boundary

Project Laravel riêng nên có:

```
app/
└── Services/
    └── AiAgent/
        └── WorkspaceAiAgentClient.php
```

Client chịu trách nhiệm:
1. Agent base URL;
2. server token;
3. request ID;
4. authenticated user context;
5. organization context;
6. JSON contract;
7. timeout;
8. retry policy;
9. HTTP error mapping;
10. không expose token cho browser.

Controller/UI không tự ghép Authorization header.

## 23. Ví dụ Laravel → Agent

User:

> Ngày mai tôi có lịch gì?

Headers:

```
POST /api/v1/agent/chat
Authorization: Bearer <server-token>
Content-Type: application/json
X-Request-Id: req-9e8...
X-User-Id: user-100
X-Organization-Id: org-10
```

Body:

```json
{
  "message": "Ngày mai tôi có lịch gì?",
  "conversation_id": "conv-01"
}
```

Agent classify → account resolver → authorization → credential → Google Calendar.

## 24. Ví dụ Calendar write

```json
{
  "message": "Tạo cuộc họp ngày mai lúc 9 giờ, tên Họp team.",
  "conversation_id": "conv-01",
  "capability": "calendar.write",
  "action": "create",
  "summary": "Họp team",
  "confirmed": true
}
```

confirmed=true không bypass authorization/account/credential checks.

## 25. Google OAuth boundary

Agent hiện có:

```
GET /auth/google/start
GET /auth/google/callback
```

OAuth start hiện nhận account_id, capability và identity context.

Ví dụ:

```
GET /auth/google/start?account_id=google-work&capability=calendar.read
```

OAuth callback trả safe result; không trả access token/refresh token.

OAuth state phải gắn user/organization/provider, có expiry và chống replay theo Authentication Architecture.

## 26. Organization boundary

Laravel gửi X-Organization-Id nhưng Agent vẫn phải kiểm tra user/org relationship và authorization của Agent.

Luồng:

```
Laravel authenticated user
  ↓
Laravel selected organization
  ↓
Agent authenticated request
  ↓
Agent verifies user/org
  ↓
Capability authorization
```

Không coi header là bằng chứng duy nhất user thuộc organization.

## 27. Compatibility rules

V1:
1. Không đổi endpoint theo kiểu breaking.
2. Không đổi semantics field hiện có.
3. Có thể thêm optional request fields.
4. Có thể thêm response fields.
5. Không đổi type field hiện có.
6. Không biến optional thành required trong V1.
7. Breaking change tạo V2.
8. Client bỏ qua response fields không biết.
9. Capability mới không được làm hỏng client cũ.

## 28. UI không phụ thuộc implementation

Laravel UI chỉ phụ thuộc API contract:

```
status
conversation_id
message
execution
request_id
error
```

Không phụ thuộc Python class, LangGraph node, database table, repository implementation, provider SDK hoặc filesystem path.

## 29. Ownership

### Laravel sở hữu
- Web UI;
- login/session;
- organization selection;
- chat UI;
- browser security;
- presentation;
- Agent API client.

### Agent sở hữu
- AgentContext;
- classification/routing;
- authorization;
- account resolver;
- credential resolver;
- tool/provider;
- Google integration;
- Knowledge;
- Agent memory;
- audit/execution.

## 30. Những gì V1 chưa định nghĩa

- Laravel authentication package cụ thể;
- Laravel UI framework;
- Laravel database schema chi tiết;
- Agent DB access từ Laravel;
- public third-party API;
- OAuth token delivery cho browser;
- webhook contract;
- MCP public protocol contract;
- streaming/WebSocket;
- file upload contract;
- Knowledge API riêng.

Các phần này sẽ có contract riêng khi triển khai.

## 31. Acceptance Criteria

### Transport
- [ ] POST /api/v1/agent/chat.
- [ ] Production HTTPS.
- [ ] JSON UTF-8.
- [ ] Server-to-server Bearer token.
- [ ] Browser không có server token.

### Identity
- [ ] Laravel lấy user từ authenticated session.
- [ ] Laravel gửi X-User-Id.
- [ ] Laravel gửi X-Organization-Id.
- [ ] Agent validate context.
- [ ] Browser không quyết định Agent identity.

### Chat
- [ ] message bắt buộc, không rỗng.
- [ ] conversation_id optional.
- [ ] Agent trả conversation_id.
- [ ] account_hint/capability/action/target_resource optional.

### Execution
- [ ] classify trước route.
- [ ] account resolve trước authorization.
- [ ] authorization trước credential/provider.
- [ ] provider chỉ sau allow + credential ready.
- [ ] provider_called=false khi deny/oauth_required.
- [ ] credential secret không có trong response.

### Errors
- [ ] 401/403/404/409/422/429/502/504 theo contract.
- [ ] structured error code/message/request_id.
- [ ] không trả stack trace/secret.

### Reliability
- [ ] X-Request-Id trace xuyên Agent.
- [ ] timeout có giới hạn.
- [ ] retry có giới hạn.
- [ ] side-effect không retry mù.
- [ ] Idempotency-Key cho side-effect.

## 32. Implementation gap được ghi rõ

Tài liệu này chốt contract, nhưng không giả định mọi mục đã runtime-verified.

Code hiện tại đã có request model và Calendar execution flow tương ứng với phần lớn contract. Các mục cần implementation/verification tiếp theo:
- response request_id;
- server-to-server authentication middleware/dependency;
- structured HTTP error envelope;
- Idempotency-Key persistence/handling;
- timeout/retry policy trong Laravel client.

Không ghi PASS cho các mục trên chỉ vì tài liệu đã được commit.

## 33. Trạng thái chốt

**API CONTRACT V1 — LOCKED FOR IMPLEMENTATION**

Đã chốt:
- Laravel là project riêng.
- Agent boundary là HTTP API.
- Endpoint chuẩn POST /api/v1/agent/chat.
- Bearer server-to-server authentication V1.
- X-Request-Id, X-User-Id, X-Organization-Id.
- Core request fields.
- Calendar V1 extension fields.
- Capability/action contract.
- Conversation ID.
- Execution envelope.
- Authorization/provider boundary.
- OAuth-required behavior.
- Error/status model.
- Timeout/retry/idempotency rules.
- Compatibility rules.
- Ownership boundary.

## 34. Next Step

1. Implement/verify Agent API boundary theo contract.
2. Tạo standalone Laravel project workspace_ai_web.
3. Implement WorkspaceAiAgentClient.
4. Test Laravel → Agent với User/Organization context.
5. Test Calendar read.
6. Test Calendar write + confirmation.
7. Test authorization denied.
8. Test OAuth required.
9. Sau khi API boundary ổn định mới xây Chat UI.

**API CONTRACT V1 — LOCKED FOR IMPLEMENTATION.**

## Laravel Web Project — Repository chính thức

Laravel Web là project/repository độc lập:

**Repository:** `ananh888846/workspace_ai_agent_web`

**GitHub:** https://github.com/ananh888846/workspace_ai_agent_web

Agent repository này không chứa source code Laravel.

Mọi implementation phía Laravel của contract này phải được thực hiện trong repository trên.

Topology:

```
workspace_ai_agent
        ↑
        │ HTTPS API
        ↓
workspace_ai_agent_web
```

Tên project/repository Laravel được chốt chính thức là `workspace_ai_agent_web`.


## 38. Implementation Status — Agent API Boundary

Ngày 2026-09-23:

Đã implement trong `workspace_ai_agent`:

- Server-to-server Bearer authentication bằng `AGENT_SERVER_TOKEN`.
- Kiểm tra `Authorization: Bearer ...` bằng so sánh constant-time.
- Bắt buộc `X-Request-Id` và kiểm tra UUID.
- Bắt buộc `X-User-Id` và `X-Organization-Id` sau khi server authentication thành công.
- Tạo execution context từ trusted server request; token không được đưa vào context.
- Success response của `/api/v1/agent/chat` có `request_id`.
- Structured HTTP error envelope cho HTTP exception, validation error và internal error.
- Không trả exception detail nguyên bản đối với lỗi nội bộ.
- Thêm unit/API boundary tests cho authentication và structured response/error.

Chưa coi là runtime-verified trong môi trường deployment thật. Cần chạy test suite sau khi pull code.

Còn lại trong contract target:

- Idempotency-Key persistence/handling cho side-effect.
- Retry policy thực tế ở Laravel client.
- Runtime verification end-to-end Laravel → Agent trên môi trường triển khai.
