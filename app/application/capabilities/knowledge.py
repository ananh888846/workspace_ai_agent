from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from app.application.execution_contract import build_execution_contract
from app.application.knowledge.authorized_retrieval import AuthorizedKnowledgeRetrievalService
from app.application.knowledge.retrieval import (
    KnowledgeRetrievalService,
    RerankedKnowledgeRetrievalService,
)
from app.infrastructure.database.connection import database_connection
from app.infrastructure.database.repositories.knowledge_authorization import (
    PostgresKnowledgeAuthorizationRepository,
)
from app.infrastructure.knowledge.ollama_embedding import OllamaEmbeddingProvider
from app.infrastructure.knowledge.qdrant import QdrantVectorIndex
from app.infrastructure.knowledge.bge_reranker import BGEReranker
from app.config.settings import get_settings


@dataclass(frozen=True)
class KnowledgeHandler:
    """Knowledge V1 read capability.

    Authorization is evaluated before embedding/Qdrant access. PostgreSQL is
    canonical for source/provenance metadata; Qdrant is derived retrieval
    state and is always tenant-filtered by organization_id.
    """

    def handle(self, state: dict) -> dict:
        payload = state["request"]
        context = state.get("context") or {}
        user_id = str(context.get("user_id") or "")
        organization_id = str(context.get("organization_id") or "")
        conversation_id = getattr(payload, "conversation_id", None) or str(uuid4())
        limit = max(int(getattr(payload, "max_results", 5)), 1)

        if not user_id or not organization_id:
            return self._error(
                conversation_id=conversation_id,
                intent="knowledge",
                capability="knowledge.read",
                action="read",
                code="authorization_denied",
                message="Knowledge authorization context is missing.",
            )

        settings = get_settings()
        with database_connection() as connection:
            authorization = PostgresKnowledgeAuthorizationRepository(connection)

            # Hard boundary: no embedding/Qdrant work before the canonical
            # PostgreSQL capability permission check.
            if not authorization.authorize_query(
                user_id=user_id,
                organization_id=organization_id,
            ):
                return self._error(
                    conversation_id=conversation_id,
                    intent="knowledge",
                    capability="knowledge.read",
                    action="read",
                    code="authorization_denied",
                    message="Knowledge read permission is not granted.",
                )

            embedding = OllamaEmbeddingProvider(
                base_url=settings.ollama_base_url,
                model=settings.ollama_embedding_model,
            )
            vector_index = QdrantVectorIndex(
                base_url=settings.qdrant_url,
                collection=settings.qdrant_collection,
            )
            retrieval = KnowledgeRetrievalService(
                embedding=embedding,
                vector_index=vector_index,
            )
            if settings.knowledge_reranker_enabled:
                retrieval_service = RerankedKnowledgeRetrievalService(
                    retrieval=retrieval,
                    reranker=BGEReranker(model_name=settings.knowledge_reranker_model),
                )
                candidate_limit = max(limit, 30)
            else:
                retrieval_service = retrieval
                candidate_limit = limit

            service = AuthorizedKnowledgeRetrievalService(
                retrieval=retrieval_service,
                authorization=authorization,
            )
            results = service.retrieve(
                payload.message,
                user_id=user_id,
                organization_id=organization_id,
                candidate_limit=candidate_limit,
                limit=limit,
            )

        return {
            "status": "ok",
            "conversation_id": conversation_id,
            "message": "Knowledge retrieval completed.",
            "data": {
                "results": [
                    {
                        "point_id": item.point_id,
                        "score": item.score,
                        "content": item.content,
                        "document_version_id": item.document_version_id,
                        "chunk_index": item.chunk_index,
                        "provider": item.provider,
                        "source_url": item.source_url,
                        "canonical_url": item.canonical_url,
                        "external_id": item.external_id,
                        "source_id": item.source_id,
                    }
                    for item in results
                ],
            },
            "execution": build_execution_contract(
                intent="knowledge",
                capability="knowledge.read",
                action="read",
                authorization={"status": "allow"},
                provider_called=True,
            ),
            "provider_called": True,
        }

    @staticmethod
    def _error(
        *,
        conversation_id: str,
        intent: str,
        capability: str,
        action: str,
        code: str,
        message: str,
    ) -> dict:
        return {
            "status": code,
            "conversation_id": conversation_id,
            "message": message,
            "execution": build_execution_contract(
                intent=intent,
                capability=capability,
                action=action,
                authorization={"status": "deny" if code == "authorization_denied" else "not_evaluated"},
                provider_called=False,
            ),
            "provider_called": False,
        }


knowledge_handler = KnowledgeHandler()
