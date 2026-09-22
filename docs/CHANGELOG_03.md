# CHANGELOG_03.md

> Changelog tiếp theo của `docs/CHANGELOG_02.md`.
>
> Quy tắc: changelog chỉ ghi trạng thái đã được triển khai/kiểm tra; không ghi `PASS` nếu chưa có runtime verification.

## 2026-09-22 — Chốt nguyên tắc Calendar Intelligence và triển khai Natural Language Date/Time V1

- Cập nhật [`docs/ARCHITECTURE.md`](./ARCHITECTURE.md): chốt Calendar Service là tầng domain độc lập; LangGraph chỉ là Super-Graph ở tầng trên cùng.
- Cập nhật [`docs/DECISIONS.md`](./DECISIONS.md): thêm **Decision 035 — Calendar Natural Language Date/Time dùng Python thuần**.
- Cập nhật [`docs/GOOGLE_CALENDAR.md`](./GOOGLE_CALENDAR.md): ghi rõ phạm vi, boundary và trạng thái Calendar Natural Language Date/Time V1.
- Thêm [`app/services/calendar_datetime.py`](../app/services/calendar_datetime.py): parser ngày giờ tự nhiên tiếng Việt bằng Python thuần, không Pydantic, không LangGraph.
- Thêm [`tests/services/test_calendar_datetime.py`](../tests/services/test_calendar_datetime.py): test cho ngày mai, thứ tuần sau, thời gian tương đối, buổi chiều, ngày cụ thể và validation reference.
- Chưa tích hợp parser vào Calendar CRUD request flow; do đó chưa đánh dấu E2E Calendar Natural Language là PASS.
- Không thay đổi Calendar CRUD V1; CRUD V1 tiếp tục là regression baseline.

## 2026-09-22 — Chốt lại Framework toàn project: chỉ LangGraph + Pydantic có chọn lọc

- Cập nhật [`docs/ARCHITECTURE.md`](./ARCHITECTURE.md): **LangGraph là framework orchestration duy nhất** của project.
- Cập nhật [`docs/ARCHITECTURE.md`](./ARCHITECTURE.md): xác nhận **LangChain và CrewAI không được dùng** làm dependency, abstraction layer, agent runtime hoặc orchestration framework.
- Cập nhật [`docs/DECISIONS.md`](./DECISIONS.md): sửa Decision 012 thành **Rejected / Superseded**, ghi rõ LangChain + CrewAI bị loại khỏi kiến trúc.
- Cập nhật [`docs/DECISIONS.md`](./DECISIONS.md): thêm **Decision 034 — Chủ project phải chốt trước khi dùng LangGraph/Pydantic cho phần mới**.
- Quy tắc mới: trước mỗi lần triển khai phần mới có quyết định kỹ thuật trực tiếp về LangGraph hoặc Pydantic, phải hỏi ý kiến chủ project.
- Nếu phát hiện framework/phương án tốt hơn, phải đề xuất và so sánh trước; chỉ triển khai sau khi chủ project chốt.
- Pydantic tiếp tục chỉ dùng chọn lọc tại các boundary thực sự cần validation, normalization, serialization hoặc contract ổn định.
- Không thực hiện runtime migration trong thay đổi này; đây là **architecture/documentation decision**, chưa đánh dấu runtime LangGraph migration là PASS.
- Kiểm tra GitHub code search với `LangChain`, `CrewAI` và `langchain` trong repository không trả về kết quả code/document hiện hành ngoài Decision lịch sử đã được cập nhật.

## 2026-09-22 — Chốt LangGraph và Pydantic selective contracts

- Cập nhật [`docs/ARCHITECTURE.md`](./ARCHITECTURE.md): chốt **LangGraph** là framework orchestration chuẩn cho Agent Runtime production toàn project.
- Cập nhật [`docs/DECISIONS.md`](./DECISIONS.md): thêm **Decision 031 — LangGraph as Production Agent Orchestrator**.
- Cập nhật [`docs/DECISIONS.md`](./DECISIONS.md): thêm **Decision 032 — Pydantic Selective Tool Contracts**.
- LangGraph chịu trách nhiệm graph state, routing, control flow, retry/interrupt/resume khi cần; không sở hữu Authorization, Credential hoặc Provider business logic.
- Pydantic chỉ dùng khi data boundary thực sự cần validation, normalization, serialization hoặc contract ổn định.
- Không bắt buộc tạo Pydantic model cho mọi Tool/helper; tránh over-engineering.
- Quyết định này mới ở mức **architecture/documentation accepted**; chưa đánh dấu runtime migration sang LangGraph là PASS.
- Calendar CRUD V1 tiếp tục được giữ nguyên làm regression baseline trong quá trình migrate từng capability.
- Chưa triển khai Calendar Intelligence, Free/Busy, Scheduling Assistant, Recurrence hoặc Multi-account Calendar.

## 2026-09-21 — Google OAuth scope consistency

- Sửa `app/infrastructure/oauth/google.py` để lưu bộ scope thực tế của từng phiên OAuth vào OAuth state đã mã hóa.
- Callback không còn tự dựng một bộ scope Calendar cố định khác với authorization request.
- Callback dựng lại `Flow` bằng chính bộ scope đã lưu trong state trước khi gọi `fetch_token(code=code)`.
- Tiếp tục giữ `code_verifier` PKCE trong state mã hóa và ký HMAC.
- Scope thực tế Google trả về sau token exchange tiếp tục được lưu trong `account_credentials.scopes`.
- Xác định warning `Scope has changed` không phải dấu hiệu cần thay `credentials.json`; nguyên nhân chính là authorization request và callback trước đây có thể dùng bộ scope khác nhau.
- Không thay đổi thiết kế credential encryption và không lưu token plaintext vào repository.
- Đồng bộ `docs/CONFIGURATION.md` và `docs/GOOGLE_CALENDAR.md` với implementation.

