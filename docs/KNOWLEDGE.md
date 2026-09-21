# Workspace AI Agent — KNOWLEDGE V1 / V2.1

## Pipeline

Knowledge Systematization Agent is the first Agent capability. V1 starts with Google, then expands to Facebook, TikTok and Instagram.

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
- Facebook/Meta, TikTok, Instagram when their provider contracts are approved
- uploaded documents
- device-generated documents/images

## Ingestion

Provider ingestion phải chuẩn hóa dữ liệu trước khi index. Ingestion không được tự mở quyền truy cập cho user.

## Search

Knowledge search phải chạy trong authorization context để tránh retrieval chéo dữ liệu không được phép.
