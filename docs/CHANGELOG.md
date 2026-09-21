# CHANGELOG

## 2026-09-20 — Architecture V2 documentation reset

Repository đã được làm sạch và khởi tạo lại lớp tài liệu kiến trúc V2.

### Added

- `docs/ARCHITECTURE.md` — Architecture V2 Final blueprint.
- `docs/DATABASE.md` — Database V2 blueprint.
- `docs/AUTHORIZATION.md` — Authorization model.
- `docs/ACCOUNTS.md` — External Account model.
- `docs/DATA_PACKAGES.md` — Data Package / Resource Access model.
- `docs/DEVICES.md` — Device architecture.
- `docs/EVENTS.md` — Observation/Event/Activity model.
- `docs/MEMORY.md` — Memory boundaries.
- `docs/KNOWLEDGE.md` — Knowledge/Qdrant architecture.
- `docs/AGENTS.md` — Agent architecture.
- `docs/TOOLS.md` — Capability/Tool architecture.
- `docs/PROVIDERS.md` — Provider/adapter architecture.
- `docs/AUTOMATION.md` — Event-driven automation plan.
- `docs/ROADMAP_V2.md` — Ordered implementation roadmap.

### Important

Đây là phase **documentation only**. Không có code application/database được tạo trong phase này.

Các quyết định đã chốt được đưa vào blueprint để làm nguồn tham chiếu trước khi bắt đầu implementation.

### Next gate

Trước khi code:

1. Review Architecture V2.
2. Review Database V2.
3. Đối chiếu với yêu cầu thực tế.
4. Chốt schema/migration plan.
5. Sau đó mới triển khai Phase 1.


## 2026-09-21 07:36:00 +07:00

### Finalize Architecture V2 blueprint

- Hoàn thiện request lifecycle và authorization boundary.
- Khóa quy tắc credential chỉ được lấy sau Authorization ALLOW.
- Hoàn thiện database conventions: ID, time, FK, unique, index và metadata.
- Bổ sung Decision Log 001–017.
- Bổ sung Runtime Contract và runtime gate.
- Bổ sung Security V2 cho credential, logging, data isolation và webhook.
- Chưa tạo application code hoặc database migration.
