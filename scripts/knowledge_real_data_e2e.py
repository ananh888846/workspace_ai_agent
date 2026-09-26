from __future__ import annotations

"""Local operator E2E for real PostgreSQL + Qdrant Knowledge data.

This command ingests one real local Markdown/text file, verifies the canonical
PostgreSQL version and exact Qdrant chunk index, then queries the real Agent API.
The data is intentionally kept after the run.
"""

import argparse
import hashlib
import os
import sys
from pathlib import Path
from uuid import uuid4

import httpx
import psycopg

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.application.knowledge.ingest import KnowledgeIngestionService
from app.domain.knowledge.source import KnowledgeSourceItem
from app.infrastructure.database.repositories.knowledge import PostgresKnowledgeRepository
from app.infrastructure.database.repositories.knowledge_authorization import (
    PostgresKnowledgeAuthorizationRepository,
)
from app.infrastructure.knowledge.ollama_embedding import OllamaEmbeddingProvider
from app.infrastructure.knowledge.qdrant import QdrantVectorIndex


class ParagraphChunker:
    def chunk(self, content: str) -> list[str]:
        return [part.strip() for part in content.split("\n\n") if part.strip()]


class AllowLocalIngestion:
    """Local-only adapter; query permission is verified before ingestion."""

    def authorize_ingestion(self, **_: object) -> bool:
        return True


def required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ingest a real local file and query it through Knowledge Agent."
    )
    parser.add_argument("--file", required=True, help="Path to a real .md/.txt file")
    parser.add_argument("--query", required=True, help="Question whose answer is in the file")
    parser.add_argument("--external-id", default=None)
    parser.add_argument("--title", default=None)
    parser.add_argument("--max-results", type=int, default=5)
    args = parser.parse_args()

    path = Path(args.file).expanduser().resolve()
    if not path.is_file():
        raise SystemExit(f"File not found: {path}")

    content = path.read_text(encoding="utf-8")
    if not content.strip():
        raise SystemExit(f"File is empty: {path}")

    organization_id = required_env("KNOWLEDGE_REAL_ORGANIZATION_ID")
    user_id = required_env("KNOWLEDGE_REAL_USER_ID")
    agent_token = required_env("AGENT_SERVER_TOKEN")
    agent_base_url = os.getenv("AGENT_BASE_URL", "http://127.0.0.1:8000")
    external_id = args.external_id or f"local-file:{path.as_posix()}"
    title = args.title or path.name
    checksum = hashlib.sha256(content.encode("utf-8")).hexdigest()

    print("=== Knowledge Real-Data E2E ===")
    print(f"file: {path}")
    print(f"organization_id: {organization_id}")
    print(f"user_id: {user_id}")
    print(f"external_id: {external_id}")
    print(f"bytes: {len(content.encode('utf-8'))}")

    with psycopg.connect(required_env("DATABASE_URL")) as connection:
        authorization = PostgresKnowledgeAuthorizationRepository(connection)
        if not authorization.authorize_query(
            user_id=user_id, organization_id=organization_id
        ):
            raise SystemExit(
                "The supplied user does not have knowledge.read in this organization."
            )

        repository = PostgresKnowledgeRepository(connection)
        qdrant = QdrantVectorIndex(
            base_url=os.getenv("QDRANT_URL", "http://127.0.0.1:6333"),
            collection=os.getenv("QDRANT_COLLECTION", "knowledge_v1"),
        )
        embedding = OllamaEmbeddingProvider(
            base_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
            model=os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text-v2-moe"),
        )

        item = KnowledgeSourceItem(
            organization_id=organization_id,
            user_account_id=None,
            provider="local_file",
            resource_type="document",
            external_id=external_id,
            content=content,
            source_checksum=checksum,
            title=title,
            mime_type="text/plain",
            source_revision=str(path.stat().st_mtime_ns),
        )

        result = KnowledgeIngestionService(
            repository=repository,
            authorization=AllowLocalIngestion(),
            chunker=ParagraphChunker(),
            embedding=embedding,
            vector_index=qdrant,
        ).ingest(item)

        print("ingestion:", {
            "status": result.status,
            "source_id": result.source_id,
            "document_version_id": result.document_version_id,
            "chunk_count": result.chunk_count,
        })

        if not result.source_id or not result.document_version_id:
            raise RuntimeError("Ingestion did not return source/version IDs")

        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT status, version_no FROM knowledge_document_versions
                   WHERE id = %s AND organization_id = %s""",
                [result.document_version_id, organization_id],
            )
            version = cursor.fetchone()
            cursor.execute(
                """SELECT COUNT(*) FROM knowledge_chunks
                   WHERE document_version_id = %s AND organization_id = %s""",
                [result.document_version_id, organization_id],
            )
            chunk_count = int(cursor.fetchone()[0])

        print("postgres:", {
            "version_status": version[0] if version else None,
            "version_no": version[1] if version else None,
            "chunk_count": chunk_count,
        })

        if not version or version[0] != "active":
            raise RuntimeError("PostgreSQL active version verification failed")
        if chunk_count != result.chunk_count:
            raise RuntimeError("PostgreSQL chunk count does not match ingestion")

        indexed = qdrant.is_indexed(
            result.document_version_id, result.chunk_count
        )
        print(f"qdrant_index_complete: {indexed}")
        if not indexed:
            raise RuntimeError("Qdrant index is incomplete")

        version_id = result.document_version_id

    request_id = str(uuid4())
    response = httpx.post(
        f"{agent_base_url.rstrip('/')}/api/v1/agent/chat",
        headers={
            "Authorization": f"Bearer {agent_token}",
            "X-Request-Id": request_id,
            "X-User-Id": user_id,
            "X-Organization-Id": organization_id,
            "Content-Type": "application/json",
        },
        json={"message": args.query, "max_results": args.max_results},
        timeout=120.0,
    )
    response.raise_for_status()
    payload = response.json()

    print("agent.status:", payload.get("status"))
    print("agent.execution:", payload.get("execution"))
    print("agent.provider_called:", payload.get("provider_called"))

    results = payload.get("data", {}).get("results", [])
    print(f"agent.result_count: {len(results)}")
    for index, item in enumerate(results, start=1):
        print(f"--- result {index} ---")
        print(f"score={item.get('score')}")
        print(f"document_version_id={item.get('document_version_id')}")
        print(f"chunk_index={item.get('chunk_index')}")
        print(f"content={item.get('content')}")

    if payload.get("status") != "ok":
        raise RuntimeError(f"Agent Knowledge request failed: {payload}")
    if not results:
        raise RuntimeError(
            "Agent returned no Knowledge results although PostgreSQL/Qdrant verification passed."
        )
    if not any(item.get("document_version_id") == version_id for item in results):
        raise RuntimeError("Agent did not return the ingested document version")

    print("REAL KNOWLEDGE E2E PASSED")
    print("Data was intentionally kept in PostgreSQL and Qdrant.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
