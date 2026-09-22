# Agent Runtime V2.2 — Phase 1

> Trạng thái: **Implemented — orchestration seam V1**  
> Ngày: 2026-09-22

## Mục tiêu

Phase 1 triển khai phần lõi đã được phê duyệt trong Decision 045 mà không rewrite toàn bộ Calendar runtime:

- tạo **Agent Runtime Entry** độc lập với FastAPI;
- tạo **LangGraph Super-Graph** tối thiểu;
- giữ `/api/v1/agent/chat` làm compatibility endpoint;
- giữ Application Authorization, Credential Resolver, Tool và Provider boundary hiện tại;
- không đưa secret vào Graph state;
- không thêm Agent service vào Docker Compose.

## Luồng Phase 1

```text
FastAPI
  ↓
Agent Runtime Entry
  ↓
LangGraph Super-Graph
  ├── classify_request
  └── execute_route
        ↓
Existing Application Runtime
  ├── Account Resolver
  ├── Authorization
  ├── Credential Resolver
  ├── Tool
  └── Provider
```

`execute_route` nhận state đã phân loại và gọi application callback được dependency injection. Graph không biết SQL, Qdrant, OAuth secret hoặc provider API.

## Vì sao chưa tách toàn bộ Calendar execution?

Calendar V1 đang là regression baseline. Việc tách toàn bộ `agent_chat()` trong một commit sẽ tạo thay đổi lớn và tăng rủi ro regression.

Phase 1 vì vậy chỉ tạo orchestration seam. Phase tiếp theo sẽ di chuyển từng capability vào route/handler riêng, sau mỗi bước chạy regression.

## Graph state

State chỉ chứa:

- request;
- context;
- intent;
- capability;
- action;
- result.

Không chứa:

- access token;
- refresh token;
- client secret;
- credential object;
- SQL connection;
- provider client.

## Deployment

Không thay đổi Docker Compose. Postgres và Qdrant tiếp tục là infrastructure services. Agent Runtime vẫn có thể chạy cùng process Python/FastAPI trong development.

## Tiêu chí mở Phase 2

- Phase 1 unit test PASS.
- Calendar regression vẫn PASS.
- Không phát sinh provider side effect ngoài hành vi hiện tại.
- Sau đó mới tách capability routing và execution handler khỏi endpoint.
