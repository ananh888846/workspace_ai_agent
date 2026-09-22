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
