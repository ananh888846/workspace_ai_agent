"""
Created/Updated: 2026-09-24 20:32 GMT+7
Main Function: Qdrant vector index adapter with tenant-filtered Knowledge retrieval.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import UUID, uuid5


class QdrantVectorStoreError(RuntimeError):
    """Raised when Qdrant rejects a vector operation."""


@dataclass
class QdrantVectorIndex:
    """Minimal Qdrant REST adapter for Knowledge V1.

    Qdrant is derived retrieval state. PostgreSQL remains canonical.
    """

    base_url: str
    collection: str
    timeout_seconds: float = 30.0
    _vector_size: int | None = None

    def _request(self, method: str, path: str, payload: dict | None = None):
        request = Request(
            f"{self.base_url.rstrip('/')}{path}",
            data=json.dumps(payload).encode("utf-8") if payload is not None else None,
            headers={"Content-Type": "application/json"} if payload is not None else {},
            method=method,
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read()
                return json.loads(raw.decode("utf-8")) if raw else {}
        except HTTPError as exc:
            raise QdrantVectorStoreError(f"qdrant_http_{exc.code}") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise QdrantVectorStoreError("qdrant_unavailable") from exc
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise QdrantVectorStoreError("qdrant_invalid_response") from exc

    def _ensure_collection(self, vector_size: int) -> None:
        if self._vector_size == vector_size:
            return
        try:
            existing = self._request(
                "GET", f"/collections/{self.collection}"
            )
        except QdrantVectorStoreError as exc:
            if "qdrant_http_404" not in str(exc):
                raise
            existing = None

        if existing is None:
            self._request(
                "PUT",
                f"/collections/{self.collection}",
                {"vectors": {"size": vector_size, "distance": "Cosine"}},
            )
        else:
            config = (
                existing.get("result", {})
                .get("config", {})
                .get("params", {})
                .get("vectors", {})
            )
            size = config.get("size") if isinstance(config, dict) else None
            if size is not None and int(size) != vector_size:
                raise QdrantVectorStoreError("qdrant_vector_dimension_mismatch")
        self._vector_size = vector_size

    def upsert(
        self,
        chunks: list[str],
        vectors: list[list[float]],
        document_version_id: str | None = None,
        organization_id: str | None = None,
    ) -> None:
        if len(chunks) != len(vectors):
            raise QdrantVectorStoreError("qdrant_chunk_vector_count_mismatch")
        if not vectors:
            return

        self._ensure_collection(len(vectors[0]))
        points = []
        namespace = UUID(document_version_id) if document_version_id else UUID(int=0)
        for index, (chunk, vector) in enumerate(zip(chunks, vectors)):
            point_id = str(uuid5(namespace, f"chunk:{index}"))
            points.append(
                {
                    "id": point_id,
                    "vector": vector,
                    "payload": {
                        "document_version_id": document_version_id,
                        "organization_id": organization_id,
                        "chunk_index": index,
                        "content": chunk,
                    },
                }
            )

        self._request(
            "PUT",
            f"/collections/{self.collection}/points?wait=true",
            {"points": points},
        )

    def search(
        self,
        vector: list[float],
        *,
        organization_id: str,
        limit: int,
    ):
        if not vector:
            return []
        if limit < 1:
            raise ValueError("limit_must_be_positive")
        payload = {
            "vector": vector,
            "limit": limit,
            "with_payload": True,
            "filter": {
                "must": [
                    {"key": "organization_id", "match": {"value": organization_id}}
                ]
            },
        }
        response = self._request(
            "POST",
            f"/collections/{self.collection}/points/search",
            payload,
        )
        points = response.get("result", [])
        from app.application.knowledge.retrieval import RetrievalCandidate
        return [
            RetrievalCandidate(
                point_id=str(point["id"]),
                score=float(point.get("score", 0.0)),
                content=str(point.get("payload", {}).get("content", "")),
                document_version_id=str(point.get("payload", {}).get("document_version_id", "")),
                chunk_index=int(point.get("payload", {}).get("chunk_index", 0)),
            )
            for point in points
        ]

    def is_indexed(self, document_version_id: str, expected_chunk_count: int) -> bool:
        """Return whether Qdrant contains exactly the expected chunk indexes.

        This is a derived-index health check. PostgreSQL remains canonical;
        a false result tells ingestion that the current version must be
        re-indexed on retry.
        """
        if expected_chunk_count < 0:
            raise ValueError("expected_chunk_count_must_be_non_negative")

        offset = None
        indexes: set[int] = set()
        while True:
            payload = {
                "limit": 1000,
                "with_payload": True,
                "with_vector": False,
                "filter": {
                    "must": [
                        {
                            "key": "document_version_id",
                            "match": {"value": document_version_id},
                        }
                    ]
                },
            }
            if offset is not None:
                payload["offset"] = offset

            response = self._request(
                "POST",
                f"/collections/{self.collection}/points/scroll",
                payload,
            )
            result = response.get("result", {})
            for point in result.get("points", []):
                payload_data = point.get("payload", {})
                indexes.add(int(payload_data.get("chunk_index", -1)))

            offset = result.get("next_page_offset")
            if offset is None:
                break

        return indexes == set(range(expected_chunk_count))

    def reconcile(
        self,
        document_version_id: str,
        active_chunk_indices: list[int] | None = None,
    ) -> None:
        """Remove stale chunks for one immutable document version.

        The caller supplies the canonical chunk indexes from PostgreSQL. The
        Qdrant scan is scoped to this version only, so reconciliation cannot
        delete another document or tenant's vectors.
        """
        if active_chunk_indices is None:
            return None
        active = set(active_chunk_indices)
        offset = None
        while True:
            payload = {
                "limit": 1000,
                "with_payload": True,
                "with_vector": False,
                "filter": {
                    "must": [
                        {
                            "key": "document_version_id",
                            "match": {"value": document_version_id},
                        }
                    ]
                },
            }
            if offset is not None:
                payload["offset"] = offset

            response = self._request(
                "POST",
                f"/collections/{self.collection}/points/scroll",
                payload,
            )
            result = response.get("result", {})
            points = result.get("points", [])
            stale_ids = [
                str(point["id"])
                for point in points
                if int(point.get("payload", {}).get("chunk_index", -1)) not in active
            ]
            if stale_ids:
                self._request(
                    "POST",
                    f"/collections/{self.collection}/points/delete?wait=true",
                    {"points": stale_ids},
                )

            offset = result.get("next_page_offset")
            if offset is None:
                break

    def delete_document_version(self, document_version_id: str) -> None:
        """Delete all derived points for one document version."""
        self._request(
            "POST",
            f"/collections/{self.collection}/points/delete?wait=true",
            {
                "filter": {
                    "must": [
                        {
                            "key": "document_version_id",
                            "match": {"value": document_version_id},
                        }
                    ]
                }
            },
        )
