"""\nCreated/Updated: 2026-09-24 20:32 GMT+7\nMain Function: Exports Knowledge infrastructure adapters for application wiring.\n"""\n\n"""\nCreated/Updated: 2026-09-24 20:32 GMT+7\nMain Function: Knowledge subsystem implementation or verification code for the Workspace AI Agent.\n"""\n\n"""Concrete Knowledge infrastructure adapters."""

from app.infrastructure.knowledge.docling import DoclingDocumentParser
from app.infrastructure.knowledge.ollama_embedding import OllamaEmbeddingProvider
from app.infrastructure.knowledge.qdrant import QdrantVectorIndex
from app.infrastructure.knowledge.bge_reranker import BGEReranker

__all__ = [
    "DoclingDocumentParser",
    "OllamaEmbeddingProvider",
    "QdrantVectorIndex",
]
