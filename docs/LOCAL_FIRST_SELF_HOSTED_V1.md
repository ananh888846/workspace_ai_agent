# LOCAL-FIRST / SELF-HOSTED ARCHITECTURE V1

**Cập nhật:** 2026-09-23 13:30 (GMT+7, TP.HCM)

> Trạng thái: **ACCEPTED — ARCHITECTURAL INVARIANT**
>
> Phạm vi: toàn bộ Workspace AI Agent và các hệ thống Web/Edge tích hợp.

## 1. Mục tiêu

Workspace AI Agent về lâu dài phải có khả năng chạy hoàn toàn trên hạ tầng local/self-hosted của người dùng.

Agent Core không được phụ thuộc bắt buộc vào một AI SaaS/cloud backend để thực hiện các chức năng cốt lõi.

## 2. Local-first

Các thành phần cốt lõi phải có khả năng chạy local:

- Agent Runtime / FastAPI;
- PostgreSQL;
- Qdrant;
- LLM local, trước mắt qua Ollama;
- Conversation / Memory;
- Knowledge;
- Authorization;
- Identity domain khi được triển khai;
- NAS/local object storage khi cần;
- Home Assistant và các local integration;
- Edge Device trên LAN.

Internet là một integration boundary, không phải dependency bắt buộc của Agent Core.

## 3. Cloud là optional provider/integration

Các dịch vụ như:

- Google Calendar;
- Google Drive;
- Zalo;
- Facebook;
- Instagram;
- cloud LLM;
- cloud object storage;

được xem là provider/integration tùy chọn.

Việc mất Internet không được làm Agent Core mất khả năng khởi động, đọc local knowledge, xử lý local memory, thực hiện authorization hoặc phục vụ các workflow không cần provider cloud.

## 4. Provider independence

Business logic không được phụ thuộc trực tiếp vào provider cụ thể.

Luồng chuẩn:

    Agent
      ↓
    Application / Capability
      ↓
    Tool / Provider Adapter
      ↓
    External Provider nếu cần

Provider-specific behavior phải nằm trong provider boundary.

## 5. Local Web

Laravel Web có thể chạy:

- cùng máy chủ local với Agent;
- trên một máy chủ local khác trong LAN;
- hoặc trên server riêng có network access tới Agent.

Web không được biến thành source of truth của Agent Identity, Authorization, Knowledge hoặc Memory.

Luồng:

    Browser
      ↓
    Laravel Web
      ↓ server-to-server
    Workspace AI Agent
      ↓
    Local PostgreSQL / Qdrant / Ollama / local services

## 6. Edge và LAN

ESP32, Luckfox, camera, sensor và Home Assistant có thể giao tiếp với Agent qua LAN.

Edge Device là Interaction Endpoint, không phải database client.

Edge không được:

- truy cập trực tiếp PostgreSQL;
- truy cập trực tiếp Qdrant để bypass authorization;
- tự quyết định permission;
- bypass Agent Authorization.

## 7. Data-local by default

Dữ liệu mặc định ở local:

- conversations;
- messages;
- memories;
- knowledge metadata/chunks;
- identity metadata;
- authorization data;
- events;
- evidence metadata;
- evidence binary nếu dùng NAS/local storage.

Chỉ gửi dữ liệu ra cloud/provider khi capability thực sự cần và đã qua authorization.

Raw evidence không được đưa lên cloud chỉ vì Edge tạo ra evidence.

## 8. LLM architecture

LLM local là provider mặc định cho các workflow có thể xử lý local.

Cloud LLM nếu được hỗ trợ chỉ là provider tùy chọn.

LLM không được sở hữu:

- Identity;
- Authentication;
- Authorization;
- Credential resolution;
- Provider permission.

LLM chỉ thực hiện phần reasoning/generation được application boundary cho phép.

## 9. Offline capability target

Khi Internet mất:

### Phải tiếp tục hoạt động

- Agent process;
- PostgreSQL;
- Qdrant;
- Ollama/local LLM;
- local Knowledge retrieval;
- local Memory;
- local authorization;
- local conversation;
- local Web Chat nếu Web và Agent cùng LAN;
- local Edge communication.

### Có thể tạm thời không hoạt động

- Google Calendar/Drive;
- Zalo/Facebook/Instagram;
- cloud LLM;
- cloud storage;
- các provider yêu cầu Internet.

Provider failure phải được biểu diễn thành lỗi capability/provider rõ ràng, không làm sập Agent Core.

## 10. Security invariant

1. Cloud provider không phải source of truth của Agent Identity.
2. Cloud provider không phải source of truth của Authorization.
3. Internet không phải dependency bắt buộc của Agent Core.
4. Local data mặc định không được tự động đồng bộ lên cloud.
5. Credential secret không vào LLM prompt hoặc Graph state.
6. Edge không bypass Agent Authorization.
7. Provider-specific logic không lan vào Domain/Application core.
8. Local deployment không được bỏ qua security boundary chỉ vì chạy trong LAN.

## 11. Deployment direction

Kiến trúc mục tiêu:

    LOCAL SERVER
    ├── Agent API
    ├── PostgreSQL
    ├── Qdrant
    ├── Ollama
    ├── NAS/Object Storage
    └── supporting workers

    LOCAL LAN
    ├── Laravel Web
    ├── ESP32
    ├── Luckfox
    ├── Home Assistant
    └── other devices

External provider chỉ kết nối qua Provider/Integration boundary.

## 12. Những phần chưa triển khai

Các phần sau được ghi nhận cho phase mở rộng, không triển khai trong Web Chat V1:

- HA/offline queue cho provider;
- provider retry/circuit breaker nâng cao;
- local service discovery;
- mTLS cho mọi Edge Device;
- device_credentials runtime;
- interaction_sessions runtime;
- authentication_events runtime;
- evidence runtime;
- NAS/Object Storage runtime;
- central biometric storage;
- cloud/local LLM routing policy;
- offline sync conflict resolution;
- multi-server local cluster/high availability.

Các phần này chỉ mở khi capability tương ứng thực sự cần.

## 13. Web Chat V1

Web Chat V1 phải kiểm chứng đúng local request path:

    Browser
      ↓
    Laravel
      ↓
    server-to-server auth
      ↓
    Agent API
      ↓
    Agent Runtime
      ↓
    local services

Web Chat không được tạo một Agent riêng, một DB Agent riêng hoặc một LLM cloud riêng.

## 14. Kết luận

Local-first/self-hosted là architectural invariant của Workspace AI Agent.

Mọi thiết kế mới phải trả lời:

> Nếu Internet mất, phần cốt lõi nào vẫn phải hoạt động?

Nếu một dependency cloud không cần thiết cho capability local mà lại trở thành bắt buộc, thiết kế phải được review lại.

**Status: ACCEPTED — ARCHITECTURAL INVARIANT**
