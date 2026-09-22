# Agent Runtime V2.2 — Phase 1

> Trạng thái: **Implemented — orchestration seam V1**  
> Ngày: 2026-09-22

## Mục tiêu

Phase 1 triển khai phần lõi đã được phê duyệt trong Decision 045 mà không rewrite toàn bộ Calendar runtime:

- tạo **Agent Runtime Entry** độc lập với FastAPI;
- tạo **LangGraph Super-Graph** tối thiểu;
- giữ `/api/v1/agent/chat` làm compatibility endpoint;
- giữ Application Authorization, Credential Resolver, Tool và Provider boundary hiện tại;
- không đưa secret vào Graph state;
- không thêm Agent service vào Docker Compose.

## Luồng Phase 1

```text
FastAPI
  ↓
Agent Runtime Entry
  ↓
LangGraph Super-Graph
  ├── classify_request
  └── execute_route
        ↓
Existing Application Runtime
  ├── Account Resolver
  ├── Authorization
  ├── Credential Resolver
  ├── Tool
  └── Provider
```

`execute_route` nhận state đã phân loại và gọi application callback được dependency injection. Graph không biết SQL, Qdrant, OAuth secret hoặc provider API.

## Vì sao chưa tách toàn bộ Calendar execution?

Calendar V1 đang là regression baseline. Việc tách toàn bộ `agent_chat()` trong một commit sẽ tạo thay đổi lớn và tăng rủi ro regression.

Phase 1 vì vậy chỉ tạo orchestration seam. Phase tiếp theo sẽ di chuyển từng capability vào route/handler riêng, sau mỗi bước chạy regression.

## Graph state

State chỉ chứa:

- request;
- context;
- intent;
- capability;
- action;
- result.

Không chứa:

- access token;
- refresh token;
- client secret;
- credential object;
- SQL connection;
- provider client.

## Deployment

Không thay đổi Docker Compose. Postgres và Qdrant tiếp tục là infrastructure services. Agent Runtime vẫn có thể chạy cùng process Python/FastAPI trong development.

## Tiêu chí mở Phase 2

- Phase 1 unit test PASS.
- Calendar regression vẫn PASS.
- Không phát sinh provider side effect ngoài hành vi hiện tại.
- Sau đó mới tách capability routing và execution handler khỏi endpoint.


## Phase 2 — Capability Routing

**Trạng thái:** Implemented — chờ runtime verification.

Phase 2 đã thay đổi Super-Graph thành router thực tế:

- app/agent_runtime/runtime.py bổ sung route trong graph state.
- Thêm node route_request và conditional edges tới capability handler tương ứng.
- AgentRuntimeDependencies dùng route_handlers thay cho một execute callback duy nhất.
- calendar.read và calendar.write được đăng ký từ Agent Runtime wiring trong app/main.py.
- default handler giữ compatibility cho request chưa có capability route riêng.
- Nếu không có route và không có default, Graph trả unsupported_action với provider_called=false.
- Graph state không chứa credential, access token hoặc provider client.
- Calendar execution logic chưa bị rewrite; mục tiêu là giảm rủi ro regression.

### Verification gate
Sau khi pull code, phải chạy:

```text
python -m pytest tests/unit/agent_runtime -q
python -m pytest -q
```

Chỉ khi cả hai suite PASS mới ghi nhận Phase 2 đã verified.


## Runtime V2.2 — Phase 3: Calendar Application Handler

### Trạng thái
**Implemented — chờ verification local**

Phase 3 tách orchestration của Calendar capability khỏi FastAPI entry:

```text
FastAPI
  ↓
Agent Runtime
  ↓
LangGraph Super-Graph
  ↓
CalendarHandler
  ↓
Account Resolver
  ↓
Authorization
  ↓
Credential Resolver
  ↓
Calendar execution / Tool
  ↓
Provider
```

### Thành phần

- `app/application/capabilities/calendar.py`
  - là Application Handler của Calendar;
  - nhận `AgentRuntimeState`;
  - thực hiện Account → Authorization → Credential;
  - dispatch `calendar.read` / `calendar.write`;
  - áp dụng Execution/Error Boundary trước response;
  - không lưu credential/secret trong Graph state.
- `app/main.py`
  - chỉ còn FastAPI transport, request schema, OAuth HTTP endpoints và Agent Runtime wiring;
  - không còn `_execute_agent_chat()`;
  - Calendar routes được đăng ký trực tiếp vào `calendar_handler.handle`.
- `app/api/chat.py`
  - Phase 3 chưa rewrite toàn bộ Calendar provider execution functions để tránh thay đổi hành vi Calendar V1;
  - các function execution hiện hữu được Handler gọi như execution adapter trong bước chuyển tiếp.

### Nguyên tắc không thay đổi

- Không thay đổi DB schema/migration.
- Không thay đổi OAuth scope.
- Không thêm Agent service/Docker service.
- Không để LangGraph truy cập SQL, credential secret hoặc provider API.
- Không rewrite Calendar CRUD, Free/Busy, Scheduling, Recurrence.
- Giữ compatibility endpoint `POST /api/v1/agent/chat`.

### Verification gate

Sau khi pull:

```powershell
python -m pytest tests/unit/application/test_calendar_handler.py tests/unit/agent_runtime -q
python -m pytest -q
```

Baseline trước Phase 3: **94 passed, 2 warnings**. Phase 3 phải đạt toàn bộ regression trước khi chuyển Phase 4.


## Phase 3 — Regression compatibility fix

Sau verification local, Phase 3 phát hiện 8 regression failures do test boundaries cũ vẫn patch symbol từ `app.main`, trong khi orchestration đã được chuyển sang `CalendarHandler`.

Đã sửa theo đúng kiến trúc mới:
- Runtime/API tests patch Account, Authorization, Credential và Calendar execution tại `app.application.capabilities.calendar`.
- CalendarHandler trả HTTP 400 cho request cần runtime authorization context nhưng thiếu user/organization context.
- Không đưa compatibility dependency ngược vào FastAPI main.

Mục tiêu là giữ FastAPI là transport boundary và CalendarHandler là application capability boundary, thay vì khôi phục coupling cũ.

**Trạng thái:** chờ chạy lại targeted + full regression.


## Phase 3 — OAuth-required boundary hardening

Verification local sau regression compatibility fix còn **1 failure / 96 passed** ở nhánh `oauth_required`: `execution.credential.provider_called` thực tế là `true`, trong khi contract yêu cầu `false` vì provider chưa được gọi.

Đã gia cố `CalendarHandler`:
- khi `CredentialResolution.status != "ready"`, handler trả ngay;
- ép `execution.credential.provider_called = false`;
- ép `execution.provider_called = false`;
- không dispatch Calendar execution/provider.

**Trạng thái:** chờ chạy lại targeted + full regression. Không chuyển Phase 4 cho tới khi full suite PASS.


## 2026-09-22 — Hardening lần 2: cô lập credential provider_called cho oauth_required

Local verification sau commit trước vẫn còn 1 failure: `oauth_required` trả `execution.credential.provider_called = true` dù handler đã dừng trước provider. Đã gia cố bằng cách tạo dict credential mới khi nhánh pre-provider kết thúc, tránh mọi alias/reference có thể làm thay đổi cờ `provider_called` sau phép gán.

**Trạng thái:** chờ verification local lại. Chưa đóng Phase 3.


## Phase 3 — OAuth-required test boundary root cause

Đã xác định failure còn lại không nằm ở Execution/Error Boundary production. Runtime test mock sai namespace của `CredentialResolver`: handler sử dụng symbol đã import tại `app.application.capabilities.calendar`, trong khi test mock `app.application.core_runtime.CredentialResolver`.

Đã cập nhật test để mock đúng `app.application.capabilities.calendar.CredentialResolver`, bảo đảm `credential_result.status` mà Handler kiểm tra thực sự là `oauth_required`.

**Trạng thái:** chờ chạy lại targeted + full regression.

## Phase 3 — VERIFIED

Ngày 2026-09-22, Phase 3 đã PASS toàn bộ verification local:
- `tests/unit/application/test_calendar_handler.py tests/unit/agent_runtime`: **6 passed**;
- `python -m pytest -q`: **97 passed, 0 failed, 2 warnings**.

Đã xác nhận CalendarHandler là application capability boundary; FastAPI không còn giữ orchestration Calendar cũ. OAuth-required là pre-provider error và test boundary đã mock đúng dependency namespace.

**Phase 3 status: CLOSED / VERIFIED.**


## Phase 4 — E2E Agent + Google Calendar real provider

### Trạng thái
**Implementation started — chưa VERIFIED**

Phase 4 chuyển verification từ unit/regression sang real-provider E2E. Test đầu tiên nằm tại [tests/e2e/test_calendar_agent_google.py](../tests/e2e/test_calendar_agent_google.py).

### Phase 4A flow

`Client/TestClient → POST /api/v1/agent/chat → Agent Runtime → LangGraph Super-Graph → CalendarHandler → Account Resolver → Authorization → Credential Resolver → Calendar execution / Tool → Google Calendar API`

### E2E scenarios đã thêm
1. Tạo event thật và xác nhận `provider_called=true`.
2. Đọc event vừa tạo từ Google Calendar thật.
3. Gửi delete chưa confirmation và xác nhận `confirmation_required` + `provider_called=false`.
4. Gửi delete đã confirmation và xác nhận event được xóa thật.
5. Fixture cleanup tự dọn event nếu test không xóa event.

### Isolation
E2E được bật bằng `RUN_GOOGLE_CALENDAR_E2E=1`, vì vậy regression mặc định không gọi Google Calendar thật. User/account/organization được lấy từ environment; test không chứa token hay credential secret.

### Lưu ý
Phase 4A cố ý kiểm chứng provider/runtime boundary trước. Natural-language extraction đầy đủ cho “ngày mai”, “tuần này”, “chiều mai rảnh 1 tiếng” và “kéo dài 1 tiếng” là phần tiếp theo sau khi baseline real-provider PASS.
