# Knowledge V2

## Pipeline

```text
Source
 ↓
Document
 ↓
Normalize
 ↓
Chunk
 ↓
Embedding
 ↓
Qdrant
```

## SQL vs Qdrant

SQL giữ:

- document metadata;
- source/resource;
- ownership;
- package/access mapping;
- version/checksum;
- Qdrant point id.

Qdrant giữ vector và dữ liệu phục vụ similarity retrieval.

## Sources dự kiến

- Google Drive
- Gmail attachments
- Facebook data
- Zalo/Telegram khi provider được triển khai
- uploaded documents
- device-generated documents/images

## Ingestion

Provider ingestion phải chuẩn hóa dữ liệu trước khi index. Ingestion không được tự mở quyền truy cập cho user.

## Search

Knowledge search phải chạy trong authorization context để tránh retrieval chéo dữ liệu không được phép.
