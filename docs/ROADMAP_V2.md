# Workspace AI Agent — ROADMAP V2.1

> Roadmap implementation chính thức. Không triển khai phase sau khi gate của phase trước chưa đạt.

## Phase 0 — Documentation / Blueprint
- Chốt Architecture V2.1.
- Chốt Core Contracts V2.1.
- Chốt Database V2.1.
- Chốt Authorization, Accounts và Data Package.
- Chốt Source Tree.
- Chưa tạo migration hoặc application business code.

## Phase 1 — Core Foundation
- PostgreSQL connection/session boundary.
- users, organizations, organization_members, user_sessions.
- Authentication.
- Organization/Tenant context.
- AgentContext.
- Request ID / trace context.
- Core error/result contract.
- Contract tests.
- Chưa triển khai Google, Qdrant, CrewAI hoặc device workflow.

### Phase 1 gate
- Organization isolation test.
- Session/authentication test.
- AgentContext không chứa secret.
- Membership không tự cấp application permission.
- Migration/FK integrity test.

## Phase 2 — Accounts / Resources / Authorization
- user_accounts, account_credentials.
- roles, permissions, role_permissions, user_roles.
- account_grants.
- resources + parent/child hierarchy.
- resource_permissions.
- resources.user_account_id và provider/account consistency.
- AccountResolver, CredentialResolver, AuthorizationService.
- Provider base contract.

### Phase 2 gate
- Owner ALLOW.
- Delegated account ALLOW.
- Unauthorized user DENY.
- Credential không được resolve khi DENY.
- Provider/tool không được gọi khi DENY.
- Parent resource không thể trỏ sang organization khác.

## Phase 3 — Data Package
- Package/version.
- Resource membership.
- Package grants.
- Package resolver.
- Authorization kết hợp capability + account + resource + package.

## Phase 5 — Capability / Tool / Additional Provider
- Capability registry.
- Tool definition/registry/resolver.
- Google provider adapter.
- Gmail / Drive / Calendar tools.
- Audit + run trace.

### Phase 4 gate
- Multi-account Google.
- Account selection/default policy.
- Provider error/rate-limit handling.
- Audit trace đầy đủ.
- Credential boundary được kiểm chứng.

## Phase 4 — Knowledge Systematization Agent (first Agent capability)
- Ingestion pipeline.
- Knowledge document/chunk metadata and versioning.
- Normalize → chunk → embedding → Qdrant.
- Authorized retrieval/filter.
- Google first; then Facebook, TikTok, Instagram.
- Answer and summarize from ingested knowledge.
- Do not live-query providers for every question when knowledge is already indexed.

### Knowledge gate
- Không retrieve dữ liệu ngoài authorization scope.
- Qdrant payload có tenant/resource/account/package context cần thiết.
- SQL vẫn là source of truth cho ownership/access.

## Phase 6 — Devices / Events / Activity
- Device registry.
- Device ↔ Organization ↔ Resource binding.
- Device capabilities.
- Observation.
- Event.
- Activity Session.
- Activity.

## Phase 7 — Tasks / Agents / Agent-to-Agent
- Task / Work Order.
- General / Knowledge / Activity / Device Agent.
- Agent runs / Tool runs.
- Agent-to-Agent Message / Task / Permission.
- Agent execution vẫn qua Application + Authorization boundary.

## Phase 8 — Anomaly / Automation
- Anomaly + evidence.
- Automation trigger/condition/action.
- Approval, retry/idempotency khi capability cần.

## Phase 9 — Additional Providers
- Meta/Facebook.
- Zalo.
- Telegram.
- Home Assistant.

## Phase 10 — Scale
- workers/queue.
- event bus.
- caching.
- high-volume device ingestion.
- distributed processing.
- partition/archive.

## Framework boundary
LangChain/CrewAI chỉ được đưa vào khi Core Contracts đã chạy ổn định. Framework không sở hữu authorization, credential access hoặc tenant isolation.

## Migration gate

ARCHITECTURE V2.1
  ↓
CORE CONTRACTS V2.1
  ↓
DATABASE_V2_DETAILED.md
  ↓
ERD_V2.md
  ↓
FK / UNIQUE / CHECK
  ↓
INDEX
  ↓
MIGRATION ORDER
  ↓
PostgreSQL migration
  ↓
Phase 1 implementation
  ↓
Runtime verification

## Nguyên tắc rollout
Không thêm domain chỉ để làm cây thư mục đầy đủ. Mỗi capability mới phải đi qua: Decision → Domain design → Database contract → Migration → Runtime verification.
