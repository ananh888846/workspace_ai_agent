# Workspace AI Agent — KNOWLEDGE SOURCE CONTRACT V1

> **Status:** Design locked — 2026-09-21
>
> Contract chung cho mọi provider đưa dữ liệu vào Knowledge Systematization Agent.

## 1. Mục tiêu

Provider adapter phải chuyển dữ liệu riêng của provider thành một canonical `KnowledgeSourceItem`. Agent Core không biết API schema riêng của Google, Facebook, TikTok hoặc Instagram.

## 2. Canonical source item

```text
KnowledgeSourceItem
├── organization_id
├── user_account_id
├── provider
├── resource_type
├── external_id
├── parent_external_id?
├── title?
├── content
├── mime_type?
├── source_url?
├── author?
├── published_at?
├── updated_at?
├── source_revision?
├── source_checksum
├── language?
├── metadata
└── deleted
```

## 3. Identity

Identity chính:

```text
organization_id + user_account_id + provider + resource_type + external_id
```

`external_id` phải ổn định trong provider.

Không dùng title/name làm identity.

## 4. Account binding

`user_account_id` phải trỏ đến external account đã đăng ký.

Một user có thể có nhiều account cùng provider. Provider adapter không được tự suy diễn account từ prompt.

Account selection nằm ở AccountResolver; authorization nằm ở AuthorizationService.

## 5. Resource binding

Nếu source item tương ứng với resource đã có, adapter phải map về resource đó.

Nếu resource chưa tồn tại, resource provisioning phải chạy qua application resource service với tenant/provider/account consistency rules đã khóa trong Database V2.1.

Không tạo resource bằng cách bypass database integrity.

## 6. Content

`content` là nội dung canonical để normalize/chunk/embed.

Không đưa vào `content`:

- access token;
- refresh token;
- API key;
- cookie/session secret;
- private credential;
- internal authorization secret.

Binary/image/audio có thể có binary reference; pipeline V1 phải có extractor phù hợp trước khi embedding text.

## 7. Revision và checksum

Provider nên cung cấp `source_revision` hoặc equivalent.

Pipeline luôn tạo `source_checksum` từ canonical normalized content + các metadata cần thiết theo policy.

```text
same revision/checksum → unchanged
changed revision/checksum → new version
```

## 8. Delete semantics

`deleted=true` biểu diễn source đã bị xóa/thu hồi.

Delete không được xóa audit history. Pipeline phải mark/reconcile SQL state và remove hoặc tombstone Qdrant point theo retention policy.

## 9. Metadata

Metadata phải JSON-safe và không chứa secret.

Metadata có thể gồm:

- provider labels;
- folder/path;
- post/video/article identifiers;
- language;
- author display name;
- source timestamps;
- extraction method;
- parser version.

## 10. Provider mapping

### Google Drive

```text
provider = google_drive
a external file id → external_id
mimeType → mime_type
name → title
modifiedTime → updated_at
webViewLink → source_url
```

### Facebook/Meta

Canonical mapping phụ thuộc capability/API cụ thể. Không giả định mọi Facebook object đều có cùng schema hoặc cùng quyền truy cập.

### TikTok

Video/post/content object phải được map theo API object identity và capability được cấp.

### Instagram

Media/post object phải có external ID ổn định; adapter phải giữ đúng account context.

## 11. Error contract

Provider adapter chuẩn hóa lỗi thành:

- `authentication_error`
- `authorization_denied`
- `resource_not_found`
- `rate_limited`
- `provider_unavailable`
- `invalid_source`
- `unsupported_type`
- `internal_error`

Không expose credential hoặc raw secret trong error.

## 12. Contract invariants

1. Provider adapter không cấp authorization.
2. Provider adapter không tự resolve secret ngoài CredentialResolver.
3. Provider adapter không gọi Agent Core ngược vòng.
4. Cùng input canonical phải cho cùng identity.
5. Metadata không chứa secret.
6. Tenant/account context không được thay đổi trong normalize.
7. External provider errors không làm mất SQL state hiện có.
