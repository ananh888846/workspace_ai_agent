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
| Google OAuth | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI` | OAuth application |
| Calendar | `GOOGLE_CALENDAR_*_SCOPE` | Calendar OAuth scopes |

## 3. Khi chưa có Google OAuth

Agent vẫn phải khởi động được khi Client ID/Secret rỗng.
Khi đó `google_oauth_configured = false`.

Không tạo credential giả để làm Calendar có vẻ đã kết nối.

## 4. PostgreSQL local

Docker local dùng:
`postgresql://workspace:workspace_dev_password@workspace-ai-agent-postgres:5432/workspace_ai_agent`

Đây là credential phát triển local, không dùng production.

## 5. Qdrant / Ollama

Docker container có thể dùng:
- Qdrant: `http://workspace-ai-agent-qdrant:6333`
- Ollama trên host Windows: `http://host.docker.internal:11434`

Nếu Agent chạy ngoài Docker, thay hostname bằng endpoint phù hợp.

## 6. Google OAuth

Sau này tạo `.env` từ `.env.example` và điền Client ID/Secret/Redirect URI.
OAuth token của từng Google account **không** đi vào `.env`; token thuộc credential layer.

## 7. Thứ tự triển khai

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
