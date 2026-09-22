# CHANGELOG_03.md

> Changelog tiếp theo của `docs/CHANGELOG_02.md`.
>
> Quy tắc: changelog chỉ ghi trạng thái đã được triển khai/kiểm tra; không ghi `PASS` nếu chưa có runtime verification.

## 2026-09-21 — Google OAuth scope consistency

- Sửa `app/infrastructure/oauth/google.py` để lưu bộ scope thực tế của từng phiên OAuth vào OAuth state đã mã hóa.
- Callback không còn tự dựng một bộ scope Calendar cố định khác với authorization request.
- Callback dựng lại `Flow` bằng chính bộ scope đã lưu trong state trước khi gọi `fetch_token(code=code)`.
- Tiếp tục giữ `code_verifier` PKCE trong state mã hóa và ký HMAC.
- Scope thực tế Google trả về sau token exchange tiếp tục được lưu trong `account_credentials.scopes`.
- Xác định warning `Scope has changed` không phải dấu hiệu cần thay `credentials.json`; nguyên nhân chính là authorization request và callback trước đây có thể dùng bộ scope khác nhau.
- Không thay đổi thiết kế credential encryption và không lưu token plaintext vào repository.
- Đồng bộ `docs/CONFIGURATION.md` và `docs/GOOGLE_CALENDAR.md` với implementation.

## 2026-09-21 — Google OAuth PKCE callback fix

- Sửa `app/infrastructure/oauth/google.py` để tạo `code_verifier` PKCE chủ động cho từng phiên OAuth.
- `code_verifier` được đưa vào OAuth state, nhưng state được mã hóa bằng Fernet và ký HMAC nên verifier không xuất hiện plaintext trong URL.
- OAuth start gửi `code_challenge` S256 tới Google.
- OAuth callback xác minh state, giải mã state, khôi phục đúng `code_verifier` và gán lại cho `Flow` trước khi gọi `fetch_token(code=code)`.
- Nguyên nhân lỗi thực tế đã xác định: Flow ở callback được tạo mới nên PKCE verifier do Flow trước đó tự sinh không còn tồn tại, dẫn tới `InvalidGrantError: (invalid_grant) Missing code verifier`.
- Credential sau OAuth tiếp tục được mã hóa bằng Fernet và lưu vào PostgreSQL `account_credentials`.
- Không lưu access token, refresh token hoặc PKCE verifier vào repository/file runtime.
- Đồng bộ `docs/GOOGLE_CALENDAR.md` với implementation thực tế.
- Không tạo Migration 052.

## 2026-09-21 — Quy tắc ghi chú mã nguồn Python

- Tất cả ghi chú/comment/docstring trong file `.py` phải viết bằng tiếng Việt.
- Khi sửa code Python, không thêm comment/docstring tiếng Anh trừ nội dung bắt buộc của tên thư viện, API hoặc protocol.
- Quy tắc này phải được duy trì trong các lần sửa code tiếp theo và được ghi nhận trong tài liệu/changelog liên quan.

## 2026-09-21 — Google OAuth không mở rộng scope đã cấp trước đó

- Sửa `app/infrastructure/oauth/google.py` để OAuth Calendar không gửi `include_granted_scopes=true`.
- Mục tiêu là tránh Google gộp các scope đã từng cấp cho cùng OAuth client như `drive.readonly` hoặc `gmail.readonly` vào token response của phiên Calendar hiện tại.
- Authorization request vẫn lưu đúng bộ scope của phiên trong state và callback vẫn dùng chính bộ scope đó.
- Không thay đổi `credentials.json`; file này tiếp tục chỉ chứa cấu hình OAuth client.
- Commit: `b57d7ec3a2b23337a12d0269a493be744eb89771`.

## 2026-09-21 — Agent chat phân loại Calendar V1

- Sửa `app/api/chat.py` để `POST /api/v1/agent/chat` không còn dừng mặc định ở `intent=not_classified` khi message có ý định Calendar.
- Thêm bộ phân loại Calendar V1 cho các yêu cầu đọc lịch và nhóm thao tác tạo/sửa/xóa lịch.
- Khi intent Calendar được nhận diện, runtime tự chuyển sang `AccountResolver` ngay cả khi request không truyền `account_hint`.
- Sau khi resolve account, runtime tiếp tục `AuthorizationService` rồi `CredentialResolver` theo đúng thứ tự bảo vệ.
- Request không nhận diện được intent vẫn chỉ trả về contract metadata và không gọi account/provider.

## 2026-09-21 — Sửa lỗi cú pháp Calendar runtime

- Loại bỏ đoạn Calendar runtime bị lặp trong `app/main.py` sau lần nối luồng Agent.
- Lỗi runtime tương ứng: `IndentationError: unexpected indent` tại dòng khởi tạo `ExternalAccount`.

## 2026-09-21 — Calendar provider runtime gate

- Nối CredentialResolver từ readiness sang credential context nội bộ được tạo từ credential OAuth đã mã hóa trong PostgreSQL.
- Thêm CalendarToolRegistry để phân giải Google Calendar tool trước khi gọi provider.
- Nối GoogleCalendarTool → GoogleCalendarAdapter → Google Calendar API v3 cho thao tác đọc danh sách event.
- Với yêu cầu đọc lịch hiện tại, runtime mặc định đọc các event trong ngày theo múi giờ Asia/Ho_Chi_Minh.
- HTTP response chỉ trả metadata credential; không trả access token, refresh token hoặc encrypted credential.

## 2026-09-21 — Chuẩn hóa timezone của Google OAuth credential

- Chuẩn hóa `expires_at` từ PostgreSQL sang datetime phù hợp với biên Google Auth.
- Sửa lỗi runtime `can't compare offset-naive and offset-aware datetimes`.
- Không thay đổi token, scope hoặc thiết kế mã hóa credential.

## 2026-09-21 — Chốt chuẩn UTC cho toàn bộ thời gian Database và sửa UTF-8 API

- Chốt nguyên tắc: mọi timestamp lưu trong PostgreSQL dùng UTC; không lưu giờ GMT+7 trong database.
- Khi đọc/hiển thị cho người dùng hoặc API, application/presentation layer chuyển UTC sang `Asia/Ho_Chi_Minh` (GMT+7).
- Thời gian nhận từ người dùng phải được chuẩn hóa về UTC trước khi ghi database.
- Provider có thể dùng timezone riêng theo API contract nhưng không làm thay đổi chuẩn UTC của database.
- Sửa `POST /api/v1/agent/chat` trả JSON với `application/json; charset=utf-8`.

## 2026-09-21 — Tạo utility thời gian dùng chung

- Thêm `app/core/datetime.py` với `utc_now()`, `to_utc()` và `to_vietnam_time()`.
- `to_utc()` và `to_vietnam_time()` từ chối datetime không có timezone.
- Calendar và các domain mới về sau phải dùng utility này thay vì tự xử lý timezone riêng.

## 2026-09-21 — Calendar Read V1 CLOSED

- Đã runtime verification thực tế qua `POST /api/v1/agent/chat` với yêu cầu đọc lịch.
- Classification `calendar.read` đúng; AccountResolver, Authorization, CredentialResolver và ToolResolver đều đi đúng thứ tự.
- Google Calendar API v3 được gọi thực tế và trả về 2 event.
- HTTP UTF-8 hiển thị đúng tiếng Việt.
- Khung thời gian đọc dùng `Asia/Ho_Chi_Minh` và tuân thủ chuẩn UTC của database.
- Đánh dấu **Calendar Read V1 — CLOSED / E2E PASS**.
- Phase tiếp theo tách riêng: Calendar Write V1 và Calendar webhook/push sync.

## 2026-09-21 — Calendar Write V1 runtime implementation

- Thêm `execute_google_calendar_write()` vào `app/api/chat.py`.
- Nối `calendar.write` qua AccountResolver → AuthorizationService → CredentialResolver → CalendarToolRegistry → GoogleCalendarTool → GoogleCalendarAdapter.
- Hỗ trợ `create`, `update`, `delete` event.
- Create yêu cầu `summary`, `start`, `end`.
- Update yêu cầu `event_id` và patch các field được truyền vào.
- Delete yêu cầu `event_id` và `confirmed=true`; nếu chưa xác nhận thì trả `confirmation_required` và không gọi provider.
- Datetime Calendar Write bắt buộc có timezone/UTC và được chuẩn hóa về UTC trước khi gửi Google.
- Cập nhật `POST /api/v1/agent/chat` để nhận `event_id`, `summary`, `start`, `end`, `description`, `location`, `confirmed`.
- Cập nhật `docs/GOOGLE_CALENDAR.md` với contract Calendar Write V1 và nguyên tắc UTC/GMT+7.
- **Chưa đánh dấu E2E PASS**; cần chạy Create/Update/Delete trên Google Calendar thật.

## 2026-09-21 — Chốt runbook Google OAuth

- Thêm `docs/GOOGLE_OAUTH.md` làm tài liệu thao tác chuẩn cho toàn bộ quy trình Google OAuth.
- Runbook ghi rõ cách lấy `user_id`, `organization_id`, xác định `account_id`, chọn capability, tạo OAuth URL, hoàn tất callback và kiểm tra scope.
- Ghi rõ `x-user-id` và `x-organization-id` là HTTP headers, không phải biến môi trường.
- Ghi rõ cách dùng `curl.exe` trên PowerShell để lấy redirect URL khi `Invoke-WebRequest` bị chặn HTML parsing.
- Ghi nhận xác nhận thực tế ngày 2026-09-21: Google OAuth với `calendar.write` đã trả callback thành công.
- Liên kết `docs/GOOGLE_CALENDAR.md` với runbook OAuth chuẩn.
- Từ nay khi cần OAuth lại, mở `docs/GOOGLE_OAUTH.md` và thực hiện theo từng bước trong tài liệu.

## 2026-09-21 — Chuẩn bị E2E Calendar Write

- Thêm validation datetime trước khi gọi Google Calendar provider.
- Datetime sai định dạng hoặc thiếu timezone trả `validation_error` và `provider_called=false`, không bị báo nhầm thành lỗi provider.
- Chuyển các docstring/comment tiếng Anh còn lại trong Calendar adapter sang tiếng Việt theo quy tắc mã nguồn Python của dự án.
- Chưa đánh dấu Calendar Write E2E PASS; chờ kiểm tra Create/Update/Delete trên Google Calendar thật.

## 2026-09-22 — Bảo vệ UTF-8 cho Calendar Write

- Thêm lớp bảo vệ `_repair_mojibake()` trước khi gửi `summary`, `description` và `location` tới Google Calendar.
- Chỉ khôi phục các chuỗi có dấu hiệu mojibake phổ biến; chuỗi Unicode tiếng Việt bình thường được giữ nguyên.
- Mục tiêu là tránh trường hợp client Windows/PowerShell làm sai encoding trước khi text đi vào Google Calendar.
- Chưa đánh dấu Calendar Write E2E PASS; cần tạo event tiếng Việt thật và kiểm tra trực tiếp trên Google Calendar.


## 2026-09-22 — Sửa CredentialResolver cho OAuth credential có thể refresh

- Xác định nguyên nhân Calendar Write trả `oauth_required` dù account có credential `active`: truy vấn credential trước đây loại bỏ mọi row có `expires_at` đã qua.
- Sửa `PostgresCredentialRepository` để vẫn lấy credential `status=active` khi access token đã hết hạn.
- Nếu credential còn `refresh_token`, trả `ready` để Google Auth có thể refresh access token khi provider được gọi.
- Nếu credential đã hết hạn nhưng không còn `refresh_token`, mới trả `oauth_required`.
- Không thay đổi encrypted credential, OAuth scope hoặc database schema.
- Chưa đánh dấu Calendar Write E2E PASS; cần chạy lại request Create UTF-8 sau khi restart server.


## 2026-09-22 — Chuẩn hóa timezone response Calendar Write

- Sửa response Calendar Write để chuyển `start` và `end` từ UTC của Google Calendar sang `Asia/Ho_Chi_Minh` / GMT+7.
- Response đặt `timeZone=Asia/Ho_Chi_Minh` để `dateTime` và timezone metadata nhất quán.
- Không thay đổi nguyên tắc database lưu UTC hoặc payload gửi Google Calendar.
- Cần test lại Create với event mới; không dùng lại event đã tạo trước khi sửa.


## 2026-09-22 — Calendar Write V1 CLOSED / E2E PASS

- Đã kiểm chứng thực tế Calendar Write V1 với Google Calendar thật qua `POST /api/v1/agent/chat`.
- Create event — **PASS**: tạo event `p85pvng0r6fmnacg8bfm8lhesg` thành công.
- Update event — **PASS**: cập nhật đúng event theo `event_id`, bao gồm nội dung tiếng Việt và thời gian GMT+7.
- Delete chưa xác nhận — **PASS**: trả `confirmation_required` và `provider_called=false`, không gọi Google Calendar.
- Delete có `confirmed=true` — **PASS**: Google Calendar được gọi và xóa đúng event `p85pvng0r6fmnacg8bfm8lhesg`.
- AccountResolver, Authorization, CredentialResolver và provider boundary đều hoạt động đúng trong các E2E Write.
- Response `start/end` nhất quán với `Asia/Ho_Chi_Minh` / GMT+7; chuẩn UTC nội bộ không thay đổi.
- UTF-8 tiếng Việt được kiểm chứng qua Create/Update.
- Đóng acceptance **Calendar Write V1 — CLOSED / E2E PASS**.
- Provider error/rollback acceptance và Calendar webhook/push sync vẫn để phase sau; chưa đánh dấu PASS.
