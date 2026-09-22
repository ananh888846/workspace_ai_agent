# CHANGELOG_04.md

> Changelog tiếp theo của `docs/CHANGELOG_03.md`.
>
> Quy tắc: chỉ ghi trạng thái đã được triển khai/kiểm tra; không ghi `PASS` nếu chưa có runtime verification.
>
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
- Chưa thay đổi hành vi Calendar V1; contract mới được triển khai độc lập để làm nền cho bước wiring vào runtime.
- Chưa đánh dấu runtime PASS; cần chạy test suite local sau khi pull.
