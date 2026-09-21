# Workspace AI Agent — ARCHITECTURE V2 FINAL

> Blueprint kiến trúc chính thức. Đây là nguồn tham chiếu trước khi viết code.

## 1. Quy tắc bất biến

1. Identity xác định ai; Authorization quyết định được làm gì.
2. Account xác định nguồn tài khoản; Account Grant xác định ai được dùng account.
3. Capability mô tả khả năng; Tool là implementation.
4. Agent không truy cập trực tiếp provider API, SQL hoặc Qdrant nếu bỏ qua Application/Authorization.
5. LLM không quyết định identity, account hoặc permission.
6. Device không phải User.
7. Conversation, Memory, Knowledge, Observation, Event, Activity và Data Package là các domain riêng.
8. Credential chỉ được lấy sau khi Authorization ALLOW.
9. Provider-specific logic nằm trong Provider/Tool layer.
10. Muốn đổi kiến trúc phải cập nhật Decision Log.

## 2. V2.1 — Tenant, Resource, Session, Task và Multi-Agent

V2.1 bổ sung các domain nền tảng mà không thay đổi nguyên tắc Authorization V2.

### 2.1 Organization / Tenant
Organization là boundary của workspace/domain. Một User có thể là member của nhiều Organization.

`organization_members.member_role` chỉ là vai trò membership trong tenant (owner/admin/member/guest). Nó không thay thế `roles`, `permissions` và `role_permissions` của application authorization. Membership không tự cấp quyền đọc/ghi resource hoặc dùng external account.

### 2.2 Resource hierarchy
Resource có thể có quan hệ cha/con. Hierarchy chỉ mô tả cấu trúc, không tự cấp quyền.

### 2.3 Device ↔ Resource ↔ Organization
Device thuộc một Organization và có thể gắn với một Resource cụ thể. Device identity vẫn độc lập với User.

### 2.4 Activity Session
Activity Session gom các Event/Activity liên quan thành một phiên có start/end/duration/status/confidence.

### 2.5 Task / Work Order
Task biểu diễn công việc được giao hoặc yêu cầu nghiệp vụ, có assignee, resource, trạng thái và thời gian. Activity được đối soát với Task để phát hiện mismatch.

### 2.6 Agent-to-Agent Communication
Agent có thể giao task/message cho Agent khác nhưng không bypass AgentContext, Authorization, ToolResolver hoặc Audit.

### 2.7 Anomaly Detection
Anomaly là kết quả phát hiện sai lệch từ facts/events/activities/tasks; không mặc định là kết luận "fraud".

### 2.8 Execution boundary

```text
LLM / Agent
  ↓ intent / plan
Application
  ↓ authorization
Capability
  ↓
Tool
  ↓
Provider
```

Không có đường đi `LLM → Tool` hoặc `LLM → Credential`.

### 2.9 Nguyên tắc V2.1
- Organization là tenant boundary; không dùng User làm tenant thay thế.
- Resource hierarchy không bypass authorization.
- Device không đại diện cho User.
- Activity Session lưu lifecycle của một phiên; Activity vẫn là domain summary.
- Task là declared/assigned intent; Activity là observed/recorded result.
- Anomaly phải có evidence và detection method.
- Agent-to-Agent message/task phải trace được.
- LLM không tự quyết định authorization hoặc kết luận anomaly cuối cùng.

## 3. Request lifecycle

~~~text
Request
 ↓
Authentication
 ↓
AgentContext
 ↓
Route / Capability
 ↓
Resolve candidate Account nếu cần
 ↓
Authorization
 ├── Capability permission
 ├── Account access
 ├── Resource access
 └── Data Package access nếu áp dụng
 ↓
Resolve Credential
 ↓
Resolve Tool
 ↓
Execute
 ↓
Agent Run / Tool Run / Audit
 ↓
Response
~~~

AccountResolver trước Authorization chỉ được xác định candidate account/metadata. Không lấy secret trước ALLOW.

## 4. Authorization

Operation protected chỉ được ALLOW khi mọi điều kiện bắt buộc đạt:

~~~text
Capability Permission
AND Account Access
AND Resource Access
AND Package Access nếu áp dụng
=
ALLOW
~~~

Thiếu hoặc DENY một điều kiện bắt buộc thì không gọi provider/tool.

## 5. AgentContext

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

Context không phải nguồn cấp quyền.

## 6. Account và Capability

~~~text
Capability
 ├── requires_account=false → Tool
 └── requires_account=true
          ↓
      Account Resolver
          ↓
      Authorization
          ↓
          Tool
~~~

Nếu có nhiều account cùng provider mà request không chỉ rõ account, dùng policy default hoặc yêu cầu user chọn. Không để LLM tự đoán.

## 7. Data Package

Data Package là access definition, không phải credential và không bắt buộc là bản sao dữ liệu. Trong V2.1, Package là tenant-scoped; package, version, resource membership và grant không được vượt organization boundary.

~~~text
Data Package
 └── Version
      ├── Resource A
      ├── Resource B
      └── Resource C
             ↓
           Grant → User
~~~

Resource authorization vẫn có hiệu lực.

## 8. Provider

~~~text
Capability
 ↓
Tool Resolver
 ↓
Provider Adapter
 ↓
External API
~~~

Google là provider đầu tiên. Facebook/Meta, Zalo, Telegram, Home Assistant và provider khác triển khai sau Core.

## 9. Device / Event

~~~text
Device
 ↓
Observation
 ↓
Verification / Detection
 ↓
Event
 ↓
Activity
~~~

AI inference không mặc định là fact.

## 10. Knowledge

~~~text
Source
 ↓
Document
 ↓
Normalize
 ↓
Chunk
 ↓
Embedding
 ↓
Qdrant
~~~

SQL giữ metadata, ownership, access, version/checksum và mapping. Retrieval phải chạy trong authorization context.

## 11. LangChain / CrewAI

LangChain cung cấp LLM, retrieval, tool và agent primitives. CrewAI cung cấp multi-agent/task/workflow orchestration. Authorization vẫn thuộc Application Layer.

## 12. Audit

Operation nhạy cảm phải truy được request_id, user, session/device, capability/action, account, resource/package, tool, result và thời gian.

## 13. Quy tắc ghi chú trong Python

- Tất cả comment, docstring và ghi chú trong file `.py` phải viết bằng **tiếng Việt**.
- Các tên kỹ thuật bắt buộc giữ nguyên như tên biến/hàm, package, class, API, exception, protocol, framework và thuật ngữ chính thức không cần dịch.
- Không viết comment/docstring tiếng Anh mới trong code Python nếu có thể diễn đạt rõ bằng tiếng Việt.
- Khi sửa file Python có comment/docstring tiếng Anh, ưu tiên chuyển phần ghi chú liên quan sang tiếng Việt trong cùng thay đổi.
- Quy tắc này áp dụng cho code mới và các phần code được chỉnh sửa về sau.

## 13. Quy tắc thay đổi

Khi phát sinh yêu cầu mới:
1. cập nhật Decision Log;
2. cập nhật Architecture/Database/domain docs;
3. cập nhật Roadmap nếu cần;
4. ghi Changelog;
5. rồi mới triển khai code.

## 14. Trạng thái

Blueprint V2.1 đã được cập nhật thêm tenant/resource hierarchy, device-resource binding, activity session, task/work order, agent-to-agent communication và anomaly detection.

Architecture contract đã chốt. Database V2.1 001 → 050 đã CLOSED; Agent/Knowledge application runtime vẫn chưa triển khai.
