# Google OAuth — Quy trình thao tác

> Mục đích: đây là tài liệu thao tác chuẩn để thực hiện lại Google OAuth khi cần cấp hoặc cấp lại quyền cho một Google account.
>
> Trạng thái: **ĐÃ XÁC NHẬN THỰC TẾ — Calendar Write OAuth PASS ngày 2026-09-21.**

## 1. Khi nào cần mở file này

Mỗi khi cần OAuth lại Google account, không tự nhớ URL hoặc tự thay đổi `.env`.

Làm theo đúng tài liệu này.

Các trường hợp thường gặp:

- Cấp quyền Google lần đầu.
- Cấp thêm capability mới, ví dụ từ `calendar.read` sang `calendar.write`.
- Re-authorize sau khi thay đổi scope.
- Credential cũ hết hạn hoặc cần cấp lại quyền.

## 2. Phân biệt các thông tin

### `credentials.json`

Đây là cấu hình OAuth Client của Google.

File nằm tại:

`data/google/credentials.json`

Không phải token của user.

### `x-user-id`

Đây là ID user trong PostgreSQL.

Không đặt vào `.env`.

### `x-organization-id`

Đây là ID organization trong PostgreSQL.

Không đặt vào `.env`.

### `account_id`

Đây là ID account Google nội bộ trong PostgreSQL.

Không phải email Google và không phải access token.

## 3. Lấy `user_id`

Nếu chưa biết user ID, kiểm tra PostgreSQL:

```powershell
docker exec workspace-ai-agent-postgres psql -U workspace -d workspace_ai_agent -c "SELECT id, email FROM users ORDER BY created_at;"
```

Chọn đúng user cần OAuth.

## 4. Lấy `organization_id`

Sau khi có `user_id`:

```powershell
docker exec workspace-ai-agent-postgres psql -U workspace -d workspace_ai_agent -c "SELECT * FROM organization_members WHERE user_id = '<USER_ID>';"
```

Lấy cột `organization_id`.

Chỉ sử dụng organization có `status = active`.

## 5. Xác định `account_id`

Không đoán `account_id`.

Nếu chưa biết account ID, tra bảng account tương ứng trong PostgreSQL hoặc dùng account metadata đã được runtime resolve.

Nguyên tắc:

- Một user có thể có nhiều Google account.
- OAuth phải gắn đúng account cần cấp quyền.
- Không dùng email thay cho `account_id` khi endpoint yêu cầu UUID nội bộ.

## 6. OAuth theo capability

### Calendar Read

Dùng:

`capability=calendar.read`

Scope:

`https://www.googleapis.com/auth/calendar.readonly`

### Calendar Write

Dùng:

`capability=calendar.write`

Scope:

`https://www.googleapis.com/auth/calendar`

Không tự thêm scope khác vào URL.

## 7. Tạo OAuth URL

Endpoint:

`GET /auth/google/start`

Request phải có hai HTTP header:

```text
x-user-id: <USER_ID>
x-organization-id: <ORGANIZATION_ID>
```

Ví dụ PowerShell:

```powershell
curl.exe -s -D - `
  -H "x-user-id: <USER_ID>" `
  -H "x-organization-id: <ORGANIZATION_ID>" `
  "http://localhost:8000/auth/google/start?account_id=<ACCOUNT_ID>&capability=calendar.write"
```

Trong output tìm dòng:

```text
location: https://accounts.google.com/...
```

Copy toàn bộ URL `https://accounts.google.com/...` và mở bằng Chrome.

> Không dùng `Invoke-WebRequest` nếu PowerShell chặn HTML parsing. `curl.exe` là cách thao tác chuẩn trong tài liệu này.

## 8. Hoàn tất OAuth

Đăng nhập đúng Google account và chấp nhận quyền.

Google sẽ redirect về:

`http://localhost:8000/auth/google/callback`

Kết quả thành công có dạng:

```json
{
  "status": "ok",
  "account_id": "<ACCOUNT_ID>",
  "organization_id": "<ORGANIZATION_ID>",
  "message": "Google OAuth hoàn tất."
}
```

## 9. Kiểm tra sau OAuth

Không coi việc Google redirect thành công là đủ.

Cần kiểm tra tiếp capability/scope trước khi test feature.

Đối với Calendar Write, credential phải có scope Calendar phù hợp:

`https://www.googleapis.com/auth/calendar`

Không đưa access token hoặc refresh token vào chat, log, SQL command hoặc tài liệu.

## 10. Quy tắc bảo mật

- Không commit `data/google/credentials.json` vào Git.
- Không dán access token/refresh token vào chat.
- Không ghi token plaintext vào log.
- Không sửa `.env` để thêm `x-user-id` hoặc `x-organization-id`.
- Không tự thay đổi `GOOGLE_REDIRECT_URI` nếu không có yêu cầu kiến trúc.
- OAuth state và PKCE được server quản lý; không tự tạo state thủ công.
- Không dùng OAuth URL cũ khi cần cấp lại quyền.

## 11. Quy trình chuẩn rút gọn

```text
Mở docs/GOOGLE_OAUTH.md
        ↓
Lấy user_id
        ↓
Lấy organization_id
        ↓
Xác định account_id
        ↓
Chọn capability
        ↓
GET /auth/google/start
        ↓
Copy Location Google
        ↓
Mở Chrome
        ↓
Google consent
        ↓
/auth/google/callback
        ↓
Kiểm tra scope/credential
        ↓
Test capability
```

## 12. Lần xác nhận thực tế

Ngày **2026-09-21**, quy trình này đã được chạy thực tế cho:

- user: `01a0c387-8eb5-7df5-aaa1-fcb8d3684ccc`
- organization: `01a0c387-8eaa-7147-8cf8-5e284268b30a`
- account: `01a0c387-8f30-767d-acb4-ccf9edc0f22b`
- capability: `calendar.write`

Callback thực tế trả:

```json
{
  "status": "ok",
  "account_id": "01a0c387-8f30-767d-acb4-ccf9edc0f22b",
  "organization_id": "01a0c387-8eaa-7147-8cf8-5e284268b30a",
  "message": "Google OAuth hoàn tất."
}
```

Kết luận: **Google OAuth cho Calendar Write đã được xác nhận hoạt động thực tế.**
