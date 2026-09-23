# IDENTITY ERD V1 — Thiết kế dữ liệu hoàn chỉnh

**Cập nhật:** 2026-09-23 13:00 (GMT+7, TP.HCM)

> Trạng thái: **PROPOSED — ERD V1 hoàn chỉnh để review trước migration**.
>
> Phạm vi: Human Identity, External Identity, Device Identity, Device Authentication, Interaction Session, Authentication Event, Evidence và NAS/Object Storage.
>
> Tài liệu này là thiết kế logical/physical mapping. **Chưa tạo migration và chưa thay đổi runtime.**

## 1. Mục tiêu

Identity V1 phải đáp ứng:

- Một Human có nhiều External Account.
- External Account và Credential tách biệt.
- Device là Principal độc lập với Human.
- Luckfox/ESP32 có thể authenticate chính nó.
- Edge có thể nhận diện Human bằng face/voice/biometric method mà không biến Device thành User.
- Authentication Context có lifecycle riêng với User Session và Activity Session.
- Unknown Person có thể tạo Authentication Event + Evidence.
- Binary image/video/audio nằm ngoài PostgreSQL.
- PostgreSQL giữ metadata, quan hệ, ownership, integrity, retention và storage reference.
- Evidence access phải đi qua Authorization context.
- Không lưu face embedding/raw credential trong prompt, audit log hoặc Agent state.
- Không tạo bảng trùng với users, user_accounts, devices, account_credentials hiện có.

## 2. Nguyên tắc thiết kế

### 2.1 Không tạo bảng principals generic trong V1

Principal là **khái niệm logical**, không nhất thiết là một bảng polymorphic.

| Logical Principal | Physical source |
|---|---|
| Human Principal | users |
| Device Principal | devices |
| Service Principal | Service identity boundary; DB table chỉ tạo khi Service Authentication implementation được duyệt |

Không tạo principals(subject_type, subject_id) vì sẽ tạo polymorphic FK khó được PostgreSQL bảo vệ và dễ nhân đôi users/devices.

### 2.2 Không tạo external_identities riêng

user_accounts đã là External Identity/External Account canonical model.

Một User có thể có:

User A
→ Google Account 1
→ Google Account 2
→ Zalo
→ Facebook
→ Instagram

account_credentials tiếp tục là credential của external account.

### 2.3 Credential theo boundary

| Credential | V1 storage |
|---|---|
| Google/Zalo/Facebook OAuth/token | account_credentials |
| Device key/certificate/secret | device_credentials — bảng mới |
| Human password | Provider boundary, chưa chốt DB |
| Human passkey | Provider boundary, chưa chốt DB |
| Service server-to-server token | Secret/config boundary, chưa tạo DB table |

account_credentials không đổi nghĩa thành generic credential table.

## 3. ERD tổng thể

    ORGANIZATIONS
        │
        ├── ORGANIZATION_MEMBERS ── USERS
        │                              │
        │                              ├── USER_ACCOUNTS
        │                              │       └── ACCOUNT_CREDENTIALS
        │                              │
        │                              ├── ACCOUNT_GRANTS
        │                              │
        │                              ├── USER_SESSIONS
        │                              │
        │                              └── DEVICE_USERS
        │                                      │
        └── DEVICES ──────────────────────────┘
                │
                ├── DEVICE_CREDENTIALS
                │
                ├── INTERACTION_SESSIONS
                │       │
                │       ├── AUTHENTICATION_EVENTS
                │       │       │
                │       │       └── EVIDENCE
                │       │              │
                │       │              └── EVIDENCE_STORAGE_OBJECTS
                │       │
                │       └── authenticated USER
                │
                └── Device capabilities

Luồng logic:

    Device Identity
          ↓
    Device Authentication
          ↓
    Human Identification / Authentication
          ↓
    Interaction Session
          ↓
    Agent Context
          ↓
    Authorization
          ↓
    Protected Action

## 4. Mapping schema hiện tại → Identity V1

| Entity | Trạng thái | Vai trò |
|---|---|---|
| users | REUSE | Human Identity |
| organization_members | REUSE | Human ↔ Organization membership |
| user_accounts | REUSE | External Identity / External Account |
| account_credentials | REUSE | External Account Credential |
| devices | REUSE | Device Identity |
| device_users | REUSE | Device ↔ Human relationship/trust binding |
| user_sessions | REUSE | Web/client authenticated session; không phải Interaction Session |
| account_grants | REUSE | Delegated external-account authorization |
| device_credentials | NEW | Device Authentication Credential |
| interaction_sessions | NEW | Human ↔ Device ↔ Agent interaction context |
| authentication_events | NEW | Authentication/identification attempts and results |
| evidence | NEW | General Identity/Authentication Evidence |
| evidence_storage_objects | NEW | NAS/Object Storage reference |
| service_principals | DEFERRED | Chỉ tạo khi Service Authentication DB implementation được duyệt |

## 5. Existing tables — contract sử dụng lại

### users

Human Identity canonical. Không tạo Human Identity table thứ hai.

### organization_members

Organization membership. Identity thành công không tự động có quyền.

Protected action vẫn cần:

    Human Identity
    AND Organization Membership
    AND Capability Permission
    AND Account/Resource/Package Authorization

### user_accounts

External Identity canonical. Một User có thể có nhiều account cùng provider nếu external_account_id khác nhau.

### account_credentials

Chỉ lưu credential của user_accounts.

Security boundary:

    Authorization ALLOW
          ↓
    Credential Resolver
          ↓
    account_credentials
          ↓
    Provider

### devices

Device Identity canonical. devices.id là identity nội bộ; devices.device_uuid là identifier được đăng ký.

Device không trở thành User.

### device_users

Đây là binding/relationship, không phải bằng chứng rằng Human vừa được authenticate.

Ví dụ:

    Luckfox-001 ↔ User A
    relationship = owner

Quan hệ này không thay thế authentication_events.

### user_sessions

Giữ nguyên nghĩa authenticated session của Web/client. Không đổi thành Interaction Session.

### account_grants

Giữ nguyên authorization model cho việc một User dùng external account của User khác.

## 6. NEW — device_credentials

### Mục đích

Lưu metadata và encrypted material phục vụ Device Authentication.

### Logical schema

| Column | Type | Null | Key |
|---|---|---:|---|
| id | UUID | NO | PK |
| device_id | UUID | NO | FK |
| credential_type | VARCHAR(64) | NO | INDEX |
| fingerprint | VARCHAR(255) | NO | UNIQUE |
| public_key | TEXT | YES | |
| encrypted_secret | BYTEA | YES | |
| issued_at | TIMESTAMPTZ | NO | |
| expires_at | TIMESTAMPTZ | YES | INDEX |
| revoked_at | TIMESTAMPTZ | YES | INDEX |
| status | VARCHAR(32) | NO | INDEX |
| metadata | JSONB | NO | |
| created_at | TIMESTAMPTZ | NO | |
| updated_at | TIMESTAMPTZ | NO | |

Credential type V1:

- device_key
- certificate
- pre_shared_key

Security:

- encrypted_secret không plaintext;
- không log secret;
- không đưa secret vào AgentContext;
- không đưa secret vào LLM prompt;
- credential revoked/expired không được authenticate.

## 7. NEW — interaction_sessions

### Mục đích

Context của một phiên tương tác.

    User A
      ↓ face
    Luckfox-001
      ↓
    Interaction Session
      ↓
    "Hôm nay tôi có lịch gì?"
      ↓
    Agent

### Logical schema

| Column | Type | Null | Key |
|---|---|---:|---|
| id | UUID | NO | PK |
| organization_id | UUID | NO | FK |
| device_id | UUID | YES | FK |
| user_id | UUID | YES | FK |
| channel | VARCHAR(64) | NO | INDEX |
| authentication_method | VARCHAR(64) | YES | |
| authentication_status | VARCHAR(32) | NO | INDEX |
| started_at | TIMESTAMPTZ | NO | INDEX |
| last_activity_at | TIMESTAMPTZ | YES | INDEX |
| ended_at | TIMESTAMPTZ | YES | |
| status | VARCHAR(32) | NO | INDEX |
| metadata | JSONB | NO | |
| created_at | TIMESTAMPTZ | NO | |

Channel V1:

- browser
- voice
- camera
- display
- edge
- api

Authentication status:

- unknown
- pending
- authenticated
- failed
- expired
- revoked

user_id là authenticated human context, không phải giá trị tin cậy tuyệt đối do Edge gửi.

## 8. NEW — authentication_events

### Mục đích

Lưu từng lần authentication/identification, bao gồm cả thất bại.

### Logical schema

| Column | Type | Null | Key |
|---|---|---:|---|
| id | UUID | NO | PK |
| organization_id | UUID | NO | FK |
| interaction_session_id | UUID | YES | FK |
| device_id | UUID | YES | FK |
| candidate_user_id | UUID | YES | FK |
| authenticated_user_id | UUID | YES | FK |
| method | VARCHAR(64) | NO | INDEX |
| verification_status | VARCHAR(32) | NO | INDEX |
| confidence | NUMERIC(5,4) | YES | |
| provider | VARCHAR(100) | YES | |
| occurred_at | TIMESTAMPTZ | NO | INDEX |
| expires_at | TIMESTAMPTZ | YES | |
| metadata | JSONB | NO | |
| created_at | TIMESTAMPTZ | NO | |

Method V1:

- face
- voice
- passkey
- password
- oauth
- device_key
- certificate

Verification status:

- pending
- recognized
- rejected
- unknown
- expired
- error

### Candidate và authenticated user phải tách

candidate_user_id là candidate do Edge/recognizer đưa ra.

authenticated_user_id chỉ được ghi khi Authentication Policy xác nhận kết quả.

Điều này ngăn candidate trở thành trusted identity chỉ vì model nhận diện.

confidence chỉ là dữ liệu của phương thức nhận diện. Không có rule kiểu confidence > 0.8 = automatically authorized.

## 9. NEW — evidence

### Mục đích

Evidence là bằng chứng, không phải kết luận.

Ví dụ:

    Unknown face detected
          ↓
       snapshot
          ↓
       Evidence

### Logical schema

| Column | Type | Null | Key |
|---|---|---:|---|
| id | UUID | NO | PK |
| organization_id | UUID | NO | FK |
| interaction_session_id | UUID | YES | FK |
| authentication_event_id | UUID | YES | FK |
| device_id | UUID | YES | FK |
| user_id | UUID | YES | FK |
| evidence_type | VARCHAR(64) | NO | INDEX |
| mime_type | VARCHAR(255) | YES | |
| captured_at | TIMESTAMPTZ | NO | INDEX |
| status | VARCHAR(32) | NO | INDEX |
| sha256 | VARCHAR(64) | YES | INDEX |
| size_bytes | BIGINT | YES | |
| retention_until | TIMESTAMPTZ | YES | INDEX |
| metadata | JSONB | NO | |
| created_at | TIMESTAMPTZ | NO | |

Evidence type V1:

- image
- video
- audio
- sensor_snapshot
- recognition_result

Evidence status V1:

- registered
- available
- quarantined
- expired
- deleted

Không lưu binary image/video/audio trong PostgreSQL.

## 10. NEW — evidence_storage_objects

### Mục đích

Trừu tượng hóa NAS/Object Storage.

### Logical schema

| Column | Type | Null | Key |
|---|---|---:|---|
| id | UUID | NO | PK |
| evidence_id | UUID | NO | FK |
| storage_provider | VARCHAR(64) | NO | INDEX |
| storage_class | VARCHAR(64) | YES | |
| bucket | VARCHAR(255) | YES | |
| object_key | TEXT | NO | |
| object_version | VARCHAR(255) | YES | |
| region | VARCHAR(100) | YES | |
| size_bytes | BIGINT | YES | |
| sha256 | VARCHAR(64) | YES | |
| status | VARCHAR(32) | NO | INDEX |
| created_at | TIMESTAMPTZ | NO | |
| deleted_at | TIMESTAMPTZ | YES | |

Canonical reference:

    storage_provider
    bucket
    object_key
    object_version

Không dùng public URL làm source of truth. Signed URL chỉ được tạo tạm thời sau Authorization.

## 11. Authentication → Interaction flow

### Unknown Person

    Device
      ↓
    authentication_event
      verification_status = unknown
      authenticated_user_id = NULL
      ↓
    evidence
      ↓
    evidence_storage_objects
      ↓
    NAS/Object Storage
      ↓
    Agent/Policy

### Recognized Person

    Device
      ↓
    authentication_event
      candidate_user_id = User A
      authenticated_user_id = User A
      verification_status = recognized
      ↓
    interaction_session.user_id = User A
      ↓
    Agent
      ↓
    Authorization

## 12. Device Trust và Human Authentication không gộp

Không thiết kế:

    device_users = authentication

Mà:

    Device Identity
      +
    Device Credential Authentication
      +
    Device/User Binding
      +
    Human Authentication
      +
    Organization Membership
      +
    Authorization

Nếu device_users có Luckfox-001 ↔ User A nhưng face recognition trả unknown thì Interaction Session không tự gán User A.

## 13. Authorization flow

Identity Layer cung cấp context:

    Principal
    Human
    Device
    Interaction
    Authentication Event

Authorization Layer tiếp tục kiểm tra:

    Organization Membership
      AND
    Role/Permission
      AND
    Device trust/capability
      AND
    Account Grant
      AND
    Resource Permission
      AND
    Data Package

Chỉ sau ALLOW:

    Capability / Tool
          ↓
       Provider

DENY:

    Provider call = NOT CALLED
    Credential = NOT RESOLVED

## 14. Evidence access flow

Agent không tự đọc NAS.

    Agent Decision
        ↓
    Need Evidence?
        ↓ YES
    Evidence Authorization
        ↓
    Evidence Record
        ↓
    Storage Resolver
        ↓
    NAS/Object Storage
        ↓
    temporary authorized access
        ↓
    Vision / Audio / Analysis

Không cho Edge gửi public storage URL vào LLM như một cơ chế authorization.

## 15. Tenant integrity

Các bảng mới tenant-scoped:

- device_credentials kế thừa tenant từ devices;
- interaction_sessions;
- authentication_events;
- evidence;
- evidence_storage_objects kế thừa tenant qua evidence.

Các quan hệ bắt buộc cùng Organization:

    interaction_sessions.device_id
        ↔ devices(id, organization_id)

    interaction_sessions.user_id
        ↔ organization_members(organization_id, user_id)

    authentication_events.device_id
        ↔ devices(id, organization_id)

    authentication_events.candidate_user_id
        ↔ organization_members(organization_id, user_id)

    authentication_events.authenticated_user_id
        ↔ organization_members(organization_id, user_id)

    evidence.device_id
        ↔ devices(id, organization_id)

    evidence.user_id
        ↔ organization_members(organization_id, user_id)

    evidence.authentication_event_id
        ↔ authentication_events(id, organization_id)

    evidence.interaction_session_id
        ↔ interaction_sessions(id, organization_id)

Mục tiêu: Cross-organization Identity Context phải bị PostgreSQL reject, không chỉ reject ở application.

## 16. Không lưu biometric raw trong Identity V1

V1 không tạo:

- face_embeddings;
- face_templates;
- voice_embeddings;
- biometric vector store riêng.

Nếu Edge sử dụng local face recognition:

    Face model / template
          ↓
    Edge-local boundary
          ↓
    verification result
          ↓
    Agent

PostgreSQL chỉ cần method, candidate, verification_status, confidence, provider, timestamp.

Central biometric storage là security/privacy design riêng.

## 17. Ba loại Session không được gộp

| Session | Ý nghĩa |
|---|---|
| user_sessions | Phiên authenticated của Web/client |
| interaction_sessions | Phiên Human ↔ Device/Channel ↔ Agent |
| activity_sessions | Phiên hoạt động nghiệp vụ |

Ví dụ:

    Browser login → user_sessions
    Luckfox nhận diện User A → interaction_sessions
    User A thực hiện một hoạt động → activity_sessions

## 18. Interaction Session và Conversation

conversations tiếp tục là Conversation domain.

Không đổi conversations thành Identity table.

Nếu runtime cần nối Interaction với Conversation, có thể bổ sung link sau khi Conversation Context contract được review.

ERD V1 không tạo FK bắt buộc chỉ để nối hai domain, tránh làm Identity migration phụ thuộc Conversation implementation.

## 19. Migration plan dự kiến

Migration 051 đã thuộc Knowledge V1 và không được tái sử dụng.

Sau khi ERD được chốt, migration có thể là:

    052_create_device_credentials.sql
    053_create_interaction_sessions.sql
    054_create_authentication_events.sql
    055_create_evidence.sql
    056_create_evidence_storage_objects.sql

Nếu cần ALTER để bổ sung composite UNIQUE/FK cho tenant integrity, có thể tách migration hậu 056.

**Chưa tạo các migration này. Migration 052 → 056 chỉ mở khi Identity runtime capability thực sự được triển khai và migration gate được duyệt.**

## 20. Acceptance Test Contract trước migration

| ID | Test |
|---|---|
| ID-001 | Device A credential không authenticate được Device B |
| ID-002 | Revoked device credential → DENY |
| ID-003 | Expired device credential → DENY |
| ID-004 | Device authentication không tự tạo Human authentication |
| ID-005 | Recognized Human → candidate và authenticated user hợp lệ |
| ID-006 | Unknown Human → authenticated_user_id = NULL |
| ID-007 | Device Org B không tạo Interaction Session Org A |
| ID-008 | User Org B không trở thành authenticated user của Org A |
| ID-009 | Evidence Org A không tham chiếu Device/User/Event Org B |
| ID-010 | PostgreSQL không chứa binary image/video/audio |
| ID-011 | Không có Authorization ALLOW → không lấy storage object |
| ID-012 | Authentication thành công nhưng thiếu permission → DENY, provider không được gọi |

## 21. Security invariants V1

1. users là Human Identity canonical.
2. devices là Device Identity canonical.
3. Device Identity ≠ Human Identity.
4. user_accounts là External Identity canonical.
5. account_credentials không trở thành generic Human/Device credential table.
6. Device credential có lifecycle độc lập.
7. Authentication ≠ Authorization.
8. Face recognition ≠ permission.
9. Candidate identity ≠ authenticated identity.
10. Unknown person ≠ malicious person.
11. Edge không bypass Agent Authorization.
12. LLM không quyết định identity.
13. LLM không quyết định permission.
14. Credential secret không vào prompt/Graph state/audit/response.
15. Evidence binary không lưu trong PostgreSQL.
16. Evidence access phải được authorization.
17. Cross-organization Identity Context phải bị chặn ở DB.
18. Revoke Device Credential phải ngăn authentication mới.
19. Disabled Human không được tạo protected interaction mới.
20. Side effect chỉ được thực hiện sau Authorization ALLOW.

## 22. Decision boundary

ERD này chưa tự động chốt:

- Human Password Provider;
- Passkey Provider;
- Central biometric storage;
- Service Principal DB model;
- NAS vendor;
- Object Storage vendor;
- Face recognition model;
- Voice recognition model.

Các phần trên cần decision riêng trước implementation tương ứng.

## 23. Kết luận thiết kế

### Reuse

    users
    organization_members
    user_accounts
    account_credentials
    devices
    device_users
    user_sessions
    account_grants

### New

    device_credentials
    interaction_sessions
    authentication_events
    evidence
    evidence_storage_objects

### Deferred

    service_principals
    human password/passkey storage
    central biometric storage

Mô hình canonical:

    Human Identity
          │
          ├── External Identity
          │
          └── Interaction
                 │
    Device Identity ── Authentication
                 │
                 ├── recognized Human
                 └── unknown Human
                          │
                       Evidence
                          │
                   NAS/Object Storage

    Interaction Context
           ↓
    Authorization
           ↓
       Agent Action

**Status:** ACCEPTED — DESIGN LOCKED

Chưa tạo migration. Chưa thay đổi application/runtime.
