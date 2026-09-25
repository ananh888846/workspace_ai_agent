"""\nCreated/Updated: 2026-09-24 20:32 GMT+7\nMain Function: Opt-in runtime smoke test for real Ollama embeddings and Qdrant vector indexing.\n"""\n\nimport os

import pytest

from app.infrastructure.knowledge.ollama_embedding import OllamaEmbeddingProvider
from app.infrastructure.knowledge.qdrant import QdrantVectorIndex


@pytest.mark.integration
def test_knowledge_embedding_and_qdrant_runtime_smoke():
    if os.getenv("RUN_KNOWLEDGE_VECTOR_SMOKE") != "1":
        pytest.skip("set RUN_KNOWLEDGE_VECTOR_SMOKE=1")

    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    embedding_model = os.getenv(
        "OLLAMA_EMBEDDING_MODEL", "nomic-embed-text-v2-moe"
    )
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    collection = os.getenv("QDRANT_COLLECTION", "knowledge_v1")
    version_id = "11111111-1111-1111-1111-111111111111"

    chunks = [
        "Knowledge runtime smoke test.",
        "Ollama generates the embedding and Qdrant stores the vector.",
    ]

    embedding = OllamaEmbeddingProvider(ollama_url, embedding_model)
    vectors = embedding.embed(chunks)

    assert len(vectors) == len(chunks)
    assert len(vectors[0]) > 0

    index = QdrantVectorIndex(qdrant_url, collection)
    index.upsert(chunks, vectors, version_id)
    index.reconcile(version_id)

    assert index._vector_size == len(vectors[0])
