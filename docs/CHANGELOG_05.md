# CHANGELOG_05.md

> Changelog tiếp theo của `docs/CHANGELOG_04.md`.
>
> Quy tắc: chỉ ghi trạng thái đã được triển khai/kiểm tra; không ghi PASS nếu chưa có runtime verification.

## 2026-09-23 16:xx +07:00 — Chốt Authentication Architecture cho Laravel Web ↔ Workspace AI Agent

- Thêm `docs/AUTHENTICATION_LARAVEL_AGENT_V1.md`.
- Chốt Laravel Web là project độc lập, không đặt Laravel vào repository `workspace_ai_agent`.
- Chốt ba lớp cần tách biệt:
  - User Login / Laravel Session;
  - Server-to-server Authentication giữa Laravel và Agent;
  - Google OAuth cho external Google accounts.
- Chốt Browser không được tự gửi hoặc tự quyết định `X-User-Id` / `X-Organization-Id` để gọi Agent.
- Laravel lấy User/Organization từ authenticated session và tạo trusted Agent request.
- Agent xác thực server-to-server token trước khi tạo AgentContext.
- `X-User-Id` và `X-Organization-Id` chỉ là identity/tenant context, không thay thế Authorization.
- Agent tiếp tục tự kiểm tra Capability Permission, Account Access, Resource Access và Package Access theo kiến trúc hiện hành.
- Chốt Google OAuth thuộc Agent integration boundary; một User có thể có nhiều Google accounts.
- OAuth state phải gắn với user/organization/provider, có thời hạn và chống replay.
- Google credential phải được mã hóa trước khi lưu và không được đưa vào browser, prompt, Graph state hoặc log.
- Chốt Request ID chạy xuyên Laravel → Agent → Agent Run → Tool Run → Provider.
- Chốt timeout, retry policy và yêu cầu idempotency cho side-effect về sau.
- Chốt production topology có thể chạy Laravel và Agent trên hai server khác nhau.
- Không thay đổi database schema.
- Không thay đổi OAuth scope.
- Không thay đổi Docker topology.
- Chưa triển khai code Laravel; đây là architecture/design lock trước khi tạo project Laravel riêng.

### Git commit

- `5ca33288b2d21f61f453a77310034f33c59ab643` — `docs: add Laravel Agent authentication architecture v1`

### Next phase

- Tạo project Laravel riêng.
- Implement Laravel login/session.
- Implement `WorkspaceAiAgentClient` theo API contract.
- Sau đó mới triển khai Chat UI và Google Account connection flow.
## 2026-09-23 — Chốt API Contract Laravel Web ↔ Agent V1

- Thêm `docs/API_CONTRACT_LARAVEL_AGENT_V1.md`.
- Chốt endpoint `POST /api/v1/agent/chat` là HTTP boundary chuẩn giữa Laravel Web và Workspace AI Agent.
- Chốt server-to-server Bearer authentication V1.
- Chốt request headers:
  - `Authorization`;
  - `Content-Type`;
  - `X-Request-Id`;
  - `X-User-Id`;
  - `X-Organization-Id`.
- Chốt core request fields:
  - `message`;
  - `conversation_id`;
  - `account_hint`;
  - `capability`;
  - `action`;
  - `target_resource`.
- Chốt Calendar V1 extension fields hiện có.
- Chốt capability/action contract cho Calendar read/write/schedule/free_busy.
- Chốt execution order: classify → route → account → authorization → credential → provider.
- Chốt provider không được gọi nếu Authorization deny hoặc credential chưa ready.
- Chốt execution envelope và `provider_called`.
- Chốt OAuth-required state không được gọi provider.
- Chốt structured error/status contract: 400/401/403/404/409/422/429/502/504.
- Chốt Request ID xuyên Laravel → Agent → execution boundary.
- Chốt timeout, retry và Idempotency-Key cho side-effect.
- Chốt backward-compatibility rules cho API V1.
- Ghi rõ các mục là contract target nhưng chưa được coi là runtime-verified:
  - response `request_id`;
  - server-to-server authentication middleware/dependency;
  - structured HTTP error envelope;
  - Idempotency-Key persistence/handling;
  - timeout/retry policy trong Laravel client.
- Không thay đổi database schema.
- Không tạo Laravel project trong repository Agent.
- Không thay đổi Google OAuth scope.

## 2026-09-23 — Chốt repository Laravel Web

- Chốt repository Laravel Web chính thức: `ananh888846/workspace_ai_agent_web`.
- GitHub: https://github.com/ananh888846/workspace_ai_agent_web
- Không đặt source Laravel trong repository `workspace_ai_agent`.
- `workspace_ai_agent` chỉ cung cấp Agent/API boundary.
- `workspace_ai_agent_web` là nơi triển khai Laravel Client, login/session và Chat UI sau khi Agent API boundary được verify.
