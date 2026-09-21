# Workspace AI Agent — SOURCE TREE V2.1

> Blueprint source tree trước implementation. Chưa phải application code.

## 1. Nguyên tắc
- `domain/` chứa business rules và entities, không gọi provider.
- `application/` điều phối use-case, authorization và transaction boundary.
- `interfaces/` nhận request và chuyển thành application command.
- `infrastructure/` triển khai PostgreSQL, Qdrant, credential store và provider adapters.
- `agent/` chỉ lập kế hoạch/orchestration; không bypass authorization.
- `providers/` chứa Google và provider-specific adapter.
- `tools/` là implementation của capability.
- `security/` xử lý authentication, authorization, credential boundary và audit.
- `workers/` dành cho job nền sau khi runtime core ổn định.
- `tests/` kiểm tra contract và runtime behavior.
- `docs/` là architecture contract.

## 2. Cây thư mục mục tiêu

~~~text
workspace_ai_agent/
├── app/
│   ├── main.py
│   ├── bootstrap.py
│   ├── config/
│   ├── interfaces/
│   │   ├── http/
│   │   │   ├── routes/
│   │   │   ├── dependencies.py
│   │   │   └── schemas/
│   │   ├── cli/
│   │   └── device/
│   ├── application/
│   │   ├── context/
│   │   ├── authentication/
│   │   ├── organizations/
│   │   ├── authorization/
│   │   ├── accounts/
│   │   ├── resources/
│   │   ├── packages/
│   │   ├── devices/
│   │   ├── observations/
│   │   ├── events/
│   │   ├── activity_sessions/
│   │   ├── activities/
│   │   ├── tasks/
│   │   ├── observations/
│   │   ├── events/
│   │   ├── activity_sessions/
│   │   ├── activities/
│   │   ├── tasks/
│   │   ├── capabilities/
│   │   ├── knowledge/
│   │   ├── conversations/
│   │   ├── memory/
│   │   ├── agents/
│   │   ├── agent_communication/
│   │   ├── anomalies/
│   │   ├── automation/
│   │   └── audit/
│   ├── domain/
│   │   ├── identity/
│   │   ├── organizations/
│   │   ├── accounts/
│   │   ├── authorization/
│   │   ├── resources/
│   │   ├── packages/
│   │   ├── devices/
│   │   ├── events/
│   │   ├── conversations/
│   │   ├── memory/
│   │   ├── knowledge/
│   │   ├── agents/
│   │   ├── agent_communication/
│   │   ├── anomalies/
│   │   ├── tools/
│   │   └── automation/
│   ├── security/
│   │   ├── authentication/
│   │   ├── authorization/
│   │   ├── organization_scope/
│   │   ├── credentials/
│   │   ├── secrets/
│   │   └── audit/
│   ├── agent/
│   │   ├── orchestrator.py
│   │   ├── planner.py
│   │   ├── router.py
│   │   ├── communication.py
│   │   └── context.py
│   ├── tools/
│   │   ├── registry.py
│   │   ├── resolver.py
│   │   └── definitions/
│   ├── providers/
│   │   ├── base/
│   │   └── google/
│   │       ├── client.py
│   │       ├── account_mapper.py
│   │       ├── credential_mapper.py
│   │       ├── resource_mapper.py
│   │       └── tools/
│   ├── infrastructure/
│   │   ├── database/
│   │   │   ├── session.py
│   │   │   ├── models/
│   │   │   └── repositories/
│   │   ├── qdrant/
│   │   ├── credentials/
│   │   └── providers/
│   ├── workers/
│   │   └── jobs/
│   └── shared/
│       ├── ids.py
│       ├── time.py
│       ├── errors.py
│       └── result.py
├── migrations/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── authorization/
│   ├── providers/
│   └── runtime/
├── scripts/
├── data/
├── secrets/
├── docker/
├── docs/
├── pyproject.toml
├── docker-compose.yml
├── Dockerfile
├── .env.example
└── README.md
~~~

## 3. Dependency direction
~~~text
interfaces → application → domain
application → ports/contracts → infrastructure/providers
agent → application capability → authorization → tool → provider adapter
domain ✕ provider
domain ✕ database
domain ✕ Qdrant
~~~
`domain/` không import provider SDK, SQLAlchemy session, Qdrant client hoặc framework-specific authorization.

## 4. Core contracts
- `AgentContext`
- `AuthenticationService`
- `OrganizationContextResolver`
- `AuthorizationService`
- `AccountResolver`
- `CredentialResolver`
- `ResourceAccessChecker`
- `DataPackageResolver`
- `CapabilityRegistry`
- `ToolResolver`
- `ProviderAdapter`
- `AuditService`

Contract không chứa secret.

## 5. Organization / Resource boundary

Mọi use-case tenant-scoped phải resolve `organization_id` trước khi truy cập dữ liệu. `parent_resource_id` không được trỏ sang organization khác. Device phải thuộc organization và có thể bind resource.

## 6. Phase 1 implementation boundary
Chỉ implement foundation, identity, session, AgentContext, database boundary và test contracts. Chưa implement Google, Qdrant, CrewAI, automation hoặc device workflow.

## 7. Phase 2 boundary
Thêm accounts, resources, authorization, credentials, provider base, Google adapter và tools. Google chỉ được gọi sau authorization.

## 8. Phase 3+ domain boundaries

Activity Session, Tasks, Agent-to-Agent communication và Anomaly chỉ triển khai sau khi core organization/resource/authorization boundary ổn định.

## 9. Quy tắc import
- domain → infrastructure: cấm
- domain → providers: cấm
- domain → agent framework: cấm
- provider → application authorization để tự quyết định quyền: cấm
- LLM → credential store: cấm
- tool → tự bypass AuthorizationService: cấm

## 10. Configuration boundary
`.env`/secret store chỉ cấp configuration và secret cho module cần thiết. Không đưa credential vào AgentContext, prompt, log, audit payload hoặc tool run metadata.

## 11. Test boundary
Mọi capability protected phải có owner ALLOW, delegated account ALLOW, denied account DENY, credential chưa resolve khi DENY và provider API không gọi khi DENY.

V2.1 bổ sung test organization isolation, resource hierarchy, device → resource, activity session, task → activity, agent → agent permission và anomaly → evidence.

## 12. Không tạo file chỉ để có đủ cây
Source tree này là target architecture. File chỉ được tạo khi phase tương ứng bắt đầu.