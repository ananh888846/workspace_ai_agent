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
