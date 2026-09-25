# Configuration & Environment

**Cập nhật:** 2026-09-24 20:50 (GMT+7, TP.HCM)

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

## 3. Windows local runtime

Khi chạy FastAPI trực tiếp trên Windows, các endpoint mặc định trong `.env.example` là:

- PostgreSQL: `127.0.0.1:5433`
- Qdrant: `127.0.0.1:6333`
- Ollama: `127.0.0.1:11434`
- Agent API: `127.0.0.1:8000`

Khi Agent chạy bên trong Docker network, dùng hostname service tương ứng, ví dụ Qdrant `workspace-ai-agent-qdrant:6333` và Ollama trên Windows host `host.docker.internal:11434`.

## 4. PostgreSQL local

Docker local dùng:

`postgresql://workspace:workspace_dev_password@workspace-ai-agent-postgres:5432/workspace_ai_agent`

Đây là credential phát triển local, không dùng production.

Khi chạy Agent trực tiếp trên Windows bằng Uvicorn, PostgreSQL Docker được truy cập qua:

`postgresql://workspace:workspace_dev_password@127.0.0.1:5433/workspace_ai_agent`

Không dùng hostname `workspace-ai-agent-postgres:5432` từ process Windows ngoài Docker network.

## 5. Docker Compose infrastructure

`docker-compose.yml` quản lý PostgreSQL 18 và Qdrant. Agent application chạy trực tiếp bằng Uvicorn trong quy trình local hiện tại.

Các volume dữ liệu dùng named volume. Không bind-mount secret vào image.

## 6. Qdrant / Ollama

- Qdrant trong Docker: `http://workspace-ai-agent-qdrant:6333`
- Qdrant từ Windows: `http://127.0.0.1:6333`
- Ollama trên Windows: `http://127.0.0.1:11434`
- Ollama từ Docker: `http://host.docker.internal:11434`

K5/K6 Knowledge runtime cần Ollama thật đang chạy. Ollama không bắt buộc để chạy API/Core cơ bản.

## 7. File Storage

Windows local nên dùng:

`FILE_STORAGE_DRIVER=local`

và:

`FILE_STORAGE_PATH=./data/storage`

Thư mục `data/` thuộc local runtime và không commit.

## 8. Google OAuth

### 8.1 Cấu trúc file local

Không commit các file OAuth thật. Local runtime dùng:

~~~text
data/
└── google/
    ├── credentials.json
    └── token.json
~~~

- `credentials.json`: OAuth client configuration tải từ Google Cloud.
- `token.json`: token local phát sinh sau OAuth flow, nếu flow dùng file token.
- Cả hai đều thuộc local secret/runtime data và không được commit.

### 8.2 Boundary

OAuth access/refresh token của từng Google account **không** đi vào `.env`; credential thuộc credential layer và được truy cập qua `CredentialResolver`.

Nếu dùng local OAuth bootstrap, `credentials.json` chỉ là input cho OAuth flow; không được coi nó là credential của một user cụ thể.

### 8.3 Scope consistency và PKCE

Mỗi lần bắt đầu OAuth, ứng dụng tạo một bộ scope cụ thể cho capability đang được cấp quyền. Bộ scope này được lưu trong OAuth state đã mã hóa cùng `code_verifier`.

Callback phải dựng lại `Flow` bằng chính bộ scope được lưu trong state, không tự dùng một bộ scope Calendar cố định khác.

PKCE vẫn bắt buộc:

~~~text
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
~~~

## 9. Nạp cấu hình khi chạy trực tiếp

`app/config/settings.py` tự đọc `.env` tại root project khi process chưa có biến môi trường tương ứng.

Thứ tự ưu tiên:

1. Environment variables đã được process/runtime cung cấp.
2. `.env` local tại root project, chỉ bổ sung biến còn thiếu.
3. Default an toàn trong `Settings`.

## 10. Thứ tự triển khai

~~~text
.env.example
    ↓
.env local
    ↓
Settings
    ↓
PostgreSQL/Qdrant connectivity
    ↓
DB migration/fixture
    ↓
FastAPI /health
    ↓
Ollama nếu dùng LLM/Knowledge K5-K6
    ↓
Google OAuth nếu dùng Calendar
    ↓
CredentialResolver
    ↓
Provider E2E
~~~

Không bỏ qua Core authorization để gọi provider API trực tiếp.

## 11. OAuth security secrets

- `GOOGLE_OAUTH_STATE_SECRET`: secret dùng để ký OAuth state bằng HMAC. Không commit.
- `GOOGLE_CREDENTIAL_ENCRYPTION_KEY`: khóa Fernet dùng để mã hóa credential trước khi ghi `account_credentials.encrypted_value`. Không commit.
- Hai giá trị này không được đưa vào prompt, log, audit hoặc HTTP response.
- Nếu thiếu một trong hai secret, OAuth flow phải dừng thay vì tạo credential không bảo vệ.

## 12. Multi-Hybrid LLM V1

Multi-Hybrid LLM V1 chỉ có ba mode:

| Mode | Hành vi |
|---|---|
| `local` | Chỉ gọi Ollama/local provider |
| `cloud` | Chỉ gọi cloud provider |
| `hybrid` | Gọi local trước; local lỗi thì fallback sang cloud |

Mặc định là `LLM_MODE=local`.

Các biến cloud là optional. Nếu chọn `cloud` hoặc `hybrid` mà cloud provider chưa được cấu hình, resolver phải báo lỗi cấu hình thay vì tự ý đổi mode.

V1 chưa có intelligent routing, model scoring, cost/token accounting, latency optimization hoặc policy routing theo organization.

API key của cloud provider là server-side secret: không commit, không log, không đưa vào LangGraph state, prompt hoặc HTTP response.
