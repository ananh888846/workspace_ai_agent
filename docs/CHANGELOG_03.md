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
- Chưa đánh dấu Google Calendar provider E2E PASS; bước gọi Google Calendar API vẫn là gate tiếp theo.

## 2026-09-21 — Sửa lỗi cú pháp Calendar runtime

- Loại bỏ đoạn Calendar runtime bị lặp trong `app/main.py` sau lần nối luồng Agent.
- Lỗi runtime tương ứng: `IndentationError: unexpected indent` tại dòng khởi tạo `ExternalAccount`.
- Chưa thay đổi logic OAuth, AccountResolver, Authorization hoặc CredentialResolver.


## 2026-09-21 — Calendar provider runtime gate

- Nối CredentialResolver từ readiness sang credential context nội bộ được tạo từ credential OAuth đã mã hóa trong PostgreSQL.
- Thêm CalendarToolRegistry để phân giải Google Calendar tool trước khi gọi provider.
- Nối GoogleCalendarTool → GoogleCalendarAdapter → Google Calendar API v3 cho thao tác đọc danh sách event.
- Với yêu cầu đọc lịch hiện tại, runtime mặc định đọc các event trong ngày theo múi giờ Asia/Ho_Chi_Minh.
- HTTP response chỉ trả metadata credential; không trả access token, refresh token hoặc encrypted credential.
- Chưa đánh dấu Calendar E2E PASS; cần chạy lại request thực tế để xác nhận Google Calendar API trả dữ liệu.


## 2026-09-21 — Chuẩn hóa timezone của Google OAuth credential

- Chuẩn hóa `expires_at` từ PostgreSQL sang datetime có timezone UTC trước khi tạo Google `Credentials`.
- Sửa lỗi runtime `can't compare offset-naive and offset-aware datetimes` khi Google Auth kiểm tra thời hạn credential.
- Không thay đổi token, scope hoặc thiết kế mã hóa credential.
- Chưa đánh dấu Calendar E2E PASS; cần chạy lại request đọc lịch sau khi pull code.


## 2026-09-21 — Chuẩn hóa expiry theo yêu cầu Google Auth

- Điều chỉnh `expires_at` sau khi đọc PostgreSQL về UTC dạng datetime không gắn timezone trước khi tạo `google.oauth2.credentials.Credentials`.
- Nguyên nhân của lỗi còn lại là Google Auth thực hiện phép so sánh thời gian bằng UTC dạng naive, trong khi credential trước đó nhận datetime aware.
- Bản sửa trước đã chuẩn hóa theo hướng ngược lại nên chưa xử lý đúng lớp Google Auth; lần này chuẩn hóa đúng tại biên provider credential.
- Không thay đổi token, scope hoặc thiết kế mã hóa credential.
- Chưa đánh dấu Calendar E2E PASS; cần chạy lại request đọc lịch sau khi pull code.


## 2026-09-21 — Chốt chuẩn UTC cho toàn bộ thời gian Database và sửa UTF-8 API

- Chốt nguyên tắc: mọi timestamp lưu trong PostgreSQL dùng UTC; không lưu giờ GMT+7 trong database.
- Khi đọc/hiển thị cho người dùng hoặc API, application/presentation layer chuyển UTC sang `Asia/Ho_Chi_Minh` (GMT+7).
- Thời gian nhận từ người dùng phải được chuẩn hóa về UTC trước khi ghi database.
- Provider có thể dùng timezone riêng theo API contract nhưng không làm thay đổi chuẩn UTC của database.
- Sửa `POST /api/v1/agent/chat` trả JSON với khai báo `application/json; charset=utf-8` để client Windows/PowerShell đọc đúng tiếng Việt.


## 2026-09-21 — Tạo utility thời gian dùng chung

- Thêm `app/core/datetime.py` làm biên chuẩn hóa ngày giờ dùng chung cho toàn hệ thống.
- Cung cấp `utc_now()`, `to_utc()` và `to_vietnam_time()`.
- `to_utc()` và `to_vietnam_time()` từ chối datetime không có timezone để tránh lặp lại lỗi naive/aware.
- Calendar và các domain mới về sau phải dùng utility này thay vì tự xử lý timezone riêng.
