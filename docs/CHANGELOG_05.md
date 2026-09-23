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