# Workspace AI Agent — CORE CONTRACTS V2

> Contract blueprint cho Core. Chưa phải implementation.

## 1. AgentContext
Runtime context tối thiểu:
~~~text
request_id
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
AgentContext không phải permission source và không chứa secret.

## 2. AuthenticationService
Input: request/session credentials.
Output: authenticated user identity và session context.
Không quyết định resource authorization.

## 3. AuthorizationService
Input: AgentContext, capability/action, candidate account, target resource, target package.
Output: ALLOW hoặc DENY cùng reason/code.
Điều kiện bắt buộc: Capability Permission AND Account Access AND Resource Access AND Package Access nếu áp dụng.

## 4. AccountResolver
- Tìm candidate external account.
- Xử lý multi-account.
- Áp dụng default-account policy hoặc yêu cầu user chọn.
- Không lấy secret trước Authorization.
- Không tự quyết định permission.

## 5. CredentialResolver
Chỉ nhận account đã được authorize và trả credential context ngắn hạn cho provider call.
Credential không được ghi vào AgentContext, prompt, log hoặc audit.

## 6. ResourceAccessChecker
Kiểm tra resource cụ thể theo user, resource và action. Resource permission không thay thế capability permission.

## 7. DataPackageResolver
Resolve package/version/resources và kiểm tra package grant. Package grant không bypass resource/account/capability authorization.

## 8. CapabilityRegistry
Đăng ký capability business-level như `drive.read`, `drive.write`, `gmail.read`, `calendar.read`, `calendar.write`, `home.control`. Registry không cấp quyền cho User.

## 9. ToolResolver
Chọn implementation phù hợp với capability/provider/resource/action/requires_account. Không bypass Authorization.

## 10. ProviderAdapter
Chuẩn hóa account mapping, credential mapping, resource mapping, API client và provider error/rate-limit policy. Không tự cấp authorization.

## 11. AuditService
Ghi tối thiểu request_id, user_id, device_id, capability, action, account_id, resource_id, package_version_id, result, timestamp. Không ghi secret.

## 12. Request execution contract
~~~text
Request
 ↓ AuthenticationService
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

## 13. Error categories
- authentication_error
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

## 14. Contract testing
Phải kiểm tra input validation, authorization boundary, credential boundary, tool selection, provider mapping, audit trace và DENY không tạo provider side effect.