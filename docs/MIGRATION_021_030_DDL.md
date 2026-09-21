# Migration 021 → 030 — DDL Design V2.1

> Design only. Chưa phải SQL production và chưa chạy database thật.
>
> Source of truth: `DATABASE_V2_DETAILED.md`, `MIGRATION_CONTRACT_V2.md`, `ERD_V2.md`.
>
> Nhóm này nối Observation/Event → Activity → Task → Conversation/Memory → Knowledge/Qdrant.

## 1. Phạm vi

021 observations  
022 events  
023 activity_sessions  
024 activities  
025 tasks  
026 conversations  
027 messages  
028 memories  
029 knowledge_documents  
030 knowledge_chunks

## 2. Migration 021 — observations

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| device_id | UUID | NO | — | FK, INDEX |
| observation_type | VARCHAR(100) | NO | — | INDEX |
| raw_data | JSONB | NO | {} | |
| confidence | NUMERIC(5,4) | YES | NULL | |
| created_at | TIMESTAMPTZ | NO | now() | INDEX |

Required:
- device_id → devices.id
- CHECK confidence BETWEEN 0 AND 1 when present
- INDEX(device_id, created_at)

Observation is raw/derived input, not automatically a business fact.

Delete policy: RESTRICT. Historical observations must not disappear through device deletion.

## 3. Migration 022 — events

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| event_uuid | UUID | NO | — | UNIQUE |
| event_type | VARCHAR(100) | NO | — | INDEX |
| organization_id | UUID | NO | — | FK, INDEX |
| user_id | UUID | YES | NULL | FK, INDEX |
| device_id | UUID | YES | NULL | FK, INDEX |
| source_type | VARCHAR(64) | NO | — | |
| source_id | UUID | YES | NULL | |
| resource_id | UUID | YES | NULL | FK, INDEX |
| occurred_at | TIMESTAMPTZ | NO | — | INDEX |
| confidence | NUMERIC(5,4) | YES | NULL | |
| status | VARCHAR(32) | NO | detected | INDEX |
| metadata | JSONB | NO | {} | |
| created_at | TIMESTAMPTZ | NO | now() | INDEX |

Required integrity:
- organization_id → organizations.id
- user_id → users.id when present
- device_id → devices.id when present
- resource_id → resources.id when present
- CHECK confidence BETWEEN 0 AND 1 when present
- event_uuid UNIQUE for idempotent ingestion

Tenant rule:
- Any non-null device/resource reference must belong to event.organization_id.
- If DB composite keys are used, add UNIQUE(id, organization_id) to target tenant tables and composite FKs; otherwise use an equivalent database-level constraint.

Indexes:
- (organization_id, occurred_at)
- (organization_id, event_type, occurred_at)
- (device_id, occurred_at)
- (resource_id, occurred_at)

Delete policy: RESTRICT for organization/user/device/resource because events are historical trace.

## 4. Migration 023 — activity_sessions

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| organization_id | UUID | NO | — | FK, INDEX |
| user_id | UUID | YES | NULL | FK, INDEX |
| resource_id | UUID | YES | NULL | FK, INDEX |
| session_type | VARCHAR(100) | NO | — | INDEX |
| started_at | TIMESTAMPTZ | NO | — | INDEX |
| ended_at | TIMESTAMPTZ | YES | NULL | |
| duration_seconds | INTEGER | YES | NULL | |
| status | VARCHAR(32) | NO | active | INDEX |
| confidence | NUMERIC(5,4) | YES | NULL | |
| source_event_id | UUID | YES | NULL | FK, INDEX |
| metadata | JSONB | NO | {} | |
| created_at | TIMESTAMPTZ | NO | now() | INDEX |
| updated_at | TIMESTAMPTZ | NO | now() | |

Required:
- organization_id → organizations.id
- user_id → users.id
- resource_id → resources.id
- source_event_id → events.id
- CHECK ended_at >= started_at when ended_at is present
- CHECK duration_seconds >= 0
- CHECK confidence BETWEEN 0 AND 1

Tenant references must match organization_id at DB level.

Indexes:
- (organization_id, started_at)
- (organization_id, status, started_at)
- (user_id, started_at)
- (resource_id, started_at)

Delete policy: RESTRICT for event/resource/user; no automatic deletion of activity history.

## 5. Migration 024 — activities

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| organization_id | UUID | NO | — | FK, INDEX |
| user_id | UUID | YES | NULL | FK, INDEX |
| activity_type | VARCHAR(100) | NO | — | INDEX |
| resource_id | UUID | YES | NULL | FK, INDEX |
| started_at | TIMESTAMPTZ | NO | — | INDEX |
| ended_at | TIMESTAMPTZ | YES | NULL | |
| status | VARCHAR(32) | NO | active | INDEX |
| confidence | NUMERIC(5,4) | YES | NULL | |
| source_event_id | UUID | YES | NULL | FK, INDEX |
| activity_session_id | UUID | YES | NULL | FK, INDEX |
| metadata | JSONB | NO | {} | |
| created_at | TIMESTAMPTZ | NO | now() | INDEX |

Required:
- organization_id → organizations.id
- user_id → users.id when present
- resource_id → resources.id when present
- source_event_id → events.id when present
- activity_session_id → activity_sessions.id when present
- all tenant-scoped references must match organization_id
- CHECK ended_at >= started_at
- CHECK confidence BETWEEN 0 AND 1

Indexes:
- (organization_id, started_at)
- (organization_id, activity_type, started_at)
- (activity_session_id, started_at)

Activity is an interpretation/domain record. It must retain source linkage; inference does not automatically make it fact.

Delete policy: RESTRICT.

## 6. Migration 025 — tasks

The exact Task/Work Order columns are taken from the V2.1 contract. Task must remain separate from Activity.

Required logical fields:
- id UUID PK
- organization_id UUID NOT NULL
- created_by/user or actor reference according to final Task contract
- title/type/action fields
- status
- priority
- requested/started/completed timestamps
- activity_session/activity reconciliation references where applicable
- result/error metadata
- created_at/updated_at

Mandatory constraints:
- organization_id → organizations.id
- tenant-scoped references use composite tenant FK/equivalent constraint
- CHECK completed_at >= started_at when both exist
- CHECK priority/weight ranges where defined by the Task contract
- indexes on (organization_id, status, created_at), (organization_id, priority, status), and lifecycle timestamps

Delete policy: RESTRICT for business history. A completed task is historical work and must not disappear because an actor/resource is removed.

Implementation note:
The production SQL must use the exact Task column list from the current Task contract before implementation; this document intentionally does not invent additional columns that are not present in the source-of-truth schema.

## 7. Migration 026 — conversations

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| user_id | UUID | NO | — | FK, INDEX |
| session_id | UUID | YES | NULL | FK, INDEX |
| title | VARCHAR(500) | YES | NULL | |
| status | VARCHAR(32) | NO | active | INDEX |
| created_at | TIMESTAMPTZ | NO | now() | INDEX |
| updated_at | TIMESTAMPTZ | NO | now() | |

Required:
- user_id → users.id
- session_id → user_sessions.id when present
- INDEX(user_id, updated_at)

Conversation belongs to a User. Organization membership is not substituted for user ownership here.

Delete policy: RESTRICT because conversation history is source material for memory/audit/runtime trace.

## 8. Migration 027 — messages

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| conversation_id | UUID | NO | — | FK, INDEX |
| role | VARCHAR(32) | NO | — | INDEX |
| content | TEXT | NO | — | |
| model | VARCHAR(100) | YES | NULL | |
| tokens | INTEGER | YES | NULL | |
| created_at | TIMESTAMPTZ | NO | now() | INDEX |

Required:
- conversation_id → conversations.id
- CHECK tokens >= 0 when present
- INDEX(conversation_id, created_at)
- INDEX(role, created_at) only if runtime analytics needs it

Message is conversation history, not automatically memory.

Security:
- Never store credentials, access tokens, refresh tokens or encryption keys in content.
- Provider/API secrets must not be copied into messages.

Delete policy: RESTRICT from conversation.

## 9. Migration 028 — memories

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| user_id | UUID | NO | — | FK, INDEX |
| memory_type | VARCHAR(64) | NO | — | INDEX |
| content | TEXT | NO | — | |
| importance | NUMERIC(5,4) | YES | NULL | |
| source_conversation_id | UUID | YES | NULL | FK, INDEX |
| status | VARCHAR(32) | NO | active | INDEX |
| created_at | TIMESTAMPTZ | NO | now() | |
| updated_at | TIMESTAMPTZ | NO | now() | |

Required:
- user_id → users.id
- source_conversation_id → conversations.id
- CHECK importance BETWEEN 0 AND 1 when present
- INDEX(user_id, status, updated_at)

Memory lifecycle:
- A message may become a memory only through an explicit memory extraction/decision step.
- Memory must retain source conversation when known.
- Memory does not grant access to Knowledge or external resources.

Delete policy: RESTRICT for user/source conversation unless a future privacy-erasure policy explicitly defines a controlled workflow.

## 10. Migration 029 — knowledge_documents

Knowledge authorization is inherited from the source Resource when resource_id is present.

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| resource_id | UUID | YES | NULL | FK, INDEX |
| title | VARCHAR(500) | YES | NULL | |
| source_type | VARCHAR(64) | NO | — | INDEX |
| source_id | VARCHAR(255) | YES | NULL | |
| version | VARCHAR(100) | NO | — | |
| checksum | VARCHAR(255) | NO | — | INDEX |
| status | VARCHAR(32) | NO | active | INDEX |
| created_at | TIMESTAMPTZ | NO | now() | |
| updated_at | TIMESTAMPTZ | NO | now() | |

Required:
- resource_id → resources.id when present
- candidate UNIQUE(source_type, source_id, version, checksum)
- provider-specific uniqueness must be finalized by provider contract

Knowledge ingestion rule:
- SQL is source of truth for document metadata, resource ownership, authorization and version.
- Qdrant is not an authorization source.
- If resource_id is present, retrieval authorization must resolve the Resource/Package boundary before returning chunks.
- A document without resource_id requires an explicit future authorization contract before production use.

Delete policy: RESTRICT.

Indexes:
- resource_id
- (source_type, source_id)
- checksum
- (status, updated_at)

## 11. Migration 030 — knowledge_chunks

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| document_id | UUID | NO | — | FK, INDEX |
| chunk_index | INTEGER | NO | — | |
| content_hash | VARCHAR(255) | NO | — | INDEX |
| qdrant_point_id | VARCHAR(255) | NO | — | UNIQUE |
| token_count | INTEGER | YES | NULL | |
| created_at | TIMESTAMPTZ | NO | now() | |

Required:
- document_id → knowledge_documents.id
- UNIQUE(document_id, chunk_index)
- UNIQUE(qdrant_point_id)
- CHECK chunk_index >= 0
- CHECK token_count >= 0 when present

Qdrant contract:
- SQL chunk id/document id remains the authoritative mapping.
- qdrant_point_id identifies the external vector point.
- Qdrant payload must not be treated as the final authorization source.
- Retrieval flow: authenticate → resolve organization/user → authorize resource/package → query Qdrant → verify mapped SQL metadata → return authorized chunks.

Delete policy:
- Chunk mapping may be deleted/rebuilt as part of controlled document re-indexing.
- Production implementation must remove/replace the corresponding Qdrant point in the same indexing workflow; database deletion alone must not leave stale authorized vectors.

Indexes:
- document_id
- content_hash
- qdrant_point_id UNIQUE

## 12. Dependency order

021 observations
→ 022 events
→ 023 activity_sessions
→ 024 activities
→ 025 tasks
→ 026 conversations
→ 027 messages
→ 028 memories
→ 029 knowledge_documents
→ 030 knowledge_chunks

Important:
- observations needs devices.
- events needs organizations/users/devices/resources.
- activity_sessions needs events/resources/users.
- activities needs activity_sessions/events/resources/users.
- tasks follows the finalized Task contract and may reference Activity Session/Activity.
- conversations needs users/user_sessions.
- messages needs conversations.
- memories needs users/conversations.
- knowledge_documents needs resources.
- knowledge_chunks needs knowledge_documents.

## 13. Acceptance tests

AT-021 Observation for nonexistent device → FK REJECT.
AT-022 Event with device/resource from another organization → REJECT.
AT-023 Activity Session with cross-tenant resource/event → REJECT.
AT-024 Activity with cross-tenant session/resource/event → REJECT.
AT-025 Invalid activity time range → CHECK REJECT.
AT-026 Message referencing nonexistent conversation → FK REJECT.
AT-027 Negative message token count → CHECK REJECT.
AT-028 Memory importance outside [0,1] → CHECK REJECT.
AT-029 Knowledge document references nonexistent resource → FK REJECT.
AT-030 Duplicate document chunk index or Qdrant point id → UNIQUE REJECT.

Runtime authorization tests:
- Unauthorized user querying Knowledge must receive zero unauthorized chunks.
- Qdrant payload alone must never grant access.
- Removing/revoking Resource/Package access must immediately affect retrieval authorization even if Qdrant vectors still exist.
- Provider fetch is not part of Knowledge retrieval authorization.

## 14. Implementation gate

- [x] Observation/Event separation is explicit.
- [x] Event is tenant-scoped.
- [x] Activity Session and Activity preserve source/lifecycle relationships.
- [x] Conversation and Message are separate history layers.
- [x] Memory is explicit and does not equal conversation history.
- [x] Knowledge document/chunk mapping is explicit.
- [x] Qdrant is retrieval storage, not authorization source.
- [x] Cross-tenant Event/Activity references require DB-level enforcement.
- [x] Temporal and confidence/importance/token/chunk checks are defined where source schema specifies them.
- [x] Secrets are prohibited from conversation/tool/knowledge content.
- [ ] Exact Task column list must be confirmed from the finalized Task source-of-truth before production SQL is generated.
- [x] No production SQL, database, provider call or runtime code is introduced.

Kết luận: Migration 021 → 030 đã được thiết kế ở mức DDL contract. Trước SQL implementation, Task schema phải được chốt đúng theo source-of-truth hiện hành; không tự mở rộng schema trong bước SQL.
