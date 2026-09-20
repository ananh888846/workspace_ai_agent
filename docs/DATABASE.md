# Workspace AI Agent — DATABASE V2

> Blueprint database. Chưa code migration và chưa tạo bảng thật trong phase tài liệu.

## 1. Nguyên tắc

- `users` là identity trung tâm.
- `user_accounts` là mô hình external account chuẩn.
- Account credentials tách khỏi account metadata.
- Ownership tách khỏi access.
- Data Package là lớp gom resource để cấp quyền theo dữ liệu.
- Conversation, Memory, Knowledge, Event, Activity và Data Package là các domain khác nhau.
- SQL lưu metadata, transaction, ownership và authorization; Qdrant phục vụ vector retrieval.
- Audit và Agent Run phải đủ để truy vết operation.

## 2. Identity

### users

```text
id
uuid
name
email
phone
status
created_at
updated_at
```

### user_sessions

```text
id
user_id
session_token_hash
device_id
ip_address
user_agent
started_at
expires_at
last_activity_at
```

## 3. External Accounts

### user_accounts

```text
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
```

Một user có nhiều account.

### account_credentials

```text
id
user_account_id
credential_type
encrypted_value
expires_at
scopes
status
created_at
updated_at
```

Không lưu token plaintext trong `user_accounts`.

## 4. Authorization

### roles

```text
id
name
description
```

### permissions

```text
id
resource
action
description
```

### user_roles

```text
user_id
role_id
```

### account_grants

```text
id
owner_user_id
grangee_user_id
user_account_id
status
starts_at
expires_at
created_at
revoked_at
```

`account_grants` cho phép User B sử dụng một external account thuộc User A trong phạm vi grant.

## 5. Resources

### resources

```text
id
resource_type
provider
external_id
owner_user_id
name
status
metadata
created_at
updated_at
```

Resource có thể là calendar, drive file, device, activity, knowledge collection, social resource...

### resource_permissions

```text
id
resource_id
user_id
action
effect
created_at
expires_at
```

## 6. Data Package

### data_packages

```text
id
owner_user_id
name
description
package_type
status
created_at
updated_at
```

### data_package_versions

```text
id
data_package_id
version
status
created_at
created_by
```

### data_package_resources

```text
id
package_version_id
resource_id
access_mode
```

### data_package_grants

```text
id
package_version_id
user_id
permission
starts_at
expires_at
created_at
revoked_at
```

Ví dụ: package `school_attendance` có thể cấp cho User B mà không cấp cho User C.

## 7. Devices

### devices

```text
id
device_uuid
device_type
name
status
firmware_version
created_at
updated_at
last_seen_at
```

### device_users

```text
device_id
user_id
relationship
status
```

### device_capabilities

```text
id
device_id
capability
enabled
config
```

## 8. Observations / Events / Activities

### observations

```text
id
device_id
event_id
observation_type
raw_data
confidence
created_at
```

### events

```text
id
event_uuid
event_type
user_id
device_id
source_type
source_id
occurred_at
confidence
status
metadata
created_at
```

### activities

```text
id
user_id
activity_type
started_at
ended_at
status
confidence
source_event_id
metadata
created_at
```

Luồng chuẩn:

```text
Observation → Event → Activity
```

## 9. Conversation

### conversations

```text
id
user_id
session_id
title
status
created_at
updated_at
```

### messages

```text
id
conversation_id
role
content
model
tokens
created_at
```

## 10. Memory

### memories

```text
id
user_id
memory_type
content
importance
source_conversation_id
status
created_at
updated_at
```

Memory không thay thế Knowledge.

## 11. Knowledge

### knowledge_documents

```text
id
resource_id
title
source_type
source_id
version
checksum
status
created_at
updated_at
```

### knowledge_chunks

```text
id
document_id
chunk_index
content_hash
qdrant_point_id
token_count
created_at
```

Qdrant lưu vector; SQL lưu metadata, ownership và mapping.

## 12. Agents

### agents

```text
id
name
agent_type
description
status
config
created_at
updated_at
```

### agent_capabilities

```text
agent_id
capability
enabled
```

## 13. Tools

### tools

```text
id
name
provider
version
status
config
created_at
updated_at
```

### tool_capabilities

```text
tool_id
capability
resource
action
requires_account
```

## 14. Runs / Trace

### agent_runs

```text
id
request_id
user_id
agent_id
conversation_id
started_at
finished_at
status
model
```

### tool_runs

```text
id
agent_run_id
tool_id
account_id
started_at
finished_at
status
error
```

## 15. Automation

### automations

```text
id
owner_user_id
name
status
created_at
updated_at
```

### automation_triggers

```text
id
automation_id
event_type
conditions
```

### automation_actions

```text
id
automation_id
action_type
config
```

## 16. Audit

### audit_logs

```text
id
request_id
user_id
device_id
action
resource_type
resource_id
account_id
result
ip_address
user_agent
created_at
metadata
```

## 17. Quan hệ tổng quát

```text
users
 ├── user_accounts ── account_credentials
 ├── user_roles ── roles ── permissions
 ├── account_grants
 ├── data_packages
 │    ├── data_package_versions
 │    ├── data_package_resources ── resources
 │    └── data_package_grants
 ├── devices ── device_capabilities
 │          └── observations/events ── activities
 ├── conversations ── messages
 ├── memories
 ├── agent_runs ── tool_runs
 └── audit_logs

resources ── resource_permissions
knowledge_documents ── knowledge_chunks ── Qdrant
agents ── agent_capabilities
 tools ── tool_capabilities
```

## 18. Database rollout order

1. Identity.
2. External accounts.
3. Authorization.
4. Resources.
5. Data Packages.
6. Devices.
7. Observations/Events/Activities.
8. Conversations/Messages.
9. Memory.
10. Knowledge metadata + Qdrant mapping.
11. Agents/Tools/Runs.
12. Automation.
13. Audit hardening.

## 19. Chưa triển khai trong blueprint

Các bảng domain đặc thù như medication, prescription, social posts, home automation nâng cao chỉ được thêm khi capability tương ứng được duyệt; không làm phình Core Database ngay từ đầu.
