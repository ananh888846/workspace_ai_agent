# Workspace AI Agent — KNOWLEDGE SOURCE CONTRACT V1

> Status: Design locked — 2026-09-21

Contract chung cho mọi provider đưa dữ liệu vào Knowledge Systematization Agent.

## 1. Mục tiêu
Provider adapter phải chuyển dữ liệu riêng của provider thành một canonical KnowledgeSourceItem. Agent Core không biết API schema riêng của Google, Facebook, TikTok hoặc Instagram.

## 2. Canonical source item
~~~text
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
├── canonical_url?
├── author?
├── published_at?
├── updated_at?
├── source_revision?
├── source_checksum
├── language?
├── metadata
└── deleted
~~~
Binary source có thể có một hoặc nhiều asset reference. Binary không nằm trực tiếp trong canonical text content.

## 3. Identity
Identity chính: organization_id + user_account_id + provider + resource_type + external_id.
external_id phải ổn định trong provider. Không dùng title/name hoặc URL làm identity duy nhất.

## 4. Source URL và canonical URL
source_url là URL được người dùng, tool hoặc event phát hiện ban đầu.
canonical_url là URL chuẩn sau khi resolver/provider adapter xử lý share URL, redirect hoặc canonical resource URL nếu có.
Ví dụ:
~~~text
source_url    = https://www.facebook.com/share/r/18EZRZymHJ/
canonical_url = https://www.facebook.com/reel/<resolved-id>
~~~
Nếu không resolve được canonical URL thì vẫn giữ source URL.

## 5. Account binding
user_account_id phải trỏ đến external account đã đăng ký. Một user có thể có nhiều account cùng provider.
Account selection nằm ở AccountResolver; authorization nằm ở AuthorizationService.

## 6. Resource binding
Nếu source item tương ứng với resource đã có, adapter phải map về resource đó.
Nếu resource chưa tồn tại, resource provisioning phải chạy qua application resource service với tenant/provider/account consistency rules đã khóa trong Database V2.1.

## 7. Content
content là nội dung canonical để normalize/chunk/embed.
Không đưa access token, refresh token, API key, cookie/session secret, private credential hoặc internal authorization secret vào content.
Binary/image/audio phải được lưu qua StorageService và có asset metadata/reference. Extracted text, OCR, transcript hoặc vision description có thể trở thành canonical knowledge content.

## 8. Revision và checksum
Provider nên cung cấp source_revision hoặc equivalent. Pipeline luôn tạo source_checksum từ canonical normalized content + metadata cần thiết theo policy.
~~~text
same revision/checksum → unchanged
changed revision/checksum → new version
~~~

## 9. Delete semantics
deleted=true biểu diễn source đã bị xóa/thu hồi. Delete không được xóa audit history.

## 10. Metadata
Metadata phải JSON-safe và không chứa secret. Có thể gồm provider labels, folder/path, post/video/article identifiers, language, author display name, source timestamps, extraction method, parser version và asset references.

## 11. Provenance
~~~text
knowledge document/version
 ↓
source provenance
 ↓
organization → user account → provider → resource → external_id
 ↓
source_url / canonical_url
~~~
Một derived/aggregated knowledge item có thể có nhiều source provenance records.

## 12. Provider mapping
Google Drive: provider=google_drive; external file id→external_id; mimeType→mime_type; name→title; modifiedTime→updated_at; webViewLink→source_url.
Facebook/Meta: canonical mapping phụ thuộc capability/API cụ thể.
TikTok: video/post/content object phải được map theo API object identity và capability được cấp.
Instagram: media/post object phải có external ID ổn định và giữ đúng account context.

## 13. Error contract
authentication_error; authorization_denied; resource_not_found; rate_limited; provider_unavailable; invalid_source; unsupported_type; internal_error.
Không expose credential hoặc raw secret trong error.

## 14. Contract invariants
1. Provider adapter không cấp authorization.
2. Provider adapter không tự resolve secret ngoài CredentialResolver.
3. Provider adapter không gọi Agent Core ngược vòng.
4. Cùng input canonical phải cho cùng identity.
5. Metadata không chứa secret.
6. Tenant/account context không được thay đổi trong normalize.
7. External provider errors không làm mất SQL state hiện có.
8. URL không thay thế identity/provenance model.
9. Binary phải đi qua StorageService abstraction.