# Workspace AI Agent — CORE CONTRACTS V2.1

> Contract blueprint cho Core. Chưa phải implementation.

## 1. AgentContext
Runtime context tối thiểu:
~~~text
request_id
organization_id
user_id
session_id
device_id
capability
action
target_account
target_resource
target_package
metadata
~~~
`organization_id` là tenant context để kiểm tra isolation. AgentContext không phải permission source và không chứa secret.

Không cho client tùy ý đổi `organization_id` để vượt tenant boundary.

## 2. OrganizationContextResolver

- Resolve organization từ authenticated membership, device binding hoặc trusted request boundary.
- Kiểm tra membership hợp lệ.
- Không thay thế AuthorizationService.

## 3. AuthenticationService
Input: request/session credentials.
Output: authenticated user identity và session context.
Không quyết định resource authorization.

## 4. AuthorizationService
Input: AgentContext, capability/action, candidate account, target resource, target package.

Điều kiện bắt buộc: Organization Membership AND Capability Permission AND Account Access (nếu áp dụng) AND Resource Access AND Package Access (nếu áp dụng).
Output: ALLOW hoặc DENY cùng reason/code.
Điều kiện bắt buộc: Capability Permission AND Account Access AND Resource Access AND Package Access nếu áp dụng.

## 5. AccountResolver
- Tìm candidate external account.
- Xử lý multi-account.
- Áp dụng default-account policy hoặc yêu cầu user chọn.
- Không lấy secret trước Authorization.
- Không tự quyết định permission.

## 6. CredentialResolver
Chỉ nhận account đã được authorize và trả credential context ngắn hạn cho provider call.
Credential không được ghi vào AgentContext, prompt, log hoặc audit.

## 7. ResourceAccessChecker
Kiểm tra resource cụ thể theo organization, user, resource và action. Resource hierarchy không được kế thừa quyền xuyên organization. Resource permission không thay thế capability permission.

## 8. DataPackageResolver
Resolve package/version/resources và kiểm tra package grant. Package grant không bypass resource/account/capability authorization.

## 9. CapabilityRegistry
Đăng ký capability business-level như `drive.read`, `drive.write`, `gmail.read`, `calendar.read`, `calendar.write`, `home.control`. Registry không cấp quyền cho User.

## 10. ToolResolver
Chọn implementation phù hợp với capability/provider/resource/action/requires_account. Không bypass Authorization.

## 11. ProviderAdapter
Chuẩn hóa account mapping, credential mapping, resource mapping, API client và provider error/rate-limit policy. Không tự cấp authorization.

## 12. Agent-to-Agent communication

~~~text
Agent A → Agent Task / Agent Message → Agent Permission → AuthorizationService → Agent B
~~~

Agent message là transport/trace; agent task là đơn vị công việc có lifecycle; permission mới quyết định được gọi hay không.

## 13. Activity Session / Task contract

Activity Session biểu diễn một khoảng hoạt động có start/end. Task/Work Order biểu diễn công việc được giao. Activity không tự chứng minh task hoàn thành nếu thiếu evidence.

## 14. Anomaly contract

~~~text
Observed Facts → Rule / Inference → Anomaly → Anomaly Evidence
~~~

Anomaly phải có evidence truy ngược được về source hợp lệ và không được dùng như kết luận gian lận.

## 15. AuditService
Ghi tối thiểu request_id, organization_id, user_id, device_id, capability, action, account_id, resource_id, package_version_id, result, timestamp. Không ghi secret.

## 16. Request execution contract
~~~text
Request
 ↓ AuthenticationService
 ↓ OrganizationContextResolver
 ↓ AgentContext
 ↓ Route / Capability
 ↓ AccountResolver (nếu cần)
 ↓ AuthorizationService
 ↓ CredentialResolver
 ↓ ToolResolver
 ↓ Tool
 ↓ ProviderAdapter
 ↓ Audit
 ↓ Response
~~~

Nếu Authorization = DENY:
~~~text
CredentialResolver = NOT CALLED
Tool = NOT CALLED
Provider API = NOT CALLED
~~~

## 17. Error categories
- authentication_error
- organization_access_denied
- authorization_denied
- account_not_found
- account_selection_required
- resource_not_found
- package_not_found
- credential_unavailable
- tool_not_found
- provider_error
- validation_error
- internal_error

Không expose secret/provider credential trong error response.

## 18. Contract testing
Phải kiểm tra input validation, organization isolation, authorization boundary, credential boundary, resource hierarchy, tool selection, provider mapping, agent-to-agent permission, activity/task reconciliation, anomaly evidence trace, audit trace và DENY không tạo provider side effect.