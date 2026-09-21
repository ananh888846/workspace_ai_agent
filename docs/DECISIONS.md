# Workspace AI Agent — ARCHITECTURE DECISIONS V2

> Decision Log là lịch sử quyết định kiến trúc. Không tự ý thay đổi decision đã chốt mà không cập nhật tài liệu.

## Decision 001 — User Account Model
**Status:** Accepted  
user_accounts là mô hình external account chuẩn; một user có nhiều account.

## Decision 002 — Account ≠ Permission
**Status:** Accepted  
Account xác định nguồn tài khoản; Authorization xác định quyền.

## Decision 003 — Account là dependency của Capability
**Status:** Accepted  
Capability không cần account hoạt động bình thường; capability cần account mới gọi AccountResolver.

## Decision 004 — Authorization thuộc Application
**Status:** Accepted  
Identity xác định user; Application Authorization quyết định quyền.

## Decision 005 — Resource Access
**Status:** Accepted  
Resource access được kiểm tra theo request; ownership không đồng nghĩa access.

## Decision 006 — Data Package
**Status:** Accepted  
Data Package là access definition có version và có thể gom nhiều resource.

## Decision 007 — Data Package không chứa Credential
**Status:** Accepted  
Package không chứa OAuth token, API key hoặc device secret.

## Decision 008 — Credential sau Authorization
**Status:** Accepted  
Candidate account có thể được xác định trước authorization; secret chỉ được lấy sau ALLOW.

## Decision 009 — Conversation / Memory / Knowledge / Data Package
**Status:** Accepted  
Bốn domain tách biệt; retrieval không tự động thành memory.

## Decision 010 — Device ≠ User
**Status:** Accepted  
Device có identity/credential/capability riêng.

## Decision 011 — Observation → Event → Activity
**Status:** Accepted  
AI inference không mặc định là fact.

## Decision 012 — LangChain + CrewAI
**Status:** Accepted  
Framework cung cấp primitives/orchestration; không sở hữu authorization.

## Decision 013 — Provider Independence
**Status:** Accepted  
Provider-specific behavior nằm ở Provider/Tool layer.

## Decision 014 — Authorization Precedence
**Status:** Accepted  
Capability Permission AND Account Access AND Resource Access AND Package Access nếu áp dụng = ALLOW. Thiếu/DENY điều kiện bắt buộc = DENY.

## Decision 015 — Runtime Gate
**Status:** Accepted  
Runtime verification là gate trước khi mở rộng phase; phải kiểm tra side effect/provider call khi cần.

## Decision 016 — Documentation is Contract
**Status:** Accepted  
Nếu implementation cần phá kiến trúc, phải cập nhật Decision/Architecture/Database/Changelog.

## Decision 017 — Core Database vs Domain Extensions
**Status:** Accepted  
Không tạo trước các bảng domain đặc thù; chỉ thêm khi capability tương ứng được duyệt.


## Decision 018 — Database Authorization Integrity
**Status:** Accepted  
Database V2 phải biểu diễn đầy đủ ba liên kết authorization quan trọng: role → permission qua `role_permissions`, account-backed resource → `user_accounts`, và account grant owner → account bằng constraint/transaction phù hợp. Migration order phải tôn trọng mọi FK dependency.


## Decision 019 — Organization Membership ≠ Application Authorization Role
**Status:** Accepted  
`organization_members.member_role` chỉ mô tả vai trò membership trong tenant. Application authorization dùng `roles`, `permissions`, `role_permissions`, cùng account/resource/package checks. Membership không tự bypass authorization.

## Decision 020 — Database Schema Source of Truth
**Status:** Accepted  
`docs/DATABASE_V2_DETAILED.md` là source of truth cho column, type, nullability, default, FK, UNIQUE, CHECK, INDEX, delete policy và migration order. `DATABASE.md` chỉ là overview; `ERD_V2.md` là relationship view.

## Decision 021 — Authorized Vector Retrieval
**Status:** Accepted  
Knowledge retrieval phải áp dụng authorization context trước/trong Qdrant retrieval. Không retrieve toàn bộ vector store rồi mới lọc quyền.

## Decision 022 — Webhook Does Not Perform Full Ingestion
**Status:** Accepted  
Webhook chỉ xác thực và ghi nhận sync event; worker thực hiện fetch/normalize/version/chunk/embed/index. Không chạy full ingestion trong HTTP webhook request.


## Decision 023 — Organization as Tenant Boundary
**Status:** Accepted  
Organization là tenant/workspace boundary. User có thể thuộc nhiều Organization; membership xác định tenant eligibility nhưng không thay thế application authorization. Resource/device/activity/task/agent-communication/anomaly entities có tenant scope phải được database và runtime enforce cùng organization.

## Decision 024 — Activity Session and Task Separation
**Status:** Accepted  
Task/Work Order là declared/assigned intent. Observation/Event/Activity Session/Activity là recorded/observed state. Activity không tự chứng minh Task hoàn thành nếu thiếu evidence.

## Decision 025 — Agent-to-Agent Same-Organization Delegation
**Status:** Accepted  
Agent Message và Agent Task là transport/work state; Agent Permission mới quyết định delegation. V2.1 chỉ cho Agent-to-Agent delegation trong cùng Organization. Agent B vẫn chịu user/resource/capability authorization.

## Decision 026 — Evidence-Based Anomaly
**Status:** Accepted  
Anomaly là inference về sai lệch dựa trên evidence, không phải kết luận fraud. Mỗi anomaly phải truy ngược được về source facts/events/activities/tasks/devices/resources trong cùng Organization.


## Decision 027 — Account Grant and Data Package Tenant Scope
**Status:** Accepted  
`account_grants` và Data Package là tenant-scoped trong V2.1. Account grant phải có `organization_id` và owner/grantee cùng là member của organization. `data_packages`, versions, package resources và package grants mang cùng `organization_id`; package không được chứa resource hoặc cấp grant ra ngoài organization. `resources.organization_id` và `devices.organization_id` là bắt buộc.


## Decision 028 — CHANGELOG Must Link Changed/Added Files
**Status:** Accepted  
Mỗi entry trong `docs/CHANGELOG.md` khi ghi nhận file được thêm hoặc thay đổi phải gắn Markdown link trực tiếp tới file trong repository. Quy tắc này áp dụng cho mọi thay đổi documentation/code được ghi vào CHANGELOG, để từ changelog có thể mở thẳng file liên quan. Không ghi tên file dạng plain text nếu file có thể được link nội bộ.
