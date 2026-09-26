# Workspace AI Agent — Local Development

**Cập nhật:** 2026-09-26 (GMT+7, TP.HCM)

> Mục tiêu: mở file này là biết cách kéo code về Windows local, khởi động hạ tầng và chạy Workspace AI Agent.

## 1. Kiến trúc local

~~~text
Windows
  |
  +-- Python / FastAPI Agent :8000
  +-- PostgreSQL Docker :5433
  +-- Qdrant Docker :6333
  +-- Ollama Windows :11434 (optional, cần cho LLM/Embedding runtime)
~~~

## 2. Yêu cầu máy

Cần có:

- Git
- Python 3.12+ (khuyến nghị Python 3.12/3.13)
- Docker Desktop
- PowerShell
- Ollama chỉ cần khi chạy LLM/Embedding/Knowledge K5-K6 runtime.

Kiểm tra:

~~~powershell
git --version
python --version
docker --version
docker compose version
~~~

## 3. Lần đầu kéo repository

~~~powershell
cd D:\Nhin_lam_cho
git clone https://github.com/ananh888846/workspace_ai_agent.git
cd workspace_ai_agent
~~~

Nếu repo đã tồn tại:

~~~powershell
cd D:\Nhin_lam_cho\workspace_ai_agent
git status
git pull --ff-only origin main
~~~

Không dùng git reset --hard để đồng bộ hằng ngày nếu chưa kiểm tra thay đổi local.

## 4. Tạo Python environment

Nếu chưa có .venv:

~~~powershell
python -m venv .venv
~~~

Kích hoạt:

~~~powershell
.\.venv\Scripts\Activate.ps1
~~~

Cài dependency:

~~~powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
~~~

Nếu PowerShell chặn Activate.ps1, không cần activate; có thể gọi trực tiếp:

~~~powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
~~~

## 5. Tạo .env local

Chỉ làm lần đầu:

~~~powershell
Copy-Item .env.example .env
~~~

.env là local-only, không commit.

Khi chạy Agent trực tiếp trên Windows, dùng:

~~~text
DATABASE_URL=postgresql://workspace:workspace_dev_password@127.0.0.1:5433/workspace_ai_agent
QDRANT_URL=http://127.0.0.1:6333
OLLAMA_BASE_URL=http://127.0.0.1:11434
~~~

Nếu chỉ chạy API/Core, Ollama có thể chưa cần cài.

## 6. Khởi động PostgreSQL + Qdrant

~~~powershell
docker compose up -d
docker compose ps
~~~

Kỳ vọng:

- workspace-ai-agent-postgres — healthy
- workspace-ai-agent-qdrant — running

Kiểm tra PostgreSQL:

~~~powershell
docker exec workspace-ai-agent-postgres pg_isready -U workspace -d workspace_ai_agent
~~~

Kiểm tra Qdrant:

~~~powershell
Invoke-WebRequest http://127.0.0.1:6333/collections
~~~

## 7. Database migrations

Migration là bước riêng; không tự chạy lại toàn bộ 001 → 052 trên database đã có schema.

Khi cần bootstrap một database PostgreSQL hoàn toàn mới, chạy các file migration theo thứ tự:

~~~powershell
Get-ChildItem database\migrations\*.sql |
  Sort-Object Name |
  ForEach-Object {
    Write-Host "Running $($_.Name)"
    Get-Content $_.FullName -Raw |
      docker exec -i workspace-ai-agent-postgres psql -U workspace -d workspace_ai_agent
    if ($LASTEXITCODE -ne 0) { throw "Migration failed: $($_.Name)" }
  }
~~~

Sau migration, chạy acceptance phù hợp với migration đang verify.

> Lưu ý: repository hiện chưa có migration tracking table tự động. Trên database đang dùng, chỉ chạy migration mới/chưa chạy; không chạy lại migration cũ.

## 8. Chạy FastAPI Agent

Cách chuẩn:

~~~powershell
$env:PYTHONPATH = (Get-Location).Path
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
~~~

Kiểm tra:

~~~powershell
Invoke-WebRequest http://127.0.0.1:8000/health
~~~

Kết quả mong đợi:

~~~json
{"status":"ok"}
~~~

API docs:

~~~text
http://127.0.0.1:8000/docs
~~~

## 9. Cách chạy nhanh mỗi ngày

Có thể dùng:

~~~powershell
.\run_daily.bat
~~~

Script sẽ:

1. kiểm tra Git;
2. pull origin/main;
3. tạo .venv nếu thiếu;
4. cài dependency;
5. bật PostgreSQL + Qdrant;
6. khởi động FastAPI nếu chưa chạy;
7. kiểm tra /health.

Script không xóa Docker volume và không reset Git.

Nếu script báo lỗi, xem:

~~~text
agent_api.log
~~~

## 10. Local Server lifecycle — L1/L2

Có thể quản lý toàn bộ Local Server bằng PowerShell:

```powershell
cd D:\Project\workspace_ai_agent
.\\scripts\\local-server.ps1 status
.\\scripts\\local-server.ps1 start
.\\scripts\\local-server.ps1 health
.\\scripts\\local-server.ps1 stop
```

Có thể đặt đường dẫn Laravel qua biến môi trường:

```powershell
$env:WORKSPACE_AI_AGENT_WEB_PATH = "D:\\Project\\workspace_ai_agent_web"
```

`start` sẽ bật PostgreSQL + Qdrant, Agent FastAPI và Laravel Web nếu đường dẫn Web được cấu hình. Script không xóa Docker volume.

Health tổng hợp của Agent: `GET /health/dependencies`.

## 11. API hardening — L3

Local mặc định:

```env
APP_ALLOWED_HOSTS=127.0.0.1,localhost
APP_CORS_ORIGINS=http://127.0.0.1:8001,http://localhost:8001
APP_ENFORCE_HTTPS=false
```

Agent có Trusted Host, CORS allowlist, security response headers và dependency health check. Không dùng `*` làm CORS allowlist.

PostgreSQL và Qdrant Docker ports được bind vào `127.0.0.1`, không public ra LAN theo mặc định.

Server-to-server `AGENT_SERVER_TOKEN` vẫn là secret của Laravel → Agent; không đưa token này vào Flutter/browser.

## 12. Remote Access V1 — L4

Remote access hiện được thiết kế theo hướng publish **Laravel Web qua HTTPS/reverse proxy**, còn Agent, PostgreSQL, Qdrant và Ollama giữ private.

Template: `deploy/Caddyfile.example`.

Decision/runbook: `deploy/REMOTE_ACCESS_V1.md`.

Flutter direct-to-Agent chưa được publish ở L4 vì cần một user/client authentication contract riêng; không tái sử dụng server-to-server token.

## 13. Chạy test

Test nhanh toàn bộ unit:

~~~powershell
$env:PYTHONPATH = (Get-Location).Path
.\.venv\Scripts\python.exe -m pytest -q
~~~

Knowledge regression:

~~~powershell
.\.venv\Scripts\python.exe -m pytest -q `
  tests/unit/knowledge/test_local_storage.py `
  tests/unit/knowledge/test_docling_parser.py `
  tests/unit/knowledge/test_postgres_knowledge_repository.py `
  tests/unit/knowledge/test_ingestion_contract.py
~~~

## 14. K4 — File Storage + Docling

K4 không cần Ollama.

~~~powershell
$env:PYTHONPATH = (Get-Location).Path
.\.venv\Scripts\python.exe -m pytest -q `
  tests/unit/knowledge/test_local_storage.py `
  tests/unit/knowledge/test_docling_parser.py
~~~

## 15. K5/K6 — Ollama + Qdrant

K5 dùng Ollama embedding; K6 dùng Qdrant.

Cài Ollama trên Windows:

https://ollama.com/download/windows

Sau khi cài:

~~~powershell
ollama --version
ollama pull nomic-embed-text-v2-moe
ollama list
Invoke-WebRequest http://127.0.0.1:11434/api/tags
~~~

Sau đó:

~~~powershell
$env:PYTHONPATH = (Get-Location).Path
$env:RUN_KNOWLEDGE_VECTOR_SMOKE = "1"

.\.venv\Scripts\python.exe -m pytest -q `
  tests/unit/knowledge/test_qdrant_vector_index.py `
  tests/unit/knowledge/test_ollama_embedding.py `
  tests/integration/test_knowledge_k5_k6_runtime.py
~~~

K5/K6 runtime smoke phải có Ollama thật đang chạy. Unit test không thay thế runtime verification.

## 16. Dừng hạ tầng

Tắt container nhưng giữ dữ liệu:

~~~powershell
docker compose stop
~~~

Khởi động lại:

~~~powershell
docker compose start
~~~

Không dùng docker compose down -v trừ khi cố ý xóa toàn bộ PostgreSQL/Qdrant local data.

## 17. Quy trình làm việc chuẩn

~~~text
1. cd workspace_ai_agent
        |
2. git status
        |
3. git pull --ff-only origin main
        |
4. .venv / pip install nếu requirements thay đổi
        |
5. Copy .env.example -> .env nếu lần đầu
        |
6. docker compose up -d
        |
7. migration mới nếu có
        |
8. chạy test cần thiết
        |
9. uvicorn app.main:app
        |
10. /health
~~~

## 18. Khi code trên GitHub vừa được cập nhật

Luôn kiểm tra commit local:

~~~powershell
git log -1 --oneline
git status
~~~

Chỉ coi thay đổi là đã kiểm thử khi local đang đúng commit đã được kéo từ GitHub.

## 19. Ranh giới repository

~~~text
workspace_ai_agent
  -> Backend / Runtime / PostgreSQL / Knowledge / Providers

workspace_ai_agent_web
  -> Frontend / Web

workspace-ai-agent-ecosystem
  -> Architecture / Design / Knowledge / Decisions / Status
~~~

Không trộn ba repository vào một runtime.

## 20. Troubleshooting nhanh

### python không nhận

Cài Python và mở PowerShell mới.

### .venv lỗi dependency

~~~powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
~~~

### ModuleNotFoundError: app

Từ root repo:

~~~powershell
$env:PYTHONPATH = (Get-Location).Path
~~~

### PostgreSQL không kết nối

~~~powershell
docker compose ps
docker logs workspace-ai-agent-postgres --tail 100
~~~

### Qdrant không kết nối

~~~powershell
docker logs workspace-ai-agent-qdrant --tail 100
Invoke-WebRequest http://127.0.0.1:6333/collections
~~~

### Ollama không nhận lệnh

Cài Ollama, đóng PowerShell cũ, mở PowerShell mới rồi:

~~~powershell
ollama --version
~~~

### Agent không start

~~~powershell
Get-Content .\agent_api.log -Tail 100
~~~

---

## 21. Source of truth

- Runtime/config: docs/CONFIGURATION.md
- Development workflow: docs/DEVELOPMENT_WORKFLOW_V1.md
- Database: docs/DATABASE_V2_DETAILED.md
- Migration contract: docs/MIGRATION_CONTRACT_V2.md
- Knowledge: docs/KNOWLEDGE.md
- Runtime acceptance: docs/RUNTIME.md

Nếu README này và implementation khác nhau, ưu tiên kiểm tra implementation rồi cập nhật tài liệu.
