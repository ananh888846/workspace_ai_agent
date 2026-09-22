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

### Commit

- `900105f25e34a57f907f0c680f7cdc30f2f2cab6` — wire Execution Contract vào Agent Chat Runtime.
