# Workspace AI Agent — ERD V2.1

> ERD logic cấp architecture. Schema chi tiết nằm trong `DATABASE_V2_DETAILED.md`.

## 1. Tenant / Identity / Authorization

```mermaid
erDiagram
    USERS ||--o{ ORGANIZATION_MEMBERS : joins
    ORGANIZATIONS ||--o{ ORGANIZATION_MEMBERS : contains
    USERS ||--o{ USER_SESSIONS : owns
    USERS ||--o{ USER_ACCOUNTS : owns
    USER_ACCOUNTS ||--o{ ACCOUNT_CREDENTIALS : secures
    USERS ||--o{ USER_ROLES : assigned
    ROLES ||--o{ USER_ROLES : grants
    ROLES ||--o{ ROLE_PERMISSIONS : maps
    PERMISSIONS ||--o{ ROLE_PERMISSIONS : defines
    USER_ACCOUNTS ||--o{ ACCOUNT_GRANTS : delegated
    ORGANIZATIONS ||--o{ ACCOUNT_GRANTS : scopes
    USERS ||--o{ ACCOUNT_GRANTS : owner
    USERS ||--o{ ACCOUNT_GRANTS : grantee
```

**Quan trọng:** `organization_members.member_role` không thay thế `roles/permissions/role_permissions`.

## 2. Resource / Package

```mermaid
erDiagram
    ORGANIZATIONS ||--o{ RESOURCES : scopes
    RESOURCES ||--o{ RESOURCES : parent
    USERS ||--o{ RESOURCES : owns
    USER_ACCOUNTS ||--o{ RESOURCES : backs
    RESOURCES ||--o{ RESOURCE_PERMISSIONS : protects
    USERS ||--o{ RESOURCE_PERMISSIONS : receives
    ORGANIZATIONS ||--o{ DATA_PACKAGES : scopes
    ORGANIZATIONS ||--o{ DATA_PACKAGE_VERSIONS : scopes
    ORGANIZATIONS ||--o{ DATA_PACKAGE_RESOURCES : scopes
    ORGANIZATIONS ||--o{ DATA_PACKAGE_GRANTS : scopes
    USERS ||--o{ DATA_PACKAGES : owns
    DATA_PACKAGES ||--o{ DATA_PACKAGE_VERSIONS : versions
    DATA_PACKAGE_VERSIONS ||--o{ DATA_PACKAGE_RESOURCES : contains
    RESOURCES ||--o{ DATA_PACKAGE_RESOURCES : included
    DATA_PACKAGE_VERSIONS ||--o{ DATA_PACKAGE_GRANTS : grants
    USERS ||--o{ DATA_PACKAGE_GRANTS : receives
```

Tenant invariants:
- `account_grants` thuộc một `organization_id`; owner và grantee phải là member của organization.
- Data Package, version, package-resource và package-grant đều mang `organization_id`.
- Package chỉ được chứa resource cùng organization.
- `parent_resource_id` phải cùng `organization_id`.
- `resources.organization_id` và `devices.organization_id` là bắt buộc.

## 3. Device / Event / Activity

```mermaid
erDiagram
    ORGANIZATIONS ||--o{ DEVICES : scopes
    RESOURCES ||--o{ DEVICES : binds
    USERS ||--o{ DEVICE_USERS : uses
    DEVICES ||--o{ DEVICE_USERS : assigned
    DEVICES ||--o{ DEVICE_CAPABILITIES : exposes
    DEVICES ||--o{ OBSERVATIONS : produces
    OBSERVATIONS }o--o{ EVENTS : contributes
    EVENTS ||--o{ ACTIVITY_SESSIONS : starts
    EVENTS ||--o{ ACTIVITIES : informs
    ACTIVITY_SESSIONS ||--o{ ACTIVITIES : groups
    ORGANIZATIONS ||--o{ ACTIVITY_SESSIONS : scopes
    ORGANIZATIONS ||--o{ ACTIVITIES : scopes
    ORGANIZATIONS ||--o{ EVENTS : scopes
    TASKS ||--o{ ACTIVITY_SESSIONS : reconciles
    TASKS ||--o{ ACTIVITIES : reconciles
    RESOURCES ||--o{ ACTIVITY_SESSIONS : scopes
    USERS ||--o{ ACTIVITY_SESSIONS : owns
```

Observation là raw observation; Event là meaningful event; Activity Session là lifecycle; Activity là recorded domain activity.

## 4. Conversation / Memory / Knowledge

```mermaid
erDiagram
    USERS ||--o{ CONVERSATIONS : owns
    CONVERSATIONS ||--o{ MESSAGES : contains
    USERS ||--o{ MEMORIES : owns
    CONVERSATIONS ||--o{ MEMORIES : sources
    RESOURCES ||--o{ KNOWLEDGE_DOCUMENTS : scopes
    KNOWLEDGE_DOCUMENTS ||--o{ KNOWLEDGE_CHUNKS : contains
    KNOWLEDGE_CHUNKS }o--|| QDRANT : indexed
```

SQL là source of truth cho ownership/access metadata; Qdrant là vector retrieval store.

## 5. Agents / Tools / Automation / Audit

```mermaid
erDiagram
    AGENTS ||--o{ AGENT_CAPABILITIES : has
    AGENTS ||--o{ AGENT_RUNS : executes
    AGENT_RUNS ||--o{ TOOL_RUNS : calls
    TOOLS ||--o{ TOOL_RUNS : executes
    AGENTS ||--o{ AGENT_MESSAGES : sends
    AGENTS ||--o{ AGENT_MESSAGES : receives
    AGENTS ||--o{ AGENT_PERMISSIONS : grants
    ORGANIZATIONS ||--o{ AGENT_MESSAGES : scopes
    ORGANIZATIONS ||--o{ AGENT_TASKS : scopes
    ORGANIZATIONS ||--o{ AGENT_PERMISSIONS : scopes
    AGENTS ||--o{ AGENT_TASKS : creates
    AGENTS ||--o{ AGENT_TASKS : receives
    AGENT_TASKS ||--o{ AGENT_MESSAGES : carries
    ORGANIZATIONS ||--o{ TASKS : scopes
    RESOURCES ||--o{ TASKS : assigned
    USERS ||--o{ AUTOMATIONS : owns
    AUTOMATIONS ||--o{ AUTOMATION_TRIGGERS : triggers
    AUTOMATIONS ||--o{ AUTOMATION_ACTIONS : acts
    USERS ||--o{ AUDIT_LOGS : generates
    ORGANIZATIONS ||--o{ ANOMALIES : scopes
    ANOMALIES ||--o{ ANOMALY_EVIDENCE : has
    EVENTS ||--o{ ANOMALIES : detects
    ACTIVITIES ||--o{ ANOMALIES : detects
    TASKS ||--o{ ANOMALIES : detects
    DEVICES ||--o{ ANOMALIES : detects
    RESOURCES ||--o{ ANOMALIES : detects
```

Agent-to-Agent message/task không tự cấp quyền; execution vẫn qua Application Authorization.

## 6. Authorization execution path

```text
Request
 ↓
Authentication
 ↓
Organization Context
 ↓
Capability
 ↓
Account Resolver (candidate only)
 ↓
Authorization
 ├─ Membership / tenant eligibility
 ├─ Capability permission
 ├─ Account access
 ├─ Resource access
 └─ Package access (if applicable)
 ↓
Credential Resolver
 ↓
Tool
 ↓
Provider
 ↓
Audit / Run Trace
```

Nếu Authorization = DENY:

```text
Credential Resolver = NOT CALLED
Tool = NOT CALLED
Provider API = NOT CALLED
```


## 7. V2.1 integrity rules

- Organization-scoped entities cannot reference resources/devices/tasks/agents from another organization.
- Account grants cannot cross organization membership boundaries.
- Data Packages cannot contain or grant access to resources/users outside their organization.
- `parent_resource_id` must remain inside the same organization as `resources.organization_id`.
- Device/resource binding must remain inside the same organization.
- Agent-to-Agent delegation is same-organization only in V2.1.
- Anomaly evidence must resolve to a source entity in the same organization as the anomaly.
- Agent message/task is transport/work state; it never grants authorization by itself.
