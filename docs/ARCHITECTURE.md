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

## 2. Request lifecycle

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

## 3. Authorization

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

## 4. AgentContext

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

## 5. Account và Capability

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

## 6. Data Package

Data Package là access definition, không phải credential và không bắt buộc là bản sao dữ liệu.

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

## 7. Provider

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

## 8. Device / Event

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

## 9. Knowledge

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

## 10. LangChain / CrewAI

LangChain cung cấp LLM, retrieval, tool và agent primitives. CrewAI cung cấp multi-agent/task/workflow orchestration. Authorization vẫn thuộc Application Layer.

## 11. Audit

Operation nhạy cảm phải truy được request_id, user, session/device, capability/action, account, resource/package, tool, result và thời gian.

## 12. Quy tắc thay đổi

Khi phát sinh yêu cầu mới:
1. cập nhật Decision Log;
2. cập nhật Architecture/Database/domain docs;
3. cập nhật Roadmap nếu cần;
4. ghi Changelog;
5. rồi mới triển khai code.

## 13. Trạng thái

Blueprint V2 đã chốt để làm nguồn tham chiếu implementation. Chưa có nghĩa module đã được triển khai.
