# Laravel Web Authentication & Agent Authentication V1

> Trạng thái: **DESIGN / ACCEPTED FOR IMPLEMENTATION**
>
> Mục tiêu: định nghĩa rõ cơ chế đăng nhập của Web Laravel, cách Laravel xác định User/Organization, cách Laravel gọi workspace_ai_agent ở server khác và cách xử lý OAuth tài khoản Google.
>
> Nguyên tắc quan trọng: **đăng nhập Web Laravel**, **xác thực giữa Laravel ↔ Agent** và **OAuth Google account** là ba lớp khác nhau. Không được trộn chúng thành một cơ chế.

---

## 1. Mục tiêu kiến trúc

Laravel là một project độc lập:

```text
Browser
   ↓ HTTPS
Laravel Web Application
   ├── Login / Session
   ├── User
   ├── Organization membership
   ├── Web authorization
   └── WorkspaceAiAgentClient
            ↓ HTTPS
     Workspace AI Agent
            ├── Authentication transport
            ├── AgentContext
            ├── Authorization
            ├── AccountResolver
            ├── CredentialResolver
            └── Capability / Tool / Provider
```

Laravel **không** trở thành một phần của Agent Runtime.

Agent **không** phụ thuộc vào Laravel session/cookie.

Hai project có thể triển khai trên hai server hoàn toàn khác nhau.

## 2. Ba lớp xác thực phải tách biệt

### 2.1 User Login — người dùng đăng nhập Web

Mục đích:
- xác định người đang sử dụng Web;
- tạo Laravel authenticated session;
- bảo vệ các route của Web;
- xác định user_id;
- xác định Organization hiện tại.

```text
Anh An
   ↓
POST /login
   ↓
Laravel Authentication
   ↓
Laravel Session
   ↓
Authenticated User
```

Cookie/session của Laravel **không được gửi sang Agent**.

### 2.2 Laravel → Agent Authentication

Mục đích:
- chứng minh request thật sự đến từ Laravel Web đã được đăng ký;
- chống client giả mạo gọi Agent bằng cách tự đặt X-User-Id;
- bảo vệ API Agent khi hai server tách biệt.

Không được xem:

```text
X-User-Id = authentication
```

X-User-Id chỉ là **identity context** sau khi transport request đã được xác thực.

### 2.3 Google OAuth — kết nối tài khoản Google

Google OAuth dùng để cấp quyền cho **external account**.

Ví dụ một User có nhiều Gmail:

```text
User A
 ├── Google Account 1
 ├── Google Account 2
 └── Google Account 3
```

Google OAuth **không phải** login session của Laravel và cũng không phải credential để Laravel tự gọi Google Calendar/Gmail thay Agent.

## 3. Luồng đăng nhập Laravel

### 3.1 Login cơ bản

```text
Browser
  │
  │ GET /login
  ▼
Laravel
  │
  │ POST /login
  │ email + password
  ▼
Authentication
  │
  ├── kiểm tra User
  ├── kiểm tra password
  ├── kiểm tra trạng thái account
  └── tạo authenticated session
  ▼
Browser
  │
  └── Laravel session cookie
```

## 4. Không cho Browser tự gửi Identity của Agent

Đây là nguyên tắc bảo mật bắt buộc.

Không thiết kế:

```text
Browser
  ↓
POST Agent
  X-User-Id: 123
  X-Organization-Id: 456
```

Vì Browser có thể sửa identity.

Thiết kế đúng:

```text
Browser
  ↓
Laravel
  ↓
Auth::user()
  ↓
Laravel lấy organization hiện tại
  ↓
Laravel tạo Agent request
  ↓
Agent
```

## 5. Request Laravel → Agent

Endpoint chuẩn:

POST /api/v1/agent/chat

Transport: HTTPS.

Headers tối thiểu:

```http
Authorization: Bearer <server-to-server-token>
Content-Type: application/json
X-Request-Id: <uuid>
X-User-Id: <user-id>
X-Organization-Id: <organization-id>
```

| Header | Ý nghĩa | Nguồn |
|---|---|---|
| Authorization | xác thực Laravel với Agent | Laravel server |
| X-Request-Id | trace request | Laravel server |
| X-User-Id | identity của user | Laravel authenticated session |
| X-Organization-Id | tenant hiện tại | Laravel membership/context |

X-User-Id và X-Organization-Id không phải secret. Secret chỉ nằm ở cơ chế server-to-server authentication.

## 6. Server-to-server authentication V1

V1 sử dụng một secret riêng giữa hai server.

Laravel:

```env
WORKSPACE_AI_AGENT_URL=https://ai.example.com
WORKSPACE_AI_AGENT_TOKEN=<long-random-secret>
```

Agent:

```env
AGENT_SERVER_TOKEN=<same-secret>
```

Laravel gửi Authorization Bearer token.

Không được:
- commit token vào Git;
- đưa token vào JavaScript/browser;
- đưa token vào chat message;
- đưa token vào prompt;
- ghi token vào log;
- trả token về API response.

## 7. Khi Laravel và Agent chạy khác server

```text
SERVER A
┌──────────────────────────────┐
│ Laravel Web                  │
│ HTTPS :443                   │
│ Login / Session / Web UI     │
└──────────────┬───────────────┘
               │ HTTPS
               │ server token
               ▼
SERVER B
┌──────────────────────────────┐
│ Workspace AI Agent           │
│ FastAPI                      │
│ /api/v1/agent/chat           │
│ PostgreSQL + Qdrant          │
└──────────────────────────────┘
```

Agent API không nên mở công khai cho toàn Internet nếu không cần. Ưu tiên private network, VPN hoặc firewall allowlist.

Nếu Agent phải public: bắt buộc HTTPS, server token, rate limit, request size limit và audit.

## 8. Không dùng Laravel session cho Agent

Đúng:

```text
Laravel Session
      ↓
Authenticated User
      ↓
Trusted identity context
      ↓
Server-to-server authentication
      ↓
Agent
```

Agent không cần biết Laravel session implementation.

## 9. Agent tạo AgentContext

Sau khi transport authentication thành công:

```text
HTTP Request
   ↓
Authenticate Laravel
   ↓
Validate headers
   ↓
AgentContext
```

Context gồm request_id, user_id, organization_id, session_id, device_id, capability, action, target_account, target_resource, target_package và metadata.

AgentContext chỉ là execution context. **AgentContext không tự cấp quyền.**

## 10. Authorization vẫn do Agent kiểm tra

Không được hiểu:

```text
Laravel authenticated = Agent authorized
```

Đây là hai việc khác nhau.

```text
Laravel
  ↓
User = 123
Organization = 10
  ↓
Agent
  ↓
Capability Permission
  AND Account Access
  AND Resource Access
  AND Package Access nếu áp dụng
  ↓
ALLOW / DENY
```

## 11. Luồng chat hoàn chỉnh

Ví dụ user nhập: “Ngày mai tôi có lịch gì?”

```text
Browser
  ↓
Laravel authenticated session
  ↓
Laravel lấy user_id + organization_id + conversation_id
  ↓
Laravel gọi Agent
  ↓
Agent authenticate Laravel server
  ↓
Agent tạo AgentContext
  ↓
Classification
  ↓
calendar.read
  ↓
AccountResolver
  ↓
Authorization
  ↓
CredentialResolver
  ↓
Google Calendar Tool
  ↓
Google Calendar Provider
  ↓
Result
  ↓
Agent response
  ↓
Laravel render chat
```

Laravel không gọi Google Calendar trực tiếp trong kiến trúc này.

## 12. Conversation

Laravel UI cần giữ conversation_id.

```json
{
  "message": "Ngày mai tôi có lịch gì?",
  "conversation_id": "conv-01"
}
```

Không dùng session ID của Laravel làm conversation ID.

## 13. Organization / Tenant

Một User có thể thuộc nhiều Organization.

Laravel phải xác định Organization hiện tại trước khi gọi Agent.

Agent vẫn phải kiểm tra tenant boundary theo authorization model của Agent.

Không cho user chọn một Organization mà họ không thuộc về.

## 14. Google OAuth — nhiều tài khoản Google

Google OAuth phải gắn với User + Organization + External Account.

```text
User 100
 ├── Gmail personal
 ├── Gmail company
 └── Google Workspace account
```

Khi user chọn dùng tài khoản công ty để đọc lịch, Agent phải resolve đúng account. Không để LLM tự đoán account.

Nếu có nhiều account mà request không chỉ rõ: dùng policy default hoặc yêu cầu user chọn account.

## 15. Google OAuth flow

```text
Browser
   ↓
Laravel
   ↓
Agent OAuth Start
   ↓
Google Authorization
   ↓
Google Callback
   ↓
Agent OAuth Handler
   ↓
Exchange Authorization Code
   ↓
Encrypt Credential
   ↓
Store account credential
   ↓
Mark account ready
   ↓
Return safe result
   ↓
Laravel
   ↓
Browser
```

OAuth code/token không đi qua chat UI.

Không trả access_token, refresh_token hoặc client_secret cho Browser nếu Agent là nơi quản lý Google integration.

## 16. OAuth State

OAuth state phải khó đoán, có thời hạn, gắn với User, Organization và provider, chống replay và được kiểm tra ở callback.

```text
OAuth Start
   ↓
Create OAuth State
   ├── user_id
   ├── organization_id
   ├── provider
   ├── expires_at
   └── nonce/state binding
   ↓
Google
   ↓
Callback
   ↓
Validate State
   ↓
Exchange Code
```

Không dùng một state cố định cho toàn hệ thống.

## 17. Credential Storage

Credential Google phải được mã hóa trước khi lưu.

```text
Google
   ↓
OAuth Token
   ↓
Encryption Boundary
   ↓
account_credentials
```

Không lưu plaintext token trong PostgreSQL, log, AgentContext, Graph state, prompt, audit event, HTTP response hoặc browser localStorage.

## 18. Login Laravel và Google OAuth không thay thế nhau

Đăng nhập Web:

```text
Email + Password
        ↓
Laravel Session
```

Kết nối Google Calendar:

```text
Authenticated Laravel User
        ↓
Google OAuth
        ↓
External Google Account
```

User có thể đăng nhập Laravel bằng email/password nhưng kết nối nhiều Google accounts.

Google OAuth account không mặc định có nghĩa user đã được cấp quyền vào mọi Organization.

## 19. Logout

Laravel logout chỉ invalidate Web session.

Logout Laravel **không tự động xóa Google OAuth credential**.

Disconnect Google Account là một flow riêng và phải đi qua authorization.

## 20. Session Security V1

Laravel Web phải:
- HTTPS production;
- secure cookie;
- HttpOnly cookie;
- SameSite policy phù hợp;
- session rotation sau login;
- CSRF protection cho state-changing browser requests;
- password hashing bằng cơ chế chuẩn của Laravel;
- rate limit login;
- không log password.

Không tự xây password hashing hoặc session mechanism.

## 21. Agent API Security V1

Agent API phải kiểm tra server-to-server token, validate identity/context, validate request body, request ID, timeout, rate limit và audit.

Agent không được tin identity do browser gửi trực tiếp.

Authorization denied phải xảy ra trước provider call.

## 22. Error model

| Tình huống | Ý nghĩa |
|---|---|
| 401 | Server-to-server authentication thất bại |
| 403 | User/org không được phép |
| 404 | Resource không tồn tại hoặc không được expose |
| 409 | Conflict / confirmation / state conflict |
| 422 | Request hợp lệ về HTTP nhưng dữ liệu/command không hợp lệ |
| 429 | Rate limit |
| 502 | Laravel không nhận được response hợp lệ từ Agent/provider boundary |
| 504 | Agent timeout |

Agent nên trả structured error.

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

Không trả stack trace, OAuth secret, access token, refresh token, filesystem path hoặc server environment cho Browser.

## 23. Request ID và Audit

Laravel tạo X-Request-Id. Agent giữ request ID xuyên suốt Agent Run, Tool Run và provider call.

```text
Laravel → Agent → Agent Run → Tool Run → Provider
                 req-abc xuyên suốt
```

## 24. Timeout và retry

Laravel không được retry vô hạn.

Chỉ retry các lỗi được xác định là retryable.

Không retry mù thao tác có side effect như tạo Calendar event, gửi Gmail hoặc điều khiển thiết bị.

## 25. Idempotency cho side effect

Khi Laravel gửi command có side effect, về sau nên hỗ trợ:

```http
Idempotency-Key: <uuid>
```

Điều này giúp retry sau network timeout không tạo side effect trùng.

## 26. Cấu hình Laravel

```env
WORKSPACE_AI_AGENT_URL=https://ai.example.com
WORKSPACE_AI_AGENT_TOKEN=...
WORKSPACE_AI_AGENT_TIMEOUT=30
WORKSPACE_AI_AGENT_CONNECT_TIMEOUT=5
```

Không đặt WORKSPACE_AI_AGENT_TOKEN trong frontend JavaScript.

## 27. Cấu hình Agent

```env
AGENT_SERVER_TOKEN=...
```

Production token phải được quản lý bằng secret manager hoặc secret mechanism của môi trường triển khai khi hệ thống trưởng thành.

## 28. Development

Local có thể chạy Laravel tại 127.0.0.1:8001 và Agent tại 127.0.0.1:8000.

Laravel:

```env
WORKSPACE_AI_AGENT_URL=http://127.0.0.1:8000
```

Agent token vẫn phải được dùng để kiểm tra đúng flow production.

## 29. Production domain đề xuất

```text
https://app.example.com
        ↓
Laravel Web

https://ai.example.com
        ↓
Workspace AI Agent
```

Browser chỉ giao tiếp với Web Laravel. Laravel server giao tiếp với Agent.

## 30. Kiến trúc project Laravel

Project riêng, ví dụ:

```text
workspace_ai_web/
├── app/
│   ├── Http/
│   ├── Models/
│   ├── Services/
│   │   └── AiAgent/
│   │       └── WorkspaceAiAgentClient.php
│   └── ...
├── config/
│   └── services.php
├── resources/
│   └── views/
│       └── chat/
├── routes/
├── tests/
└── ...
```

Agent project giữ độc lập tại workspace_ai_agent.

## 31. Ownership

### Laravel sở hữu
- Web UI;
- Web login;
- Web session;
- user-facing organization selection;
- chat UI;
- browser security;
- presentation;
- gọi Agent API.

### Agent sở hữu
- AgentContext;
- capability routing;
- authorization nghiệp vụ của Agent;
- account resolver;
- credential resolver;
- tool;
- provider;
- Google integration;
- Knowledge;
- Agent memory;
- Agent audit/execution.

## 32. Quy tắc không trộn boundary

Không để Laravel gọi Google Calendar trực tiếp nếu capability đã thuộc Agent.

Không để Browser gọi Agent bằng user token.

Không để Agent truy cập Laravel database trực tiếp.

Không để Laravel truy cập Agent database trực tiếp.

Hai hệ thống giao tiếp qua API contract.

## 33. Quy tắc bảo mật quan trọng nhất

```text
Browser không được quyết định identity của Agent.
Laravel không được tự cấp quyền Agent.
Agent không được tin mù identity header.
LLM không được quyết định permission.
OAuth token không được đưa ra browser.
Credential không được đưa vào Graph state/prompt/log.
Provider chỉ được gọi sau Authorization ALLOW.
```

## 34. Acceptance Criteria V1

- [ ] User login thành công trên Laravel.
- [ ] Logout invalidate session.
- [ ] Browser không có Agent server token.
- [ ] Laravel lấy user từ authenticated session.
- [ ] Laravel xác định organization hợp lệ.
- [ ] Laravel gọi Agent qua HTTPS ở production.
- [ ] Agent xác thực server-to-server token.
- [ ] Agent tạo AgentContext.
- [ ] Agent không tin X-User-Id từ browser trực tiếp.
- [ ] Authorization được thực hiện ở Agent.
- [ ] Google OAuth không trả token cho browser.
- [ ] Credential được mã hóa trước khi lưu.
- [ ] Token không xuất hiện trong log.
- [ ] Request ID chạy xuyên Laravel → Agent.
- [ ] Timeout được kiểm soát.
- [ ] Side-effect không retry mù.
- [ ] Authorization denied không gọi provider.

## 35. Quan hệ với ARCHITECTURE.md

Tài liệu này là tài liệu triển khai riêng cho boundary Laravel Web ↔ Agent API.

Nguyên tắc kiến trúc tổng thể trong docs/ARCHITECTURE.md vẫn là nguồn tham chiếu cao hơn.

Nếu phát sinh mâu thuẫn:
1. kiểm tra ARCHITECTURE;
2. tạo Decision Log;
3. cập nhật tài liệu;
4. sau đó mới sửa code.

## 36. Trạng thái chốt

**AUTHENTICATION V1 — DESIGN LOCK**

Đã chốt:
- Laravel là project riêng;
- Laravel có login/session riêng;
- Agent không dùng Laravel session;
- Laravel → Agent dùng server-to-server authentication;
- X-User-Id / X-Organization-Id là trusted context do Laravel tạo sau authentication;
- Agent vẫn tự thực hiện authorization;
- Google OAuth là external-account integration riêng;
- User có thể có nhiều Google accounts;
- Google credential thuộc Agent integration boundary;
- Browser không nhận Agent server token hoặc Google refresh token;
- hai project giao tiếp bằng HTTP API contract;
- có thể triển khai Laravel và Agent trên hai server khác nhau.

**Chưa chốt implementation framework cụ thể cho Laravel authentication package/UI.** Việc chọn package chỉ thực hiện khi bắt đầu tạo project Laravel riêng.