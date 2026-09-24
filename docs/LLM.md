# LLM Standalone — Ollama

> Trạng thái: **Verified — 2026-09-24**
>
> Phạm vi tài liệu này chỉ mô tả LLM layer độc lập. LLM hiện **chưa được nhúng vào Calendar, AgentRuntime hoặc scheduling flow**.

## 1. Runtime hiện tại

LLM V1 sử dụng local Ollama:

| Setting | Giá trị đã verify |
|---|---|
| `LLM_MODE` | `local` |
| Model | `qwen2.5:1.5b` |
| Ollama API | `http://127.0.0.1:11434` khi chạy Python trực tiếp trên Windows |
| Provider | `ollama` |

Trong Docker/container, Ollama host có thể được truy cập qua `http://host.docker.internal:11434`. Khi Python chạy trực tiếp trên Windows, dùng `127.0.0.1:11434` để test local provider.

## 2. Source boundary

Luồng LLM độc lập:

```
LLMResolver
    ↓
OllamaProvider
    ↓
HTTP POST /api/generate
    ↓
Ollama
    ↓
qwen2.5:1.5b
```

Các source chính:

- `app/llm/providers.py` — provider contract và response/error types.
- `app/llm/ollama.py` — Ollama HTTP adapter.
- `app/llm/resolver.py` — local/cloud/hybrid resolution.
- `app/llm/factory.py` — Settings → OllamaProvider → LLMResolver.

## 3. Models đã kiểm tra trên local Ollama

Local Ollama đã trả về:

- `qwen2.5:1.5b` — completion/tools.
- `qwen2.5vl:3b` — completion/vision.
- `nomic-embed-text-v2-moe:latest` — embedding.

LLM chat test hiện sử dụng `qwen2.5:1.5b`.

## 4. Runtime verification

Đã kiểm tra trực tiếp local:

1. Ollama API `/api/tags` hoạt động.
2. `qwen2.5:1.5b` trả lời prompt tiếng Việt qua Ollama CLI.
3. `OllamaProvider.generate()` gọi thành công Ollama và nhận response.
4. `LLMResolver(mode="local")` gọi thành công Ollama provider.
5. Unit tests LLM:

```text
python -m pytest -q tests/unit/llm

9 passed in 0.03s
```

## 5. System prompt runtime verification

Đã kiểm tra trực tiếp `system_prompt` qua `OllamaProvider.generate()`:

```text
provider = ollama
response = OK
```

Test sử dụng model `qwen2.5:1.5b`, Ollama local tại `127.0.0.1:11434`, với system prompt yêu cầu model tuân thủ định dạng trả lời. Kết quả xác nhận field `system` được truyền qua adapter và Ollama trả response thành công.

## 6. Unit-test coverage

`tests/unit/llm/test_ollama.py` kiểm tra:

- request tới `/api/generate`;
- model/prompt/stream payload;
- system prompt;
- HTTP error mapping;
- connection error mapping.

`tests/unit/llm/test_resolver.py` kiểm tra:

- local mode;
- cloud mode;
- hybrid local-first;
- hybrid fallback;
- cloud provider bắt buộc trong cloud/hybrid.

`tests/unit/llm/test_factory.py` kiểm tra factory tạo đúng Ollama provider và cấu hình model.

## 7. Error boundary

Ollama adapter maps transport/provider failures thành các lỗi contract rõ ràng:

| Failure | Error |
|---|---|
| HTTP 4xx/5xx | `LLMProviderError("ollama_http_<status>")` |
| Connection refused / network / timeout / OS error | `LLMProviderUnavailableError("ollama_unavailable")` |
| JSON hoặc UTF-8 response không hợp lệ | `LLMProviderError("ollama_invalid_response")` |
| Response không có field string `response` | `LLMProviderError("ollama_response_missing")` |

`LLMResolver` ở `hybrid` mode sẽ fallback từ local sang cloud khi local provider lỗi; `local` mode không tự fallback sang provider khác.

Các unit tests tương ứng đã được bổ sung trong `tests/unit/llm/test_ollama.py` và `tests/unit/llm/test_resolver.py`.

## 8. Explicit non-integration boundary

Tại trạng thái verified này:

- **Không** gọi Calendar provider từ LLM layer.
- **Không** đưa LLM vào `AgentRuntime`.
- **Không** đưa LLM vào LangGraph scheduling flow.
- **Không** thay đổi Google OAuth hoặc credential flow.
- LLM được kiểm thử như một subsystem độc lập.

## 9. Smoke-test commands

Kiểm tra Ollama:

```powershell
curl.exe http://127.0.0.1:11434/api/tags
```

Test model trực tiếp:

```powershell
ollama run qwen2.5:1.5b "Xin chào. Hãy trả lời bằng tiếng Việt trong một câu."
```

Test provider:

```powershell
python -c "from app.llm.ollama import OllamaProvider; p=OllamaProvider(base_url='http://127.0.0.1:11434', default_model='qwen2.5:1.5b'); print(p.generate('Hãy trả lời bằng tiếng Việt: 2 + 3 bằng bao nhiêu?'))"
```

Test LLM unit suite:

```powershell
python -m pytest -q tests/unit/llm
```
