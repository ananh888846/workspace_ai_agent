# CHANGELOG_06.md

> Changelog tiếp theo của `docs/CHANGELOG_05.md`.
>
> Quy tắc: chỉ ghi PASS khi đã có runtime verification. Các mục implement nhưng chưa chạy runtime phải ghi rõ trạng thái.

## 2026-09-23 16:xx +07:00 — Implement/Verify Agent API Boundary V1

### Đã implement

- Thêm `app/api/security.py`.
  - Server-to-server Bearer authentication.
  - Đọc `AGENT_SERVER_TOKEN` từ environment.
  - So sánh token bằng `hmac.compare_digest`.
  - Bắt buộc `X-Request-Id`.
  - Kiểm tra `X-Request-Id` là UUID.
  - Bắt buộc `X-User-Id` và `X-Organization-Id`.
  - Chỉ tạo trusted identity context sau khi server authentication thành công.
  - Không đưa server token vào AgentContext.

- Thêm `app/api/errors.py`.
  - Structured error envelope: `status`, `error.code`, `error.message`, `request_id`.
  - Chuẩn hóa HTTP 400/401/403/404/409/422/429/502/503/504.
  - Validation error trả 422 theo contract.
  - Internal error không trả exception detail ra client.

- Cập nhật `app/main.py`.
  - `POST /api/v1/agent/chat` dùng server authentication dependency.
  - Context truyền `request_id`, `user_id`, `organization_id`.
  - Success response có `request_id`.
  - Không cho request chưa authenticate đi vào Agent Runtime.

- Cập nhật Calendar response để giữ `request_id` xuyên execution boundary.

- Cập nhật `.env.example` với `AGENT_SERVER_TOKEN=`.

- Thêm tests:
  - `tests/test_api_security.py`
  - `tests/test_agent_api_boundary.py`

### Security boundary đã chốt

```text
Browser
   ↓
Laravel authenticated session
   ↓
Laravel server
   ↓ Authorization: Bearer <server token>
   + X-Request-Id
   + X-User-Id
   + X-Organization-Id
   ↓
Workspace AI Agent
   ↓
AgentContext
   ↓
Classification → Routing → Authorization → Credential → Provider
```

Browser không được biết hoặc gửi Agent server token.

### Trạng thái verification

**IMPLEMENTED — RUNTIME VERIFICATION PENDING**

Đã tạo test để kiểm tra boundary, nhưng chưa ghi PASS runtime vì chưa chạy test suite trên environment thực tế trong bước này.

### Chưa triển khai

- Idempotency-Key persistence/handling.
- Retry policy thực tế ở Laravel client.
- End-to-end test Laravel `workspace_ai_agent_web` → Agent.
- Production secret manager/firewall/VPN configuration.

### Git scope

- Chỉ thay đổi repository `ananh888846/workspace_ai_agent`.
- Không đặt source Laravel vào Agent repository.
- Laravel Web chính thức vẫn là `ananh888846/workspace_ai_agent_web`.
