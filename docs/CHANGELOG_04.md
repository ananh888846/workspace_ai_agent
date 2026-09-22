# CHANGELOG_04.md

> Changelog tiếp theo của `docs/CHANGELOG_03.md`.
>
> Quy tắc: chỉ ghi trạng thái đã được triển khai/kiểm tra; không ghi `PASS` nếu chưa có runtime verification.

## 2026-09-22 — Triển khai Execution Contract V1 và Error Contract V1

- Thêm [`app/application/execution_contract.py`](../app/application/execution_contract.py):
  - `ExecutionStatus`;
  - `ExecutionContract`;
  - `ResultContract`;
  - `ErrorContract`;
  - helper tạo execution/result chuẩn;
  - helper chuẩn hóa alias status runtime.
- Thêm [`tests/application/test_execution_contract.py`](../tests/application/test_execution_contract.py) để kiểm tra shape, error boundary, retryable và status normalization.
- Thêm [`docs/EXECUTION_CONTRACT.md`](./EXECUTION_CONTRACT.md) làm specification V1.
- Chưa thay đổi database schema và chưa tạo migration.

## 2026-09-22 — Wire Execution Contract vào Agent Chat Runtime

- Cập nhật [`app/main.py`](../app/main.py).
- `/api/v1/agent/chat` hiện tạo `execution` từ `build_execution_contract()` thay vì tự dựng execution shape riêng.
- Runtime account/authorization/credential status được normalize qua `normalize_result_status()` trước khi trả API.
- Giữ nguyên response contract hiện tại của Calendar V1 để không phá regression baseline.
- `provider_called` tiếp tục phản ánh provider call thực tế.
- Không tạo migration database.
- Không thêm LangGraph/Pydantic cho bước wiring này.
- Local verification đã PASS:
  - [`tests/application/test_execution_contract.py`](../tests/application/test_execution_contract.py): **4 passed**.
  - [`tests/services/test_scheduling.py`](../tests/services/test_scheduling.py), [`tests/unit/graphs/test_scheduling.py`](../tests/unit/graphs/test_scheduling.py), [`tests/unit/api/test_chat_api.py`](../tests/unit/api/test_chat_api.py): **18 passed, 1 warning**.

## 2026-09-22 — Execution Error Boundary V1

- Thêm [`app/application/execution_boundary.py`](../app/application/execution_boundary.py).
- Chuẩn hóa nhóm lỗi **trước provider**:
  - `account_not_found`;
  - `account_selection_required`;
  - `authorization_denied`;
  - `oauth_required`;
  - `validation_error`;
  - `confirmation_required`;
  - `unsupported_action`.
- Các lỗi trước provider bắt buộc `provider_called=false` và không retry.
- `provider_error` bắt buộc `provider_called=true`; có thể đánh dấu `retryable=true` khi provider failure có thể retry an toàn.
- Thêm `enforce_result_boundary()` làm điểm kiểm tra cuối cho capability result trước API response.
- Cập nhật [`app/main.py`](../app/main.py) để đưa Calendar capability result qua boundary enforcement.
- Boundary violation không bị chuyển thành `provider_error` giả.
- Thêm [`tests/application/test_execution_boundary.py`](../tests/application/test_execution_boundary.py) kiểm tra:
  - provider boundary;
  - retry policy;
  - status alias normalization;
  - provider error boundary.
- Chưa tạo migration và chưa thay đổi database schema.
- Chưa ghi nhận runtime PASS cho nhóm test mới; cần chạy local verification sau khi pull.

### Commit

- `900105f25e34a57f907f0c680f7cdc30f2f2cab6` — wire Execution Contract vào Agent Chat Runtime.
- `04cc9818b699630c86698d092070b2a190a9e7be` — thêm Execution Error Boundary V1.
- `e1191b6136622411269f11170f44ebfa99476793` — enforce boundary cho capability result.
- `8fe143794f2b1e474e74763a8a6802e50af7bed6` — wire boundary enforcement vào Agent Chat.
- `1a4df750f4822211108a2b53abba526e00da9cd6` — bổ sung test boundary.
- `9173a230ca7050506ae4244f78425bc47dc5e953` — giữ boundary violation không bị map thành provider error.

## 2026-09-22 — Runtime HTTP Verification cho Execution Error Boundary V1

- Thêm `tests/runtime/test_execution_error_boundary_runtime.py`.
- Dùng FastAPI `TestClient` gọi trực tiếp `POST /api/v1/agent/chat`.
- Bao phủ 5 nhánh runtime:
  - `account_not_found`;
  - `authorization_denied`;
  - `oauth_required`;
  - `validation_error` và xác nhận provider không bị gọi;
  - `provider_error` và xác nhận provider đã được đánh dấu đã gọi.
- Provider boundary được mô phỏng tại application execution boundary; không tạo/sửa/xóa Google Calendar event thật.
- Runtime verification trên môi trường local đã PASS:
  - runtime boundary suite: **5 passed, 1 warning**;
  - regression suite `tests/application tests/unit/api tests/runtime`: **32 passed, 2 warnings**.
- Warning hiện tại đến từ dependency:
  - Starlette/TestClient sử dụng API AnyIO đã deprecated;
  - Google API Core cảnh báo `grpcio 1.81.1` sẽ cần nâng lên `>=1.83.0` khi yêu cầu tương thích PQC của Google Cloud Python packages có hiệu lực vào tháng 10/2026.
- Không có test failure.
- Không tạo/sửa/xóa Google Calendar event thật và không thay đổi OAuth thật.
- **Execution Error Boundary V1 được xác nhận PASS qua runtime verification và regression suite.**


## 2026-09-22 — Hoàn thiện Scheduling Assistant V1

- Hoàn thiện `app/graphs/scheduling.py` theo Decision 041:
  - `classify_request`;
  - `resolve_calendar`;
  - `get_free_busy`;
  - `find_available_slots`;
  - `confirm` ở trạng thái `not_required` vì V1 không có side effect;
  - `format_result`.
- Graph state bổ sung `timezone`, `conflicts` và `confirmation_state`.
- Giữ nguyên nguyên tắc LangGraph chỉ orchestration; dependency provider được inject từ Application boundary.
- Hoàn thiện `app/services/scheduling.py`:
  - thêm `find_conflicts()`;
  - chuẩn hóa/clipping busy period theo search window;
  - giữ SchedulingService độc lập với LangGraph, credential, SQL, Qdrant và provider.
- Cập nhật `app/api/chat.py` để trả `conflicts` và `confirmation_state` trong Scheduling result.
- Bổ sung unit test cho conflict clipping và Scheduling Graph state.
- Không thêm Pydantic mới cho Scheduling domain.
- Không tạo migration database.
- Chưa ghi nhận runtime PASS; cần chạy test local sau khi pull.


## 2026-09-22 — Runtime Verification Scheduling Assistant V1

- Unit/domain + LangGraph Scheduling suite đã PASS:
  - `tests/services/test_scheduling.py`: **8 passed**.
  - `tests/unit/graphs/test_scheduling.py`: **1 passed**.
  - Tổng: **9 passed, 0 failed**.
- Regression suite đã PASS:
  - `tests/application tests/unit/api tests/runtime`: **32 passed, 2 warnings**.
- Runtime verification xác nhận:
  - Execution Contract/Error Boundary không bị regression.
  - Calendar scheduling classification và runtime authorization wiring tiếp tục PASS.
  - Scheduling Graph orchestration và SchedulingService tiếp tục PASS.
- Hai warning đều là dependency warning, không phải test failure:
  - Starlette/TestClient sử dụng alias AnyIO đã deprecated.
  - Google API Core cảnh báo `grpcio 1.81.1` sẽ cần `>=1.83.0` từ tháng 10/2026.
- Không tạo/sửa/xóa Google Calendar event thật trong các suite trên.
- Không thay đổi OAuth scope và không tạo migration database.
- **Scheduling Assistant V1 được xác nhận PASS qua unit/domain verification và regression suite.**


## 2026-09-22 — Triển khai Calendar Recurrence V1

- Thêm [app/services/calendar_recurrence.py](../app/services/calendar_recurrence.py): parse, validate và chuẩn hóa RRULE.
- Hỗ trợ DAILY, WEEKLY, MONTHLY, YEARLY; INTERVAL; COUNT; UNTIL; BYDAY.
- Cập nhật [app/api/chat.py](../app/api/chat.py) để validate recurrence trước khi Google Calendar provider được gọi.
- Cập nhật [app/main.py](../app/main.py) để nhận field recurrence cho Calendar create/update.
- Bổ sung [tests/services/test_calendar_recurrence.py](../tests/services/test_calendar_recurrence.py).
- Không dùng LangGraph/Pydantic cho recurrence domain service.
- Không tạo migration database.
- Chưa ghi nhận runtime PASS; cần chạy test local sau khi pull.
- Decision kiến trúc được ghi tại [docs/DECISIONS.md](./DECISIONS.md) — Decision 043.


## 2026-09-22 — Runtime Verification Calendar Recurrence V1

- `tests/services/test_calendar_recurrence.py`: **8 passed**.
- Regression `tests/application tests/unit/api tests/runtime`: **32 passed, 2 warnings**.
- Recurrence validation được xác nhận không làm hỏng Execution Contract/Error Boundary.
- Không có failure.
- 2 warnings là dependency warnings đã biết:
  - Starlette/TestClient dùng deprecated AnyIO BlockingPortal alias.
  - Google API Core cảnh báo grpcio 1.81.1 sẽ cần >=1.83.0 từ tháng 10/2026 cho PQC.
- Không tạo migration.
- Chưa thực hiện E2E mutation trên Google Calendar trong lượt verification này.
- **Calendar Recurrence V1 — UNIT + REGRESSION PASS.**


## 2026-09-22 — Review Account Resolver + Account Grant V1 và khóa Multi-account design

- Review runtime hiện tại của Account Resolver, Authorization và Credential Resolver.
- Xác nhận DB hiện tại đã có đủ nền tảng cho Multi-account V1: `user_accounts`, `account_credentials`, `account_grants`, organization membership và tenant constraints.
- Chốt contract `ResolvedAccount` với `account`, `access_mode`, `account_grant_id`, `organization_id`; không chứa secret.
- Chốt Account selection policy: explicit `account_hint` → default policy nếu có → single candidate → `account_selection_required`; không cho LLM tự chọn account.
- Chốt Account Grant scope là giới hạn quyền ủy quyền, không thay thế user capability permission và không được elevate permission.
- Chốt grant lifecycle: active + starts_at + expires_at + revoked_at.
- Chốt owner/grant access mode.
- Chốt test matrix A01–A20 và side-effect assertions.
- Không tạo migration DB ở bước design lock.
- Không thay đổi code runtime trong lượt này.
- Ghi nhận 2 finding cần sửa trước implementation:
  1. Recurrence runtime signature mismatch trong `execute_google_calendar_write()`.
  2. Duplicate CredentialResolver trong `main.py`.

### Decision

- Thêm **Decision 044 — Account Resolver + Account Grant V1: chốt contract trước Multi-account** vào `docs/DECISIONS.md`.

 
## 2026-09-22 — Runtime fixes: Calendar Recurrence + Credential Resolution

Đã sửa và ghi nhận sau khi thay đổi code:

- [`app/api/chat.py`](../app/api/chat.py)
  - `execute_google_calendar_write()` nhận thêm `recurrence`.
  - Giữ validation qua `CalendarRecurrenceService`.
  - `resolve_google_credential()` có thể nhận kết quả CredentialResolver đã resolve để chỉ chuẩn hóa response, không resolve lại.

- [`app/main.py`](../app/main.py)
  - Tái sử dụng `credential_result` cho execution response.
  - Loại bỏ duplicate CredentialResolver trong cùng một request.

- [`tests/unit/api/test_chat_api.py`](../tests/unit/api/test_chat_api.py)
  - Bổ sung regression test cho recurrence.
  - Bổ sung test xác nhận credential result có thể được tái sử dụng mà không cần resolve lần hai.

### Documentation contract

Mọi thay đổi code ở lượt này đã cập nhật Decision Log và Changelog theo nguyên tắc project: **sửa code → cập nhật docs/changelog → mới chuyển sang bước verification**.

### Git commits

- `9348e550b9f191ed9dbb833154835c7e10e01771` — fix recurrence + credential reuse.
- `80485924689608b68091f3cf972ab1889355829c` — remove duplicate credential resolution from main runtime.
- `47994c591ee175576d861846f579be38f6a71e4e` — add regression tests.

 
## 2026-09-22 — Multi-account V1 phase 1 implementation

Đã triển khai contract và authorization boundary:

- `app/application/core_runtime.py`
  - thêm `AccountCandidate`;
  - thêm `ResolvedAccount`;
  - AccountResolver trả về `ResolvedAccount`;
  - AuthorizationService nhận resolved account để enforce grant scope.

- `app/infrastructure/database/repositories/accounts.py`
  - đọc metadata active grant cùng account;
  - phân biệt `owner` / `grant`;
  - không truy cập `account_credentials`.

- `app/infrastructure/database/repositories/permissions.py`
  - owner/grant lifecycle vẫn được kiểm tra ở DB query;
  - grant scope V1 yêu cầu capability hiện tại nằm trong `scope.capabilities`;
  - scope không thay thế user capability permission.

- `app/api/chat.py` + `app/main.py`
  - truyền `ResolvedAccount` nội bộ từ Account Resolver tới Authorization;
  - không đưa object nội bộ vào HTTP response.

- Tests:
  - `tests/application/test_execution_contract.py`;
  - `tests/unit/infrastructure/database/test_postgres_account_repository.py`.

### Documentation rule

Sau thay đổi code đã cập nhật Decision Log và Changelog ngay trong cùng phase. Đây tiếp tục là nguyên tắc bắt buộc: **mọi code change phải cập nhật docs liên quan trước khi chuyển sang verification/phase kế tiếp.**

### Verification status

A01–A04 và A11–A14 đã có test coverage trong repository. A15–A20 chưa đóng cho tới khi chạy runtime/integration side-effect tests.


## 2026-09-22 — Đề xuất Runtime Architecture V2.2

- Review runtime hiện tại của Agent, FastAPI, Scheduling Graph, langgraph.json và Docker infrastructure.
- Xác nhận FastAPI vẫn là HTTP/Application entry hiện tại; LangGraph đã được triển khai thực tế cho Scheduling Assistant; chưa có Unified Agent Super-Graph; chưa có LangGraph Server production; Docker Compose hiện chỉ có Postgres và Qdrant.
- Thêm đề xuất Runtime Architecture V2.2 vào [docs/ARCHITECTURE.md](./ARCHITECTURE.md): FastAPI = HTTP transport boundary; Agent Runtime Entry = application entry cho Agent Run; LangGraph Super-Graph = orchestration cấp Agent; Capability Graph = graph theo capability khi cần; Tool/Provider = action/external API boundary.
- Thêm [Decision 045](./DECISIONS.md) với trạng thái **Proposed — chờ chủ project phê duyệt**.
- Không thay đổi code runtime.
- Không thay đổi Docker Compose.
- Không tạo migration database.
- Không triển khai LangGraph Server.


## 2026-09-22 — Runtime Architecture V2.2 Phase 1: Agent Runtime + Super-Graph

Đã triển khai phase đầu tiên của Decision 045 sau khi chủ project phê duyệt kiến trúc V2.2.

- Thêm [app/agent_runtime/runtime.py](../app/agent_runtime/runtime.py): Agent Runtime Entry, LangGraph Super-Graph tối thiểu, state không chứa credential/secret và dependency injection cho classification/application execution.
- Cập nhật [app/main.py](../app/main.py): `/api/v1/agent/chat` vẫn giữ compatibility endpoint và delegate request vào Agent Runtime; Calendar execution hiện tại chưa bị rewrite để bảo toàn regression baseline.
- Thêm [tests/unit/agent_runtime/test_runtime.py](../tests/unit/agent_runtime/test_runtime.py) kiểm tra routing và secret boundary.
- Thêm [docs/AGENT_RUNTIME_V2_2.md](./AGENT_RUNTIME_V2_2.md) làm tài liệu implementation phase 1.
- Cập nhật [docs/ARCHITECTURE.md](./ARCHITECTURE.md) trạng thái Runtime Architecture V2.2 từ PROPOSED sang ACCEPTED và ghi rõ phase 1.
- Cập nhật [docs/DECISIONS.md](./DECISIONS.md) Decision 045 từ Proposed sang Accepted và ghi implementation phase 1.
- Không thay đổi Docker Compose.
- Không tạo migration database.
- Chưa kết luận PASS runtime/regression trong lượt này; cần verification sau khi pull.


## 2026-09-22 21:16 +07:00 — Sửa regression sau Runtime V2.2 Phase 1 verification

Kết quả verification local của chủ project phát hiện **5 test failure / 87 pass**. Đã xử lý nguyên nhân và đồng bộ test contract:

- `app/api/chat.py`
  - Chuẩn hóa recurrence ở API boundary: chấp nhận cả `RRULE:...` và dạng ngắn `FREQ=...`.
  - Domain `CalendarRecurrenceService` vẫn giữ contract RRULE rõ ràng.
- `app/infrastructure/database/repositories/credentials.py`
  - Giữ `expires_at` timezone-aware trong `CredentialResolution`.
  - Chỉ chuyển expiry sang naive UTC ở boundary của Google Credentials.
  - So sánh expiry theo UTC an toàn cho cả TIMESTAMPTZ aware và giá trị naive.
- `tests/unit/application/test_core_runtime.py`
  - Đồng bộ test với contract mới: `AccountRepository → AccountCandidate → AccountResolver → ResolvedAccount`.
- `tests/unit/infrastructure/database/test_postgres_account_repository.py`
  - Đọc account metadata qua `AccountCandidate.account`.
- `tests/unit/infrastructure/database/test_postgres_credential_repository.py`
  - Đồng bộ test với schema bảo mật hiện hành: `encrypted_value` được Credential Repository đọc sau Authorization để giải mã nội bộ.
  - Test dùng Fernet key/ciphertext giả và không đưa secret vào assertion HTTP.
- Không thay đổi database schema.
- Không tạo migration.
- Không thay đổi Docker Compose.
- Chưa ghi nhận PASS sau patch; cần chủ project chạy lại targeted + regression suite.

### Git commits

- `8a0b5e69e8464ab31b2cbdf0b4b072597a87a0a2` — normalize recurrence input at API boundary.
- `2287e71ed3f1f5d45f7c49cd5c0480a719590cd2` — preserve credential expiry timezone contract.
- `080c1272d5830cd2b13bb7a06cee85c2db1255f1` — update AccountResolver unit contract.
- `78eb849c98fd4225c8696436016f8457edc3962f` — update AccountCandidate repository assertions.
- `ee337393f5b5cc8f9a4b3f6e306a9dff6512ee99` — update encrypted credential repository tests.
- `2b0407bdbf6a37e776bd32e7f3bafa30a3b56b95` — fix timezone-safe credential expiry validation.


## 2026-09-22 — Sửa lỗi syntax trong Credential Repository sau regression patch

- Phát hiện sau khi chủ project `git pull`: `app/infrastructure/database/repositories/credentials.py` có lỗi `IndentationError` tại nhánh `oauth_required`.
- Đã sửa đúng indentation của `return CredentialResolution(status="oauth_required")` bên trong điều kiện expiry.
- Không thay đổi contract credential, database schema, OAuth scope hoặc Docker Compose.
- Chưa ghi nhận PASS sau patch; cần chạy lại targeted + full regression suite.

### Git commit

- `0f2e6a22e39bc53e5c11f5c8d5b5f1f652a671c4` — fix credential repository indentation regression.


## 2026-09-22 — Runtime Architecture V2.2 Phase 2: Capability Routing

Đã triển khai Phase 2 sau khi Phase 1 đạt **92 passed** toàn bộ test suite.

- [app/agent_runtime/runtime.py](../app/agent_runtime/runtime.py)
  - chuyển AgentRuntimeDependencies.execute thành route_handlers;
  - thêm route vào Super-Graph state;
  - thêm node route_request;
  - thêm conditional edges tới handler theo capability;
  - fallback default để giữ compatibility;
  - không có route/default thì trả unsupported_action với provider_called=false.
- [app/main.py](../app/main.py)
  - đăng ký calendar.read và calendar.write vào Super-Graph;
  - giữ Calendar execution hiện tại làm regression baseline;
  - giữ default compatibility handler.
- [tests/unit/agent_runtime/test_runtime.py](../tests/unit/agent_runtime/test_runtime.py)
  - kiểm tra capability route;
  - kiểm tra default route;
  - kiểm tra unsupported route;
  - tiếp tục kiểm tra secret boundary.
- [docs/AGENT_RUNTIME_V2_2.md](./AGENT_RUNTIME_V2_2.md)
  - ghi nhận thiết kế và verification gate Phase 2.
- [docs/ARCHITECTURE.md](./ARCHITECTURE.md)
  - cập nhật runtime flow Phase 2.
- [docs/DECISIONS.md](./DECISIONS.md)
  - thêm Decision 046 về capability routing.

Không thay đổi database schema, migration, Docker Compose hoặc OAuth scope.

**Verification:** chưa ghi nhận PASS trong entry này; cần chạy targeted và full regression sau khi pull.


## 2026-09-22 — Runtime Architecture V2.2 Phase 3: Calendar Application Handler

Đã triển khai Phase 3 theo Decision 047:

- Thêm `app/application/capabilities/calendar.py` với `CalendarHandler`.
- Handler nhận state từ Agent Super-Graph và thực hiện application orchestration:
  - Account Resolver;
  - Authorization;
  - Credential Resolver;
  - Calendar execution;
  - Execution/Error Boundary.
- `app/main.py` được rút gọn thành FastAPI transport + OAuth HTTP flow + Agent Runtime wiring.
- Loại bỏ `_execute_agent_chat()` khỏi FastAPI entry.
- Đăng ký `calendar.read` và `calendar.write` trực tiếp vào `CalendarHandler.handle`.
- Giữ nguyên `POST /api/v1/agent/chat`.
- Không thay đổi database schema/migration, OAuth scope hoặc Docker topology.
- Không rewrite Calendar CRUD, Free/Busy, Scheduling hoặc Recurrence.
- Bổ sung `tests/unit/application/test_calendar_handler.py`:
  - kiểm tra thứ tự Application Boundary;
  - kiểm tra Authorization deny không resolve credential/provider;
  - kiểm tra không đưa credential vào Agent state.
- Cập nhật [`docs/AGENT_RUNTIME_V2_2.md`](./AGENT_RUNTIME_V2_2.md), [`docs/ARCHITECTURE.md`](./ARCHITECTURE.md) và [`docs/DECISIONS.md`](./DECISIONS.md) với Decision 047.

### Verification

Chưa chạy local trong lượt GitHub-first này. Sau khi pull cần chạy:

```powershell
python -m pytest tests/unit/application/test_calendar_handler.py tests/unit/agent_runtime -q
python -m pytest -q
```

Baseline trước Phase 3: **94 passed, 2 warnings**.

### Git commits

- `a661c753b625107c92e9a4943c6e52920ee239d8` — add Calendar application handler.
- `b1ded91eafd848b060ab92bad2a8c3da912bccb8` — move Calendar chat orchestration out of FastAPI main.
- `8b060236604354c4109a257e08ef164119b9237b` — preserve handler response metadata.
- `e7c7d90c0007ace72e385936f9d36908527b4c9f` — update Calendar API test monkeypatch boundaries.
- `c78a291ebe1dedc0dc3ebdea8e91824b784ec232` — add Calendar Handler tests.
- `ce144e6d4428d6b02431ba8c5ee6af172edf343f` — isolate credential boundary in Handler test.
- `ae3cafac2a8600f563bedbf991dde41313039e32` — remove unused Runtime state import.


## 2026-09-22 — Sửa 2 regression findings của Calendar Handler Phase 3

Verification local sau khi pull Phase 3 phát hiện 2 vấn đề tương thích:

- `tests/unit/application/test_calendar_handler.py`: assertion cũ mong đợi alias `deny`, trong khi Execution Contract V1 chuẩn hóa thành canonical status `authorization_denied`. Đã đồng bộ test với contract chuẩn.
- `tests/api/test_calendar_natural_language.py`: test cũ vẫn import `_natural_language_calendar_start` từ `app.main`. Phase 3 đã chuyển helper vào `CalendarHandler`; đã giữ compatibility alias tại `app.main` để không phá test/API nội bộ hiện hữu.
- Không thay đổi database schema, OAuth scope hoặc Docker topology.
- Chưa ghi nhận Phase 3 PASS; cần chạy lại targeted tests và full regression sau khi pull các commit sửa lỗi.

### Git commits

- `39919c065d6a16f0eac8d8ba45871ce16fe71a49` — fix Calendar Handler authorization status assertion.
- `fe99b62a08478db205c0fa0491482ceef994f0de` — preserve natural-language Calendar helper compatibility.


## 2026-09-22 — Sửa regression sau verification Calendar Handler Phase 3

Verification local sau khi pull Phase 3 ghi nhận **8 failures / 89 passed**. Nguyên nhân chính là các runtime/API test vẫn mock dependency tại `app.main` sau khi Calendar orchestration đã được chuyển sang `app.application.capabilities.calendar`; một request thiếu context cũng đang để `ValueError` thoát khỏi FastAPI.

Đã sửa trên GitHub:
- `app/application/capabilities/calendar.py`
  - trả HTTP 400 khi request cần runtime authorization nhưng thiếu `X-User-ID` hoặc `X-Organization-ID`;
  - không thay đổi Authorization → Credential → Provider ordering.
- `tests/runtime/test_execution_error_boundary_runtime.py`
  - chuyển monkeypatch sang CalendarHandler application boundary;
  - giữ nguyên 5 nhánh Execution/Error Boundary.
- `tests/unit/api/test_chat_api.py`
  - chuyển mock Account Resolver sang CalendarHandler boundary;
  - giữ regression contract của natural-language scheduling.

Không thay đổi DB schema/migration, OAuth scope, Docker topology hoặc Execution Contract.

**Verification:** cần chạy lại sau khi pull các commit sửa lỗi.

### Git commits

- `fix Calendar Handler missing context HTTP boundary`
- `update runtime tests for Calendar Handler boundaries`
- `update Calendar API runtime mock boundary`


## 2026-09-22 — Gia cố OAuth-required provider boundary sau Phase 3 verification

Verification local sau các regression fix:
- targeted Calendar Handler + Agent Runtime: **6 passed**;
- full regression: **1 failed, 96 passed, 2 warnings**.

Failure duy nhất:
- `tests/runtime/test_execution_error_boundary_runtime.py::test_runtime_oauth_required_error_boundary`;
- `credential.status = oauth_required` nhưng `credential.provider_called = true`.

Đã sửa `app/application/capabilities/calendar.py` để nhánh credential chưa `ready` luôn kết thúc trước Calendar execution và giữ:
- `execution.credential.provider_called = false`;
- `execution.provider_called = false`.

Đây là hardening đúng theo Execution/Error Boundary: `oauth_required` là pre-provider error.

Không thay đổi DB schema/migration, OAuth scope, Docker topology hoặc Execution Contract semantics.

**Verification:** chưa PASS; cần pull commit mới và chạy lại targeted + full regression.

### Git commit

- `851473cdaacb635a8d442bbaf5be3d7ecfcd1f5a` — fix OAuth-required provider boundary in Calendar Handler.


## 2026-09-22 — Hardening lần 2: cô lập credential provider_called cho oauth_required

Local verification sau commit trước vẫn còn 1 failure: `oauth_required` trả `execution.credential.provider_called = true` dù handler đã dừng trước provider. Đã gia cố bằng cách tạo dict credential mới khi nhánh pre-provider kết thúc, tránh mọi alias/reference có thể làm thay đổi cờ `provider_called` sau phép gán.

**Trạng thái:** chờ verification local lại. Chưa đóng Phase 3.


## 2026-09-22 — Sửa root cause test boundary của OAuth-required

Sau khi chạy lại targeted test, failure vẫn còn. Đã trace dependency boundary và xác định test helper mock sai symbol `CredentialResolver`.

Chi tiết:
- Handler dùng `CredentialResolver` đã import tại `app.application.capabilities.calendar`;
- test helper trước đó mock `app.application.core_runtime.CredentialResolver`;
- vì mock không tác động tới symbol đã import, Handler vẫn có thể nhận `credential_result.status=ready` nội bộ dù response adapter bị mock thành `oauth_required`;
- Handler tiếp tục Calendar execution và cờ `provider_called` bị propagate thành `true`.

Đã cập nhật `tests/runtime/test_execution_error_boundary_runtime.py` để mock đúng `app.application.capabilities.calendar.CredentialResolver`.

**Commit:** `a8b242e09417413930b316a1a1f11f914f24aefe` — `fix Calendar Handler credential resolver test boundary`

**Trạng thái:** chờ verification local targeted + full regression; chưa đóng Phase 3.

## 2026-09-22 — Phase 3 CLOSED / VERIFIED

Verification cuối:
- targeted Calendar Handler + Agent Runtime: **6 passed**;
- full regression: **97 passed, 0 failed, 2 warnings**;
- OAuth-required boundary PASS sau khi sửa test mock đúng `app.application.capabilities.calendar.CredentialResolver`.

Phase 3 hoàn tất. Không có DB migration, OAuth scope hoặc Docker topology thay đổi trong phase này.

**Next phase:** E2E natural-language Agent tests với Google Calendar thật, theo đúng flow Runtime → LangGraph → CalendarHandler → Account → Authorization → Credential → Calendar Tool → Google Calendar.


## 2026-09-22 — Phase 4A: E2E Agent + Google Calendar real provider

Đã mở Phase 4 sau khi Phase 3 CLOSED / VERIFIED.

- Thêm [tests/e2e/test_calendar_agent_google.py](../tests/e2e/test_calendar_agent_google.py).
- E2E chạy opt-in bằng `RUN_GOOGLE_CALENDAR_E2E=1`; không ảnh hưởng regression mặc định.
- Kiểm tra create/read/delete qua Agent Runtime và Google Calendar thật.
- Kiểm tra delete chưa confirmation không gọi provider.
- Dùng `WORKSPACE_E2E_USER_ID`, `WORKSPACE_E2E_ORGANIZATION_ID`, tùy chọn `WORKSPACE_E2E_ACCOUNT_HINT`.
- Không đưa credential secret vào test.
- Chưa kết luận Phase 4 PASS; cần chủ project pull và chạy E2E với account Google đã có credential hợp lệ.

### Git commit

- `fe18a852062023e7dbfa340e1f65bfd38265f9f0` — `test: add opt-in Google Calendar Agent E2E baseline`

### Next verification

```powershell
python -m pytest tests/e2e/test_calendar_agent_google.py -q
python -m pytest -q
```

Nếu E2E PASS, phase tiếp theo là bổ sung test/implementation cho natural-language extraction đầy đủ thay vì suy luận rằng parser hiện tại đã hỗ trợ toàn bộ câu tự nhiên.
