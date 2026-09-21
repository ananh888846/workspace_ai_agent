# Workspace AI Agent — DATABASE V2.1

> Blueprint database chính thức. Chưa tạo migration hoặc bảng thật.

## 1. Principles

- `organizations` là tenant/business boundary; user có thể thuộc nhiều organization.
- Resource thuộc organization và hỗ trợ parent/child hierarchy.
- Device thuộc organization và có thể bind vào resource.
- Activity Session biểu diễn một khoảng hoạt động có start/end.
- Task/Work Order dùng để đối soát Activity/Activity Session với công việc được giao.
- Agent-to-Agent communication phải có permission và trace; message không tự cấp quyền.
- Anomaly là kết quả dựa trên evidence, không phải kết luận gian lận.

- users là identity trung tâm.
- Organization isolation là tenant boundary cho mọi dữ liệu domain có scope organization.
- user_accounts là external account chuẩn.
- Credential tách khỏi account metadata.
- Ownership tách khỏi access.
- Data Package là access definition.
- Conversation, Memory, Knowledge, Observation, Event, Activity và Data Package là domain riêng.
- SQL giữ transaction, metadata, ownership và authorization.
- Qdrant phục vụ vector retrieval.
- Audit và Run Trace đủ để truy vết operation.

## 2. Database conventions

### ID
Core entities dùng UUID/UUIDv7 theo một convention thống nhất.

### Time
Timestamp lưu timezone-aware UTC; client hiển thị theo timezone user.

### Timestamps
Bảng mutable có created_at và updated_at. Chỉ dùng deleted_at khi domain cần soft delete.

### Foreign keys
Quan hệ core phải có FK. Không dùng JSON để thay thế FK.

### Unique
Provider identity phải có unique constraint theo scope phù hợp. Ví dụ user + provider + external_account_id.

### Index
Ưu tiên index cho user_id, provider, external_account_id, resource_id, package/version id, request_id, occurred_at, created_at và status theo query thực tế.

### JSON metadata
metadata/config chỉ dành cho dữ liệu mở rộng/provider-specific. Field nghiệp vụ quan trọng phải là column rõ ràng.

## 3. Core tables

### users
~~~text
id
uuid
name
email
phone
status
created_at
updated_at
~~~

### organizations
~~~text
id
name
organization_type
status
created_at
updated_at
~~~

### organization_members
~~~text
id
organization_id
user_id
role_id
status
starts_at
expires_at
created_at
updated_at
~~~

User có thể thuộc nhiều organization. Membership không tự động cấp quyền lên mọi account/resource.

### user_sessions
~~~text
id
user_id
session_token_hash
device_id
ip_address
user_agent
started_at
expires_at
last_activity_at
~~~

### user_accounts
~~~text
id
user_id
provider
account_type
external_account_id
display_name
email
status
metadata
created_at
updated_at
~~~

### account_credentials
~~~text
id
user_account_id
credential_type
encrypted_value
expires_at
scopes
status
created_at
updated_at
~~~

Không lưu token plaintext trong user_accounts.

## 4. Authorization

### roles
id, name, description

### permissions
id, resource, action, description

### user_roles
user_id, role_id

### account_grants
~~~text
id
owner_user_id
grantee_user_id
user_account_id
scope
status
starts_at
expires_at
created_at
revoked_at
~~~

scope xác định phạm vi grant; không mặc định cấp toàn bộ quyền owner.

## 5. Resources

### resources
~~~text
id
organization_id
parent_resource_id
resource_type
provider
external_id
owner_user_id
name
status
metadata
created_at
updated_at
~~~

`parent_resource_id` phải cùng organization khi được sử dụng.

### resource_permissions
id, resource_id, user_id, action, effect, created_at, expires_at

## 6. Data Package

### data_packages
id, owner_user_id, name, description, package_type, status, created_at, updated_at

### data_package_versions
id, data_package_id, version, status, created_at, created_by

### data_package_resources
id, package_version_id, resource_id, access_mode

### data_package_grants
id, package_version_id, user_id, permission, starts_at, expires_at, created_at, revoked_at

## 7. Devices

### devices
id, device_uuid, organization_id, resource_id, device_type, name, status, firmware_version, created_at, updated_at, last_seen_at

`resource_id` nullable khi device chưa bind resource cụ thể.

### device_users
device_id, user_id, relationship, status

### device_capabilities
id, device_id, capability, enabled, config

## 8. Observation / Event / Activity Session / Activity

### observations
id, device_id, observation_type, raw_data, confidence, created_at

### events
id, event_uuid, event_type, organization_id, user_id, device_id, resource_id, source_type, source_id, occurred_at, confidence, status, metadata, created_at

### activity_sessions
id, organization_id, user_id, resource_id, session_type, started_at, ended_at, duration_seconds, status, confidence, source_event_id, metadata, created_at, updated_at

### activities
id, organization_id, user_id, activity_type, resource_id, started_at, ended_at, status, confidence, source_event_id, activity_session_id, metadata, created_at

### activities
id, user_id, activity_type, started_at, ended_at, status, confidence, source_event_id, metadata, created_at

~~~text
Observation → Event → Activity Session → Activity
~~~

## 10. Tasks / Work Orders

### tasks
id, organization_id, assigned_user_id, resource_id, task_type, status, scheduled_at, started_at, completed_at, metadata, created_at, updated_at

Task/Work Order không thay thế raw observation hoặc event.

## 11. Conversation / Memory

### conversations
id, user_id, session_id, title, status, created_at, updated_at

### messages
id, conversation_id, role, content, model, tokens, created_at

### memories
id, user_id, memory_type, content, importance, source_conversation_id, status, created_at, updated_at

## 12. Knowledge

### knowledge_documents
id, resource_id, title, source_type, source_id, version, checksum, status, created_at, updated_at

### knowledge_chunks
id, document_id, chunk_index, content_hash, qdrant_point_id, token_count, created_at

Qdrant giữ vector; SQL giữ metadata/access/mapping.

## 13. Agents / Tools / Runs / Agent-to-Agent

### agents
id, name, agent_type, description, status, config, created_at, updated_at

### agent_capabilities
agent_id, capability, enabled

### tools
id, name, provider, version, status, config, created_at, updated_at

### tool_capabilities
tool_id, capability, resource, action, requires_account

### agent_runs
id, request_id, user_id, agent_id, conversation_id, started_at, finished_at, status, model

### tool_runs
id, agent_run_id, tool_id, account_id, started_at, finished_at, status, error

### agent_messages
id, organization_id, sender_agent_id, receiver_agent_id, agent_task_id, message_type, payload, status, created_at, processed_at

### agent_tasks
id, organization_id, parent_agent_task_id, request_id, created_by_agent_id, assigned_agent_id, capability, action, target_resource_id, status, started_at, finished_at, result_metadata, created_at, updated_at

### agent_permissions
id, organization_id, agent_id, grantee_agent_id, capability, action, resource_scope, effect, starts_at, expires_at, created_at

Agent message/task không tự cấp quyền; action vẫn qua authorization/capability/tool boundary.

## 14. Anomaly Detection

### anomalies
id, organization_id, resource_id, user_id, anomaly_type, severity, status, detected_at, confidence, detection_method, summary, metadata, created_at, updated_at

### anomaly_evidence
id, anomaly_id, evidence_type, source_type, source_id, observed_at, weight, metadata, created_at

Anomaly phải có evidence truy ngược được về event/activity/task/device/resource khi có thể.

## 15. Automation

### automations
id, owner_user_id, name, status, created_at, updated_at

### automation_triggers
id, automation_id, event_type, conditions

### automation_actions
id, automation_id, action_type, config

## 16. Audit

### audit_logs
id, request_id, user_id, device_id, action, resource_type, resource_id, account_id, result, ip_address, user_agent, created_at, metadata

## 17. Rollout order

1. Identity + Organization
2. External accounts
3. Authorization
4. Resources + hierarchy
5. Data Packages
6. Devices + organization/resource binding
7. Observation/Event
8. Activity Sessions + Activities
9. Tasks / Work Orders
10. Conversations/Messages
11. Memory
12. Knowledge metadata + Qdrant mapping
13. Agents/Tools/Runs
14. Agent-to-Agent communication
15. Anomaly + Evidence
16. Automation
17. Audit hardening

## 18. Migration gate

Trước migration phải chốt Architecture V2.1 → Database V2.1 → ERD → FK/UNIQUE/CHECK → INDEX → Migration Order → implementation → Runtime Verification.

Domain-specific tables như medication, prescription, social posts và advanced home automation chỉ thêm khi capability được duyệt.
