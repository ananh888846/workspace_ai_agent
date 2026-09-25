"""Concrete Knowledge infrastructure adapters."""

from app.infrastructure.knowledge.docling import DoclingDocumentParser
from app.infrastructure.knowledge.ollama_embedding import OllamaEmbeddingProvider
from app.infrastructure.knowledge.qdrant import QdrantVectorIndex
from app.infrastructure.knowledge.bge_reranker import BGEReranker

__all__ = [
    "DoclingDocumentParser",
    "OllamaEmbeddingProvider",
    "QdrantVectorIndex",
]
