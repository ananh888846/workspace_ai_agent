# IDENTITY_ARCHITECTURE_V1

> Trạng thái: **ACCEPTED — DESIGN LOCKED**  
> Phạm vi: Identity, Authentication, Interaction Session, Edge Device và Evidence.  
> Tài liệu này là contract kiến trúc trước khi triển khai schema/API/runtime tương ứng.

## 1. Mục tiêu

Workspace AI Agent phải hỗ trợ đồng thời:

- Human User;
- Device như ESP32, Luckfox, camera, sensor;
- Service như Laravel Web, worker hoặc MCP server;
- External Identity như Google/Zalo/Facebook/Instagram;
- tương tác trực tiếp từ Edge Device;
- xác thực người dùng tại Edge;
- trường hợp Edge không xác thực được người;
- lưu Evidence vào NAS/object storage;
- để Agent/Policy quyết định hành động tiếp theo.

Nguyên tắc cốt lõi:

> **Identity xác định principal là ai; Authentication chứng minh principal; Interaction Session xác định ai đang tương tác qua thiết bị nào; Authorization quyết định được làm gì; Evidence lưu bằng chứng để Agent/Policy có thêm context.**

## 2. Các khái niệm chính

### 2.1 Principal

Principal là thực thể có thể authenticate hoặc được hệ thống nhận diện.

V1 gồm:

    Principal
    ├── Human
    ├── Device
    └── Service

Ví dụ:

    Human  → User A
    Device → ESP32-CAM-001
    Device → Luckfox-001
    Service → Laravel Web
    Service → Automation Worker

Device **không phải User**.

## 3. Credential

Credential là bằng chứng dùng để authenticate Principal.

    Credential
    ├── Human
    │   ├── Password
    │   ├── Passkey
    │   └── External OAuth
    ├── Device
    │   ├── Device Key
    │   └── Certificate
    └── Service
        └── Server-to-server credential

Credential secret:

- không đưa vào LLM prompt;
- không đưa vào Graph state;
- không đưa vào AgentContext;
- không ghi vào audit log;
- không trả về browser/API response;
- chỉ được resolve/use trong boundary được phép.

Human authentication provider là một boundary có thể thay thế. **V1 chưa chốt password storage thuộc Laravel hay một Identity Provider cụ thể.** Quyết định này là một decision riêng và không được tự suy luận từ Web session.

## 4. External Identity

Một Human có thể liên kết nhiều External Identity:

    User A
    ├── Google Account 1
    ├── Google Account 2
    ├── Zalo
    ├── Facebook
    └── Instagram

External Identity không phải là User mới.

Nó là identity/account của provider được liên kết với Human Principal hiện tại.

External Account/Grant vẫn tuân theo authorization model hiện hành.

## 5. Device Identity

Mỗi thiết bị có Device Principal riêng.

Ví dụ:

    Luckfox-001
    ESP32-CAM-001
    ESP32-SENSOR-001
    Home-Assistant-001

Device authenticate chính nó bằng device credential.

    Device
      ↓
    Device Credential
      ↓
    Authentication
      ↓
    Authenticated Device Principal

Authentication của Device không đồng nghĩa với authentication của Human.

## 6. Edge Device là Interaction Endpoint

ESP32/Luckfox có thể vừa là:

- camera;
- microphone;
- speaker;
- display;
- sensor gateway;
- local face-recognition node;
- interaction endpoint.

Do đó Edge Device không chỉ gửi telemetry. Nó có thể tạo một **Interaction Session** giữa Human và Agent.

    Human
      │
      │ voice / face / touch
      ▼
    Edge Device
      │
      │ authenticated device
      ▼
    Workspace Agent

## 7. Human Authentication tại Edge

Ví dụ:

    User A đứng trước Luckfox
            ↓
    Camera
            ↓
    Face Detection
            ↓
    Face Recognition
            ↓
    User A

Kết quả phải được biểu diễn là:

    device = Luckfox-001
    identified_human = User A
    method = face

Không được biến thành:

    Luckfox-001 = User A

Device Identity và Human Identity luôn độc lập.

## 8. Face Recognition là Authentication/Identification Method

Face Recognition là một phương thức nhận diện/xác thực Human, không phải quyền.

Edge có thể trả về:

- candidate_user_id;
- method = face;
- confidence;
- verification_status.

Ví dụ:

    verification_status = recognized
    method = face
    candidate = user-a

Agent/Policy vẫn phải áp dụng Authorization trước khi thực hiện protected action.

Đối với hành động nhạy cảm, policy có thể yêu cầu thêm factor hoặc confirmation.

Không dùng face recognition result để tự động cấp toàn quyền cho User.

## 9. Interaction Session

Interaction Session là context của một phiên tương tác.

Tối thiểu có:

    interaction_id
    device_id
    human_principal_id (nullable)
    organization_id (nullable)
    authentication_method
    authentication_status
    started_at
    ended_at
    metadata

Ví dụ:

    interaction_id = int-001
    device = luckfox-001
    human = user-a
    authentication_method = face
    status = authenticated

Trong cùng interaction:

    User A
      │
      ├── "Hôm nay tôi có lịch gì?"
      │
      ▼
    Luckfox
      │
      ▼
    Agent
      │
      ▼
    Calendar
      │
      ▼
    Luckfox Speaker

Interaction Session không phải Authorization.

Nó chỉ cung cấp context để Authorization/Policy sử dụng.

## 10. Device + Human Authorization Context

Khi Agent nhận request từ Edge, context logic là:

    Principal:
        User A

    Interaction Device:
        Luckfox-001

    Organization:
        Home A

    Authentication:
        Face

    Request:
        "Hôm nay tôi có lịch gì?"

Agent phải kiểm tra:

    User A
    AND
    Organization membership
    AND
    Device trust/binding
    AND
    Capability permission
    AND
    Account access
    AND
    Resource access nếu có
    =
    ALLOW

Không được tin tuyệt đối vào user_id do Edge gửi lên.

Agent phải xác minh quan hệ/trust phù hợp giữa Device, Human và Organization.

## 11. Unknown Person

Nếu Edge không xác thực được Human:

    Camera
      ↓
    Face Detection
      ↓
    Face Recognition
      ↓
    UNKNOWN

Edge không được tự kết luận:

    "người này nguy hiểm"

Nó tạo một event/evidence:

    event_type = unknown_person
    device_id = luckfox-001
    interaction_id = ...
    evidence_id = ...

Sau đó Agent/Policy quyết định hành động tiếp theo.

## 12. Evidence

Evidence là dữ liệu bằng chứng có thể phục vụ Agent/Policy.

V1 hỗ trợ:

    Evidence
    ├── Image
    ├── Video
    ├── Audio
    ├── Sensor Snapshot
    └── Derived Recognition Result

Ví dụ:

    unknown_person
        ↓
    snapshot
        ↓
    Evidence
        ├── evidence_id
        ├── device_id
        ├── captured_at
        ├── storage_reference
        ├── mime_type
        ├── size
        ├── sha256
        └── metadata

## 13. NAS / Object Storage Boundary

Ảnh/video/audio lớn **không lưu trực tiếp trong PostgreSQL**.

Kiến trúc:

    PostgreSQL
        │
        │ metadata + reference
        ▼
    Evidence Record
        │
        │ storage_reference
        ▼
    NAS / Object Storage
        ├── images
        ├── videos
        ├── audio
        └── other evidence

PostgreSQL giữ:

- ownership;
- organization;
- device;
- timestamps;
- event/evidence relation;
- storage reference;
- checksum;
- classification/status;
- retention metadata.

NAS/object storage giữ binary payload.

Storage provider có thể thay đổi mà không thay đổi Evidence contract.

## 14. Agent không phải lúc nào cũng cần lấy Evidence

Khi Edge gửi:

    unknown_person
    evidence_id = ev-001

Agent có thể quyết định:

    Need evidence?
    ├── NO
    │   └── xử lý metadata/event
    │
    └── YES
        └── lấy evidence từ storage
                ↓
            Vision / Audio analysis
                ↓
            Agent Decision

Như vậy không cần chuyển toàn bộ ảnh/video lên Agent cho mọi event.

Mục tiêu:

- giảm bandwidth;
- giảm CPU/GPU;
- giảm latency;
- giảm chi phí inference;
- giảm dữ liệu nhạy cảm được truyền không cần thiết.

## 15. Agent Decision Loop

Luồng chuẩn:

    Edge
     ↓
    Device Authentication
     ↓
    Human Identification nếu có
     ↓
    Interaction Session
     ↓
    Event / Evidence
     ↓
    Workspace Agent
     ↓
    Context Resolution
     ↓
    Authorization / Policy
     ↓
    Decision
     ↓
    Tool / Provider / Notification
     ↓
    Edge Response

Agent có thể:

- trả lời;
- đọc Calendar;
- điều khiển Smart Home;
- yêu cầu confirmation;
- phân tích Evidence;
- gửi notification;
- tạo task;
- ghi memory/event;
- yêu cầu Edge tiếp tục thu thập dữ liệu.

## 16. Ví dụ 1 — User được nhận diện

    User A
      ↓
    Luckfox Face Recognition
      ↓
    recognized: User A
      ↓
    "Hôm nay tôi có lịch gì?"
      ↓
    Workspace Agent
      ↓
    Authorization
      ↓
    calendar.read
      ↓
    Google Calendar
      ↓
    "Hôm nay bạn có 3 lịch..."
      ↓
    Luckfox Speaker

## 17. Ví dụ 2 — Không nhận diện được

    Unknown Person
      ↓
    Luckfox
      ↓
    Face recognition failed
      ↓
    Capture snapshot
      ↓
    NAS
      ↓
    Evidence ID
      ↓
    Agent
      ↓
    Policy
      ├── chỉ lưu evidence
      ├── thông báo chủ nhà
      ├── yêu cầu chụp thêm
      ├── yêu cầu video ngắn
      └── action khác theo policy

Agent không tự suy diễn danh tính hoặc ý định của người đó nếu Evidence chưa đủ.

## 18. Ví dụ 3 — User được nhận diện nhưng hành động không được phép

    User A
      ↓
    Face recognized
      ↓
    "Mở cửa"
      ↓
    Agent
      ↓
    Authorization
      ↓
    DENY
      ↓
    Không gọi Smart Lock
      ↓
    Edge:
    "Xin lỗi, bạn không có quyền thực hiện thao tác này."

Authentication thành công **không đồng nghĩa Authorization thành công**.

## 19. Edge Trust Boundary

Edge Device là một trust boundary riêng.

Agent phải phân biệt:

    Device authenticated

với:

    Human authenticated

và:

    Action authorized

Ba trạng thái độc lập.

    Device Auth
         AND
    Human Auth nếu cần
         AND
    Authorization
         =
    Action Allowed

## 20. Privacy và Evidence Retention

Face/image/audio là dữ liệu nhạy cảm trong thực tế triển khai. V1 phải có:

- retention policy;
- quyền truy cập theo Organization;
- audit access;
- checksum/integrity;
- delete/expiry policy;
- không đưa raw evidence vào prompt nếu không cần;
- chỉ lấy Evidence khi workflow cần;
- không log raw image/audio;
- không log face embedding hoặc credential secret nếu không có contract bảo mật riêng.

Việc lưu trữ lâu hay ngắn phải do policy/configuration quyết định, không hard-code trong Edge.

## 21. Laravel Web Boundary

Laravel Web không trở thành Identity Database chỉ vì có Web Session.

Luồng Web:

    Browser
      ↓
    Laravel Authentication boundary
      ↓
    Laravel Session
      ↓
    Agent Identity / Authorization context
      ↓
    Workspace Agent

Laravel session là trạng thái phiên Web.

Identity/Principal/Authorization contract thuộc Agent architecture.

Password authentication provider của Human sẽ được chốt bằng decision riêng; không tạo auth_users mới hoặc biến SQLite Web thành source of truth chỉ để hoàn thành login.

## 22. Multi-channel Interaction

Một Human có thể tương tác với Agent từ nhiều channel:

                        User A
                           │
            ┌──────────────┼──────────────┐
            │              │              │
         Browser        ESP32-CAM       Luckfox
            │              │              │
         Session        Face+Voice     Face+Voice
            │              │              │
            └──────────────┼──────────────┘
                           ▼
                    Workspace Agent

Agent phải giữ được:

- ai;
- thiết bị nào;
- organization nào;
- authentication method nào;
- interaction nào;
- request nào;
- action nào;
- authorization result nào.

## 23. Không để LLM quyết định Identity

LLM có thể hiểu:

> "Hôm nay tôi có lịch gì?"

Nhưng LLM không được quyết định:

    "tôi" = User A

Identity phải đến từ Authentication/Interaction Context.

LLM cũng không được quyết định:

    User A có quyền calendar.read

Authorization service/policy quyết định.

## 24. Không để Edge tự quyết định Authorization

Edge có thể:

- authenticate device;
- nhận diện human;
- phát hiện unknown;
- capture evidence;
- gửi interaction.

Edge không tự cấp:

- calendar permission;
- Gmail permission;
- smart lock permission;
- account access;
- organization access.

Các quyết định protected action thuộc Agent/Application Authorization.

## 25. Canonical Model

Mô hình V1 được chốt:

                         IDENTITY
                            │
                  ┌─────────┴─────────┐
                  │                   │
              PRINCIPAL           CREDENTIAL
                  │                   │
           ┌──────┼──────┐       ┌────┼─────┐
           │      │      │       │    │     │
         Human  Device  Service Password Key OAuth
           │      │
           │      ├── ESP32
           │      └── Luckfox
           │
           └── User A
                  │
                  ▼
           INTERACTION SESSION
                  │
            ┌─────┴─────┐
            │           │
          Human       Device
            │           │
            └─────┬─────┘
                  ▼
                Agent
                  │
            Authorization
                  │
             ┌────┴────┐
             │         │
           Action    Evidence
                       │
                       ▼
                  NAS/Object
                    Storage

## 26. V1 Schema Direction

Tài liệu này **chưa tạo migration**.

Schema implementation phase sau phải xem xét tối thiểu các domain:

    principals
    principal_credentials
    external_identities
    devices
    device_principals / device bindings
    interaction_sessions
    authentication_events
    evidence
    evidence_storage_objects

Không được tạo bảng chỉ vì tên xuất hiện trong blueprint. Trước migration phải review với DATABASE_V2_DETAILED.md, ERD và tenant-integrity contract.

## 27. API Direction

Identity API implementation phase sau phải tách tối thiểu:

    Device Authentication
    Human/Edge Authentication Context
    Interaction Session
    Evidence Registration
    Evidence Retrieval Authorization

Không cho Edge truy cập trực tiếp database.

Không cho Edge gửi credential secret vào LLM.

Không cho browser tự chọn trusted identity headers.

## 28. Security Invariants

Các invariant bắt buộc:

1. Device Identity ≠ Human Identity.
2. Authentication ≠ Authorization.
3. Device authentication ≠ Human authentication.
4. Human authentication ≠ permission.
5. Evidence ≠ fact/conclusion.
6. Unknown person ≠ malicious person.
7. LLM không quyết định identity.
8. LLM không quyết định permission.
9. Edge không bypass Agent Authorization.
10. Credential secret không vào Graph state/prompt/audit/response.
11. Evidence binary không lưu trực tiếp trong PostgreSQL.
12. Evidence access phải qua authorization context.
13. Cross-organization evidence/device/session access phải bị chặn.
14. Device bị revoke phải không thể tiếp tục authenticate.
15. Human bị disable/revoke phải không được tạo protected interaction mới.
16. Side effect chỉ được thực hiện sau Authorization ALLOW.

## 29. Status

**IDENTITY_ARCHITECTURE_V1 = ACCEPTED — DESIGN LOCKED**

Đã chốt các boundary:

    Principal
    Credential
    External Identity
    Device Identity
    Human Identity
    Interaction Session
    Edge Authentication
    Evidence
    NAS/Object Storage
    Agent Decision
    Authorization

Chưa triển khai:

- Identity migration;
- Identity API;
- Password provider;
- Face recognition runtime;
- Luckfox runtime;
- ESP32 runtime;
- NAS integration runtime.

Các phần trên chỉ được triển khai sau khi contract/schema tương ứng được review và chốt.
