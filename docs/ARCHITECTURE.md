# Workspace AI Agent — ARCHITECTURE V2 FINAL

> Tài liệu kiến trúc chuẩn để làm blueprint trước khi viết code. Phase này chỉ mô tả thiết kế; không giả định các module đã được triển khai.

## 1. Mục tiêu

Workspace AI Agent là nền tảng Agent có khả năng mở rộng từ một Agent cá nhân thành hệ thống nhiều user, nhiều tài khoản ngoài, nhiều thiết bị, nhiều Agent, nhiều Provider và nhiều Data Package.

Mục tiêu chính:

- Một user có thể có nhiều external account.
- Account là dependency của capability, không phải dependency của Agent.
- Quyền truy cập được kiểm soát bằng Authorization + Resource Access + Data Package.
- User A có thể cho User B truy cập một account/resource/package mà không cấp toàn bộ quyền của A.
- Hỗ trợ ESP32/ESP32-CAM/Luckfox/Home Assistant.
- Tách Conversation, Memory, Knowledge, Event, Activity và Data Package.
- Có nền tảng cho LangChain và CrewAI.
- Có thể thêm Google, Facebook, Zalo, Telegram, Home Assistant... mà không sửa Agent Core.
- Có audit và trace để biết ai đã làm gì, dùng account nào và gọi tool nào.

## 2. Nguyên tắc kiến trúc

### Decision 1 — User Account

`user_accounts` là mô hình tài khoản chuẩn của Workspace AI Agent.

Quan hệ chuẩn:

```text
User
  └── user_accounts
       ├── Google
       ├── Facebook
       ├── Zalo
       ├── Telegram
       └── Provider khác
```

Không thiết kế User chỉ có một external account.

### Decision 2 — Account và Permission là hai khái niệm khác nhau

Account xác định nguồn/tài khoản bên ngoài. Authorization xác định user nào được phép sử dụng resource của account đó.

### Decision 3 — Account là dependency của capability

```text
Request
  ↓
Identity
  ↓
AgentContext
  ↓
Router
  ↓
Capability
  ↓
AccountResolver (chỉ khi capability cần account)
  ↓
Authorization
  ↓
Tool
```

Capability không cần account phải hoạt động bình thường mà không có external account.

### Decision 4 — Data Package / Resource Access

Quyền truy cập dữ liệu phải có thể cấp theo package/resource, không cấp mặc định toàn bộ database cho user.

```text
User
  ↓
Data Package
  ↓
Package Version
  ↓
Resource
  ↓
Action
```

Ví dụ User A có dữ liệu lịch nghỉ học của User C và cấp package đó cho User B; User B đọc được package, User không có grant thì không đọc được.

### Decision 5 — Data Package có version

Package có version để giữ lịch sử thay đổi, audit và khả năng rollback logic ở tầng dữ liệu.

### Decision 6 — AgentContext

Mỗi request sau xác thực phải có context gồm request/user/session/device/capability/account/permission/package metadata cần thiết.

Agent không tự bypass authorization để đọc dữ liệu.

### Decision 7 — Ownership và Access tách biệt

Owner của resource không đồng nghĩa với người được phép đọc/ghi resource.

### Decision 8 — Account Delegation

User B có thể được cấp quyền dùng Google Account của User A thông qua grant. Grant phải có scope/action/status/thời hạn nếu cần.

### Decision 9 — Conversation / Memory / Knowledge / Data Package tách biệt

- Conversation: nội dung tương tác.
- Memory: điều Agent cần nhớ.
- Knowledge: dữ liệu có thể retrieval.
- Data Package: phạm vi dữ liệu user được phép truy cập.

### Decision 10 — Device Identity

Device là thực thể riêng, không phải User. Một User có nhiều device; device có capability riêng.

### Decision 11 — LangChain + CrewAI

LangChain dùng cho model/tool/retrieval/agent components. CrewAI dùng cho multi-agent/task workflow. Hai framework không được quyết định user/account/permission.

### Decision 12 — Event / Activity

Observation → Event → Activity là các lớp khác nhau. AI inference không tự động trở thành sự thật nếu chưa có quy tắc xác nhận phù hợp.

## 3. Kiến trúc lớp

```text
Clients
  ↓
API / Gateway
  ↓
Identity & Session
  ↓
AgentContext
  ↓
Application Layer
  ├── Router
  ├── Authorization
  ├── Account Resolver
  ├── Data Package Resolver
  └── Tool Resolver
  ↓
Agent Orchestrator
  ├── Simple Agent
  ├── Workflow Agent
  └── Specialist Agent
  ↓
AI Layer
  ├── LangChain
  ├── CrewAI
  └── Model Providers
  ↓
Capability Layer
  ├── Knowledge
  ├── Event / Activity
  ├── Device
  └── Tool
  ↓
Provider / Infrastructure
  ├── Google
  ├── Facebook
  ├── Zalo
  ├── Telegram
  ├── Home Assistant
  ├── SQL database
  └── Qdrant
```

## 4. Request lifecycle

```text
Request
  ↓
Authenticate
  ↓
Build AgentContext
  ↓
Classify/Route capability
  ↓
Resolve account nếu cần
  ↓
Authorize resource/action
  ↓
Resolve Data Package nếu request dùng package
  ↓
Resolve Tool
  ↓
Execute
  ↓
Record Agent Run / Tool Run / Audit
  ↓
Response
```

LLM có thể hỗ trợ hiểu intent nhưng không được trở thành nguồn quyết định quyền.

## 5. Provider abstraction

Provider-specific code nằm dưới provider/tool layer. Agent Core chỉ làm việc với capability và contract.

Ví dụ:

```text
Capability: calendar.read
        ↓
Tool Resolver
        ↓
Google Calendar Tool
```

Sau này có thể có provider khác mà không thay đổi Authorization model.

## 6. Device architecture

```text
ESP32-CAM 01 ─┐
ESP32-CAM 02 ─┤
...           ├─ Device Gateway → Observation → Event → Activity
ESP32-CAM 10 ─┘
```

Camera có thể capture ảnh, nhận diện khuôn mặt và tạo observation. Việc xác định user và tạo activity phải qua policy phù hợp.

## 7. Activity Agent

Ví dụ:

```text
Camera nhận diện User A về nhà
  ↓
Observation
  ↓
Face verification
  ↓
Event: home_arrival
  ↓
Activity Agent
  ↓
Activity: User A arrived home
```

Medication:

```text
Prescription image
  ↓
Vision / Document extraction
  ↓
Medication information
  ↓
Schedule
  ↓
Automation
  ↓
Reminder
```

## 8. Knowledge architecture

```text
Source
  ↓
Document
  ↓
Chunk
  ↓
Embedding
  ↓
Qdrant
```

SQL giữ metadata/ownership/access; Qdrant giữ vector và retrieval index.

## 9. LangChain và CrewAI

Không đưa framework vào authorization core.

LangChain:

- LLM abstraction
- prompt
- retrieval
- tool calling
- chains/agents

CrewAI:

- multi-agent
- task orchestration
- workflow
- specialist collaboration

Application Layer vẫn là nguồn sự thật về identity, account và authorization.

## 10. Audit và observability

Mọi operation nhạy cảm cần có request_id và audit context.

Cần truy được:

- user nào gửi request;
- device/session nào;
- capability nào;
- account nào;
- resource/package nào;
- tool nào;
- kết quả thành công/thất bại;
- thời gian thực thi.

## 11. Cấu trúc thư mục định hướng

```text
workspace_ai_agent/
├── src/workspace_agent/
│   ├── identity/
│   ├── application/
│   │   ├── context/
│   │   ├── router/
│   │   ├── authorization/
│   │   ├── account_resolver/
│   │   ├── data_package_resolver/
│   │   └── tool_resolver/
│   ├── agents/
│   │   ├── general/
│   │   ├── knowledge/
│   │   ├── activity/
│   │   └── medication/
│   ├── ai/
│   │   ├── langchain/
│   │   ├── crewai/
│   │   └── models/
│   ├── capabilities/
│   ├── tools/
│   ├── providers/
│   │   ├── google/
│   │   ├── facebook/
│   │   ├── zalo/
│   │   └── home_assistant/
│   ├── devices/
│   ├── events/
│   ├── activities/
│   ├── data_packages/
│   ├── knowledge/
│   ├── memory/
│   ├── conversations/
│   ├── automation/
│   ├── database/
│   └── audit/
├── tests/
└── docs/
```

## 12. Nguyên tắc không phá kiến trúc

Không cho Agent truy cập trực tiếp provider API, database hoặc Qdrant nếu operation đó bỏ qua Application/Authorization layer.

Không để LLM tự chọn account theo suy đoán khi request không chỉ rõ account mà policy cần user confirmation/selection.

Không gộp memory với knowledge.

Không gộp event với activity.

Không coi device là user.

Không xây tất cả provider trước khi core authorization/data package được kiểm chứng.

## 13. Trạng thái blueprint

Đây là bản thiết kế V2 để duyệt. Chưa coi các module tương lai là đã triển khai.
