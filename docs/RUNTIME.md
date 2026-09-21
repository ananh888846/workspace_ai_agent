# Workspace AI Agent — RUNTIME CONTRACT V2.1

## 1. Mục tiêu

Runtime verification là gate bắt buộc trước khi mở rộng provider, device hoặc agent. Test phải kiểm tra hành vi thật, không chỉ response.

## 2. Startup

Kiểm tra application startup, database, configuration, dependency health, logging và request_id.

## 3. Identity / Organization

Kiểm tra authenticated user, session, device metadata, organization membership và chống tự đổi user_id/organization_id bằng request payload.

Test: User A thuộc Organization A → resource A ALLOW; user không thuộc Organization A → resource A DENY.

Kiểm tra authenticated user, session, device metadata và chống tự đổi user_id.

## 4. Account

Kiểm tra multi-account, AccountResolver, account hint, credential timing và không log token.

## 5. Authorization

Phải có cả ALLOW và DENY.

Authorization phải kiểm tra organization + capability + account + resource + package khi các scope tương ứng tồn tại.

~~~text
User B → Calendar A → ALLOW → Google API được gọi
User C → Calendar A → DENY  → Google API KHÔNG được gọi
~~~

## 6. Resource hierarchy

Kiểm tra parent/child cùng organization, không truy cập resource xuyên tenant và device/resource binding hợp lệ.

## 7. Data Package

Kiểm tra owner, version, resource membership, grant, expiry/revoke, thiếu grant và không chứa credential.

## 8. Device / Observation / Event

Kiểm tra device thuộc organization, observation đúng device, event giữ organization/resource/source context và không tạo event chéo organization.

## 9. Activity Session / Activity

Kiểm tra lifecycle start/end, duplicate event, missing end, unknown user và resource không hợp lệ.

## 10. Task / Work Order

Kiểm tra task thuộc organization, assigned_user/resource hợp lệ và activity/session có thể đối soát với task.

## 11. Capability / Tool

Kiểm tra routing, requires_account, tool resolution, provider adapter, contract và protected-tool denial.

## 12. Provider

Google phase đầu:
1. Drive search/read
2. Gmail search/read
3. Calendar
4. nhiều Google Account
5. account delegation

## 13. Agent-to-Agent communication

Kiểm tra permitted call → ALLOW, unpermitted/expired/wrong-organization call → DENY; agent message không tự cấp quyền và agent task phải trace tới request/agent run.

## 14. Knowledge

Kiểm tra ingestion, document/chunk, embedding, Qdrant indexing và authorized retrieval. Không được retrieval chéo dữ liệu không có quyền.

## 15. Anomaly Detection

Kiểm tra anomaly có evidence hợp lệ, evidence truy ngược được source event/activity/task/device/resource, evidence khác organization bị invalid và detection_method/confidence được lưu.

Không biến anomaly thành kết luận gian lận nếu evidence chỉ biểu thị bất thường.

## 16. Audit / Trace

Protected operation phải trace được:

~~~text
request_id
 ↓
organization
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

## 17. Runtime gate

Không mở phase tiếp theo nếu Core chưa đạt startup, identity, organization isolation, account, authorization, resource hierarchy, data package, device boundary, activity/session, task reconciliation, agent communication permission, anomaly evidence, tool và audit.

## 18. Performance

Chỉ thêm cache, queue, worker, event bus hoặc distributed processing sau benchmark runtime thực tế.

## 19. V2.1 acceptance gate

~~~text
Organization isolation
Resource hierarchy
Device → Resource
Activity Session lifecycle
Task → Activity reconciliation
Agent → Agent permission
Anomaly → Evidence trace
Authorization DENY → no credential / no tool / no provider side effect
Audit trace đầy đủ
~~~
