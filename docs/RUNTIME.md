# Workspace AI Agent — RUNTIME CONTRACT V2

## 1. Mục tiêu

Runtime verification là gate bắt buộc trước khi mở rộng provider, device hoặc agent. Test phải kiểm tra hành vi thật, không chỉ response.

## 2. Startup

Kiểm tra application startup, database, configuration, dependency health, logging và request_id.

## 3. Identity

Kiểm tra authenticated user, session, device metadata và chống tự đổi user_id.

## 4. Account

Kiểm tra multi-account, AccountResolver, account hint, credential timing và không log token.

## 5. Authorization

Phải có cả ALLOW và DENY.

~~~text
User B → Calendar A → ALLOW → Google API được gọi
User C → Calendar A → DENY  → Google API KHÔNG được gọi
~~~

## 6. Data Package

Kiểm tra owner, version, resource membership, grant, expiry/revoke, thiếu grant và không chứa credential.

## 7. Capability / Tool

Kiểm tra routing, requires_account, tool resolution, provider adapter, contract và protected-tool denial.

## 8. Provider

Google phase đầu:
1. Drive search/read
2. Gmail search/read
3. Calendar
4. nhiều Google Account
5. account delegation

## 9. Knowledge

Kiểm tra ingestion, document/chunk, embedding, Qdrant indexing và authorized retrieval. Không được retrieval chéo dữ liệu không có quyền.

## 10. Audit / Trace

Protected operation phải trace được:

~~~text
request_id
 ↓
agent_run
 ↓
tool_run
 ↓
account
 ↓
resource/package
 ↓
result
~~~

## 11. Runtime gate

Không mở phase tiếp theo nếu Core chưa đạt startup, identity, account, authorization, data package, tool và audit.

## 12. Performance

Chỉ thêm cache, queue, worker, event bus hoặc distributed processing sau benchmark runtime thực tế.
