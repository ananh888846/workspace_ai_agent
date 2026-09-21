# CHANGELOG_03.md

> Changelog tiếp theo của `docs/CHANGELOG_02.md`.
>
> Quy tắc: changelog chỉ ghi trạng thái đã được triển khai/kiểm tra; không ghi `PASS` nếu chưa có runtime verification.

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
