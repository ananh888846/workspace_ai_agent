# Configuration & Environment

> Trạng thái: **Configuration V1 baseline**
>
> Tài liệu này là nguồn tham chiếu cho cấu hình runtime. Không lưu secret thật trong GitHub.

## 1. Quy tắc

- `.env.example` được commit để mô tả cấu hình.
- `.env` local không được commit.
- OAuth client secret không được ghi vào source code.
- OAuth access/refresh token không được đặt trong `.env`.
- Credential của từng external account thuộc `account_credentials` và chỉ được truy cập qua `CredentialResolver`.
- Không log giá trị secret.

## 2. Nhóm cấu hình

| Nhóm | Biến | Mục đích |
|---|---|---|
| App | `APP_ENV`, `APP_HOST`, `APP_PORT` | Runtime process |
| PostgreSQL | `DATABASE_URL` | Core DB |
| Qdrant | `QDRANT_URL`, `QDRANT_COLLECTION` | Knowledge retrieval |
| Ollama | `OLLAMA_BASE_URL` + model names | LLM/vision/embedding |
| File Storage | `FILE_STORAGE_DRIVER`, `FILE_STORAGE_PATH` | Binary/asset storage |
| Google OAuth | `GOOGLE_CREDENTIALS_FILE`, `GOOGLE_TOKEN_DIR`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI` | OAuth application + local credential files |
| Calendar | `GOOGLE_CALENDAR_*_SCOPE` | Calendar OAuth scopes |

## 3. Khi chưa có Google OAuth

Agent vẫn phải khởi động được khi Client ID/Secret rỗng.
Khi đó `google_oauth_configured = false`.

Không tạo credential giả để làm Calendar có vẻ đã kết nối.

## 4. PostgreSQL local

Docker local dùng:
`postgresql://workspace:workspace_dev_password@workspace-ai-agent-postgres:5432/workspace_ai_agent`

Đây là credential phát triển local, không dùng production.

Khi chạy Agent trực tiếp trên Windows bằng Uvicorn, PostgreSQL Docker được truy cập qua host port:

`postgresql://workspace:workspace_dev_password@127.0.0.1:5433/workspace_ai_agent`

`.env` local phải dùng endpoint phù hợp với runtime đang chạy. Không dùng hostname `workspace-ai-agent-postgres:5432` từ process Windows ngoài Docker network.

## 5. Docker Compose infrastructure

`docker-compose.yml` hiện quản lý PostgreSQL 18 và Qdrant. Agent application container chưa được thêm vào Compose ở bước này vì source tree hiện chưa có `app/main.py`/Dockerfile runtime hoàn chỉnh.

Các volume dữ liệu dùng named volume. Không bind-mount secret vào image.

Khi application container được triển khai, Google OAuth local directory sẽ được bind-mount theo policy runtime:

```text
./data/google:/app/data/google
```

Không copy `credentials.json` vào Docker image.

## 6. Qdrant / Ollama

Docker container có thể dùng:
- Qdrant: `http://workspace-ai-agent-qdrant:6333`
- Ollama trên host Windows: `http://host.docker.internal:11434`

Nếu Agent chạy ngoài Docker, thay hostname bằng endpoint phù hợp.

## 7. Google OAuth

### 7.1 Cấu trúc file local

Không commit các file OAuth thật. Local runtime dùng:

```text
data/
└── google/
    ├── credentials.json
    └── token.json
```

- `credentials.json`: OAuth client configuration tải từ Google Cloud.
- `token.json`: token local phát sinh sau OAuth flow, nếu flow dùng file token.
- Cả hai đều thuộc local secret/runtime data và không được commit.

Trong Docker, thư mục được ánh xạ thành:

```text
/app/data/google/credentials.json
/app/data/google/token.json
```

Cấu hình:

- `GOOGLE_CREDENTIALS_FILE=/app/data/google/credentials.json`
- `GOOGLE_TOKEN_DIR=/app/data/google`

### 7.2 Boundary

Sau này tạo `.env` từ `.env.example` và điền Client ID/Secret/Redirect URI khi OAuth application cần dùng.

OAuth access/refresh token của từng Google account **không** đi vào `.env`; credential thuộc credential layer và được truy cập qua `CredentialResolver`.

Nếu dùng local OAuth bootstrap, `credentials.json` chỉ là input cho OAuth flow; không được coi nó là credential của một user cụ thể.

### 7.3 Scope consistency và PKCE

Mỗi lần bắt đầu OAuth, ứng dụng tạo một bộ scope cụ thể cho capability đang được cấp quyền. Bộ scope này được lưu trong OAuth state đã mã hóa cùng `code_verifier`.

Callback phải dựng lại `Flow` bằng **chính bộ scope được lưu trong state**, không tự dùng một bộ scope Calendar cố định khác. Cách này bảo đảm authorization request và token exchange dùng cùng contract.

Google có thể trả về thêm các scope đã được người dùng cấp trước đó khi sử dụng `include_granted_scopes=true`. Các scope thực tế do Google trả về được lưu cùng credential trong `account_credentials.scopes`; không tự chỉnh token hoặc scope bằng tay.

PKCE vẫn bắt buộc:

```text
scope + code_verifier
        ↓
OAuth state mã hóa + HMAC
        ↓
Google authorization
        ↓
callback
        ↓
khôi phục scope + code_verifier
        ↓
fetch_token()
```

Không dùng lại callback URL cũ hoặc authorization code đã sử dụng.

## 8. Nạp cấu hình khi chạy trực tiếp

`app/config/settings.py` tự đọc `.env` tại root project khi process chưa có biến môi trường tương ứng.

Thứ tự ưu tiên:

1. Environment variables đã được process/runtime cung cấp.
2. `.env` local tại root project, chỉ bổ sung biến còn thiếu.
3. Default an toàn trong `Settings`.

Docker Compose vẫn có thể inject environment variables trực tiếp; các biến đã có trong process sẽ không bị `.env` ghi đè.

## 9. Thứ tự triển khai

```
.env.example
    ↓
.env local
    ↓
Settings
    ↓
PostgreSQL/Qdrant/Ollama connectivity
    ↓
DB fixture
    ↓
PostgreSQL-backed Core runtime
    ↓
Google OAuth
    ↓
CredentialResolver
    ↓
Calendar E2E
```

Không bỏ qua Core authorization để gọi provider API trực tiếp.

## 10. OAuth security secrets

- `GOOGLE_OAUTH_STATE_SECRET`: secret dùng để ký OAuth state bằng HMAC. Không commit.
- `GOOGLE_CREDENTIAL_ENCRYPTION_KEY`: khóa Fernet dùng để mã hóa credential trước khi ghi `account_credentials.encrypted_value`. Không commit.
- Hai giá trị này không được đưa vào prompt, log, audit hoặc HTTP response.
- Nếu thiếu một trong hai secret, OAuth flow phải dừng thay vì tạo credential không bảo vệ.
