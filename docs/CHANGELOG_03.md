## 2026-09-22 — Sửa expectation Calendar Read local timezone\n\n- Runtime test xác nhận provider boundary nhận UTC đúng: `2026-09-24T00:00:00+07:00` → `2026-09-23T17:00:00+00:00`.\n- Sửa expectation `requested_start/requested_end` trong `tests/unit/api/test_chat_api.py`: response giữ nguyên thời gian local GMT+7, không cộng thêm 7 giờ.\n- Không thay đổi production logic.\n- Lần chạy vừa rồi: **17/18 PASSED, 1 FAILED**; failure chỉ do expectation của test không khớp contract local-time response.\n- Chưa đánh dấu E2E PASS.\n\n## 2026-09-22 — Sửa expectation test Calendar Read theo UTC normalization

- Runtime test phát hiện implementation đã chuyển đúng `2026-09-24T00:00:00+07:00` thành `2026-09-23T17:00:00+00:00` trước khi gọi provider.
- Sửa expectation trong `tests/unit/api/test_chat_api.py` để phản ánh contract hiện tại: request local GMT+7 được normalize sang UTC ở provider boundary.
- Đây là **test fix**, không thay đổi logic Calendar Read.
- Lần chạy trước: **17/18 PASSED, 1 FAILED** do expectation của test sai múi giờ.
- Chưa đánh dấu E2E PASS.

## 2026-09-22 — Calendar Read V1 hỗ trợ khoảng thời gian request

- Sửa [app/api/chat.py](../app/api/chat.py): Calendar Read không còn luôn cố định vào ngày hiện tại.
- Có cả `start` và `end`: provider được gọi đúng khoảng thời gian request.
- Chỉ có `start`: đọc một ngày kể từ `start`; chỉ có `end`: đọc một ngày kết thúc tại `end`.
- Không có `start/end`: giữ fallback hôm nay → ngày mai để bảo toàn hành vi cũ.
- Sửa [app/main.py](../app/main.py): truyền `payload.start` và `payload.end` vào Calendar Read.
- Bổ sung unit tests cho explicit range, start-only fallback và invalid range.
- Không thay đổi LangGraph, Pydantic, OAuth scope, database schema hoặc provider boundary.
- Đây là code + test update; chưa đánh dấu E2E PASS cho việc đối chiếu Events API với Free/Busy.

## 2026-09-22 — Sửa lỗi runtime/unit sau khi cài LangGraph

- Runtime verification local với Python 3.14.7 và pytest 8.4.2 đã phát hiện **5/14 tests FAILED** trong Scheduling Assistant V1 + runtime wiring.
- Sửa [app/services/scheduling.py](../app/services/scheduling.py): mỗi khoảng trống đủ dài nay sinh toàn bộ các slot liên tiếp theo `duration_minutes`, thay vì chỉ sinh một slot đầu tiên của mỗi khoảng.
- Sửa [app/main.py](../app/main.py): khi request có runtime context như `account_hint`, account vẫn được resolve trước khi kiểm tra có phải Calendar capability hay không; điều này giữ đúng contract runtime account resolution.
- Sửa [tests/unit/api/test_chat_api.py](../tests/unit/api/test_chat_api.py): fixture authorization dùng UUID hợp lệ thay vì giá trị `acc-1`, tránh lỗi PostgreSQL UUID khi đi qua CredentialResolver thật.
- Đây là **code fix sau test failure**, chưa đánh dấu Scheduling Assistant V1 PASS/CLOSED.
- Cần pull các commit mới và chạy lại toàn bộ test suite đã nêu trước khi tiếp tục E2E Google Calendar.

## 2026-09-22 — Sửa classification Scheduling Assistant V1

- Cập nhật [app/api/chat.py](../app/api/chat.py): nhận dạng các câu như tìm thời gian/tìm giờ/khung giờ ngay cả khi câu không chứa từ lịch.
- Giữ nguyên ưu tiên loại trừ Calendar Write để không route yêu cầu tạo/sửa/xóa sang Scheduling Assistant.
- Chưa runtime verify; cần chạy test classification và Scheduling Graph sau khi pull.

## 2026-09-22 — Triển khai Scheduling Assistant V1: SchedulingService + LangGraph Graph

- Thêm [app/services/scheduling.py](../app/services/scheduling.py): thuật toán deterministic tìm available slots từ Free/Busy.
- Thêm [app/graphs/scheduling.py](../app/graphs/scheduling.py): Scheduling Graph V1 bằng LangGraph với các node classify_request, resolve_calendar, get_free_busy, find_available_slots, format_result.
- Thêm [tests/services/test_scheduling.py](../tests/services/test_scheduling.py): unit test validation, busy boundary, merge busy và tìm slot.
- Thêm [tests/unit/graphs/test_scheduling.py](../tests/unit/graphs/test_scheduling.py): kiểm thử Graph orchestration và dependency injection.
- Cập nhật [app/api/chat.py](../app/api/chat.py): route scheduling qua Graph sau Authorization + CredentialResolver và tái sử dụng Calendar Free/Busy.
- Cập nhật [app/main.py](../app/main.py): thêm search_start, search_end, duration_minutes, max_results.
- Cập nhật [requirements.txt](../requirements.txt): thêm dependency LangGraph.
- Cập nhật [tests/unit/api/test_chat_api.py](../tests/unit/api/test_chat_api.py): kiểm thử classification cho Scheduling request.
- Chưa đánh dấu runtime PASS hoặc E2E PASS; cần pull code, cài dependency và chạy test/runtime verification trên môi trường local.
- Không tạo database migration.
- Không thêm Pydantic contract mới cho Scheduling Graph.

## 2026-09-22 — Chốt thiết kế Scheduling Assistant V1

- Chủ project đã chốt thiết kế Scheduling Assistant V1 theo mô hình **LangGraph orchestration + Domain Service độc lập + Tool boundary + Provider**.
- Cập nhật [docs/DECISIONS.md](./DECISIONS.md): thêm **Decision 041 — Scheduling Assistant V1**.
- Cập nhật [docs/ARCHITECTURE.md](./ARCHITECTURE.md): bổ sung graph flow, state và boundary rules cho Scheduling Assistant V1.
- Cập nhật [docs/GOOGLE_CALENDAR.md](./GOOGLE_CALENDAR.md): bổ sung thiết kế Scheduling Assistant V1.
- Thêm [docs/SCHEDULING_ASSISTANT_V1.md](./SCHEDULING_ASSISTANT_V1.md): đặc tả thiết kế V1 trước khi triển khai code.
- V1 chưa tạo migration database và chưa có side effect tạo/sửa/xóa event.
- Chưa đánh dấu runtime PASS; đây là **architecture/design accepted**, chưa phải implementation verification.


## 2026-09-22 — Calendar Free/Busy + Conflict Detection V1 CLOSED / E2E PASS

- Runtime E2E hoàn tất với Google Calendar thật trên account `ananh888846@gmail.com`.
- Create event test `TEST FreeBusy V1`: **PASS**, event `10krafu0fd8629bb41hpantv9o`, `14:00–15:00` GMT+7.
- FreeBusy `13:00–16:00`: **PASS / conflict**, Google trả busy `14:00–15:00`.
- FreeBusy `14:30–15:30`: **PASS / conflict**.
- Boundary `15:00–16:00`: **PASS / free**; khoảng bắt đầu đúng lúc busy kết thúc không bị coi là overlap.
- Delete event test: **PASS**, Google Calendar xóa thành công event `10krafu0fd8629bb41hpantv9o`.
- Runtime đi qua AccountResolver → AuthorizationService → CredentialResolver → CalendarToolRegistry → GoogleCalendarTool → GoogleCalendarAdapter → Google Calendar API `freeBusy.query` → CalendarConflictDetector.
- Xác nhận `provider_called=true`, timezone `Asia/Ho_Chi_Minh`, OAuth scope hiện tại không đổi và không cần migration database.
- ConflictDetector unit tests trước E2E: **5/5 PASSED**.
- Cập nhật [`docs/GOOGLE_CALENDAR.md`](./GOOGLE_CALENDAR.md), [`docs/ARCHITECTURE.md`](./ARCHITECTURE.md) và [`docs/DECISIONS.md`](./DECISIONS.md).
- Event test đã được xóa sau verification; không để lại dữ liệu test trên Google Calendar.

## 2026-09-22 — E2E đóng Calendar Natural Language Date/Time V1

- Runtime verification hoàn tất với Google Calendar thật trên account `ananh888846@gmail.com`.
- Natural Language Create: **PASS** với câu `Tạo lịch họp ngày 24/09/2026 lúc 09:00`.
- Parser resolve đúng `2026-09-24T09:00:00+07:00`, timezone `Asia/Ho_Chi_Minh` và Google tạo event thật `vet0dr4i57cobksqmbpgol2jb4`.
- Natural Language Update: **PASS** với câu `Cập nhật lịch E2E ngày 24/09/2026 lúc 14:00`; event được cập nhật thành `14:00–15:00` GMT+7.
- Delete safety: **PASS** với `confirmed=false`; trả `confirmation_required` và `provider_called=false`.
- Delete thật: **PASS** với `confirmed=true`; Google Calendar xóa thành công event test.
- Combined parser + integration tests trước E2E: **13/13 PASSED**.
- Cập nhật [`docs/GOOGLE_CALENDAR.md`](./GOOGLE_CALENDAR.md): Natural Language Date/Time V1 **CLOSED / E2E PASS**.
- Cập nhật [`docs/DECISIONS.md`](./DECISIONS.md): thêm **Decision 036 — Calendar Natural Language Date/Time V1 E2E baseline**.
- Event test đã được xóa sau verification; không để lại dữ liệu test trên Google Calendar.

## 2026-09-23 — Runtime verification: Calendar Natural Language integration PASS

- Đã runtime verification trên Windows với Python 3.14.7 và pytest 8.4.2.
- Chạy `python -m pytest tests/services/test_calendar_datetime.py tests/api/test_calendar_natural_language.py -v`.
- Kết quả: **13/13 tests PASSED**, thời gian chạy 0.84 giây.
- Xác nhận parser V1 và integration helper cùng hoạt động.
- Đã xác nhận `payload.start` tường minh được ưu tiên và message không có datetime không bị tự đoán.
- **Calendar Natural Language Date/Time integration — TEST PASS.**
- Đây vẫn là unit/integration-level verification; chưa phải E2E với Google Calendar thật.
## 2026-09-23 — Tích hợp Natural Language Date/Time vào Calendar Write

- Cập nhật [`app/main.py`](../app/main.py): khi Calendar Write không có `start`, runtime thử chuẩn hóa `start` từ `payload.message` bằng `CalendarDateTimeParser`.
- `payload.start` tường minh luôn được ưu tiên; nếu không parse được câu ngày/giờ thì không tự đoán và Calendar Write tiếp tục trả validation error.
- V1 chỉ tự chuẩn hóa `start`; `end` vẫn phải truyền rõ bằng ISO-8601 có timezone để tránh tự suy đoán thời lượng.
- Thêm [`tests/api/test_calendar_natural_language.py`](../tests/api/test_calendar_natural_language.py): kiểm thử ngày mai lúc 9h, ngày cụ thể + giờ, ưu tiên start tường minh và message không có datetime.
- Cập nhật [`docs/GOOGLE_CALENDAR.md`](./GOOGLE_CALENDAR.md) để ghi rõ boundary và trạng thái tích hợp.
- Chưa đánh dấu E2E Natural Language Create/Update PASS; cần runtime verification local và sau đó mới kiểm thử Google Calendar thật.
# CHANGELOG_03.md

> Changelog tiếp theo của `docs/CHANGELOG_02.md`.
>
> Quy tắc: changelog chỉ ghi trạng thái đã được triển khai/kiểm tra; không ghi `PASS` nếu chưa có runtime verification.

## 2026-09-23 — Runtime verification: Calendar Natural Language Date/Time V1 PASS

- Đã runtime verification trên môi trường local Windows với Python 3.14.7 và pytest 8.4.2.
- Chạy `python -m pytest tests/services/test_calendar_datetime.py -v`.
- Kết quả: **9/9 tests PASSED**, thời gian chạy 0.06 giây.
- Đã xác nhận các nhóm xử lý:
  - ngày mai lúc 9 giờ;
  - thứ sáu tuần sau lúc 14:30;
  - thời gian tương đối `2 tiếng nữa`;
  - buổi chiều `2h chiều`;
  - ngày cụ thể `24/09/2026 lúc 08:30`;
  - giờ dạng `HH:MM`;
  - giờ dạng `HHhMM`;
  - từ chối reference datetime không có timezone;
  - từ chối biểu thức ngày giờ rỗng.
- **Calendar Natural Language Date/Time V1 — TEST PASS.**
- Đây là unit/service-level verification; chưa phải E2E tích hợp parser vào Calendar CRUD request flow.

## 2026-09-22 — Sửa Calendar Natural Language Date/Time V1: nhận dạng giờ có dấu hai chấm

- Sửa [`app/services/calendar_datetime.py`](../app/services/calendar_datetime.py): parser nhận dạng các dạng giờ `HH:MM` và `HHhMM`, đồng thời tiếp tục hỗ trợ giờ đơn như `9h` hoặc `9 giờ` sau bước normalize.
- Bổ sung [`tests/services/test_calendar_datetime.py`](../tests/services/test_calendar_datetime.py): kiểm thử riêng cho `08:30` và `14h30`.
- Lỗi trước đó: `14:30` và `08:30` không khớp regex nên parser rơi về giờ mặc định `09:00`.
- Chưa đánh dấu runtime PASS; cần chạy lại pytest trên môi trường local sau khi pull.

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



## 2026-09-22 — Bắt đầu triển khai Calendar Free/Busy + Conflict Detection V1

- Chốt Decision 037: Free/Busy V1 không dùng Pydantic.
- Chốt Decision 038: giữ OAuth scope Calendar hiện tại và dùng capability calendar.read với action free_busy.
- Chốt Decision 039: ưu tiên API/SDK chính thức của provider trước thư viện bên thứ ba.
- Thêm [app/services/calendar_free_busy.py](../app/services/calendar_free_busy.py): BusyPeriod, Conflict, ConflictResult và ConflictDetector thuần Python.
- Mở rộng [app/providers/google/calendar/adapter.py](../app/providers/google/calendar/adapter.py) với Google Calendar freeBusy.query.
- Mở rộng [app/tools/calendar.py](../app/tools/calendar.py) và [app/tools/registry.py](../app/tools/registry.py) với action free_busy.
- Mở rộng [app/api/chat.py](../app/api/chat.py) để lấy Free/Busy và kiểm tra conflict.
- Mở rộng [app/main.py](../app/main.py) để route calendar.read/free_busy.
- Thêm [tests/services/test_calendar_free_busy.py](../tests/services/test_calendar_free_busy.py).
- Cập nhật [docs/GOOGLE_CALENDAR.md](./GOOGLE_CALENDAR.md) và [docs/DECISIONS.md](./DECISIONS.md).
- Đây mới là code + test preparation; **CHƯA runtime verify và CHƯA E2E PASS**.


## 2026-09-22 — Hoàn thiện boundary provider cho Free/Busy

- [app/providers/google/calendar/adapter.py](../app/providers/google/calendar/adapter.py) sử dụng Google Calendar API freeBusy.query thông qua Google Calendar client hiện tại.
- Adapter chuyển lỗi theo từng calendar từ provider thành provider error thay vì coi calendar lỗi là rảnh.
- Đây vẫn là code-level preparation; **CHƯA runtime verify và CHƯA E2E PASS**.


## 2026-09-22 — Chuẩn hóa runtime routing cho Scheduling Assistant V1

- Sửa [app/main.py](../app/main.py): request Calendar đã được phân loại sẽ đi vào runtime AccountResolver/Authorization boundary ngay cả khi client không truyền `capability` hoặc `action` tường minh.
- Ngăn trường hợp câu tự nhiên như `Tìm thời gian trống 1 tiếng ngày mai` bị trả về `not_evaluated` trước khi Scheduling Assistant có cơ hội thực thi.
- Bổ sung [tests/unit/api/test_chat_api.py](../tests/unit/api/test_chat_api.py): xác nhận natural-language scheduling request có context sẽ thực sự đi vào runtime account resolution.
- Không thay đổi LangGraph, Pydantic, OAuth scope, database schema hoặc provider boundary.
- Đây là code fix + test coverage; **CHƯA E2E PASS** với Google Calendar thật.
