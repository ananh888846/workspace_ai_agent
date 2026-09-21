# Roadmap V2

## Phase 0 — Documentation / Blueprint

- Chốt Architecture V2.
- Chốt Database V2.
- Chốt Authorization.
- Chốt Account model.
- Chốt Data Package.
- Chưa code business logic.

## Phase 1 — Foundation / Core Contracts

Trước implementation, tạo source tree theo `docs/SOURCE_TREE_V2.md` và khóa interface theo `docs/CORE_CONTRACTS_V2.md`.

- source tree
- dependency direction
- AgentContext
- AuthenticationService
- AuthorizationService
- AccountResolver
- CredentialResolver
- ResourceAccessChecker
- DataPackageResolver
- CapabilityRegistry
- ToolResolver
- ProviderAdapter
- AuditService

## Phase 1 — Foundation

- identity
- session
- AgentContext
- request id

## Phase 2 — Accounts

- user_accounts
- credentials
- AccountResolver
- Google provider đầu tiên

## Phase 3 — Authorization

- roles
- permissions
- account grants
- resources
- resource permissions

## Phase 4 — Data Package

- package
- version
- resource membership
- grants
- resolver

## Phase 5 — Capability / Tool

- capability registry
- ToolDefinition
- ToolResolver
- Google Gmail/Drive/Calendar

## Phase 6 — Runtime verification

Kiểm tra runtime thực tế trước khi mở rộng:

1. application startup;
2. Drive search/read;
3. Gmail search/read;
4. Calendar;
5. nhiều Google Account;
6. account delegation;
7. Data Package access;
8. audit/trace.

## Phase 7 — Knowledge

- ingestion
- document/chunk metadata
- embedding
- Qdrant
- authorized retrieval

## Phase 8 — Devices / Events

- device registry
- ESP32-CAM
- observations
- events
- activities

## Phase 9 — Agents

- General Agent
- Knowledge Agent
- Activity Agent
- Device Agent

## Phase 10 — LangChain / CrewAI

- LangChain primitives
- RAG/tool calling
- CrewAI multi-agent workflow

## Phase 11 — Automation

- triggers
- conditions
- actions
- scheduler/retry khi cần

## Phase 12 — Additional Providers

- Facebook/Meta
- Zalo
- Telegram
- Home Assistant

## Phase 13 — Scale

Chỉ sau khi runtime ổn định mới cân nhắc queue/event bus, caching, workers, webhook sync, distributed processing và high-volume device ingestion.

## Nguyên tắc rollout

Không triển khai phase sau khi phase trước chưa có test/verification phù hợp. Không thêm provider chỉ để tăng số lượng trong khi authorization và data package chưa ổn định.
