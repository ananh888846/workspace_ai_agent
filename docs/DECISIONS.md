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
