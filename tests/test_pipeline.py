from evidence_rag.models import Chunk
from evidence_rag.pipeline import RetrievalPipeline


def test_pipeline_returns_ranked_evidence() -> None:
    chunks = [
        Chunk("a", "doc", "vector databases store embeddings", 0),
        Chunk("b", "doc", "HTTP caching reduces latency", 1),
    ]

    response = RetrievalPipeline(chunks).search("embeddings", k=1)

    assert response.results[0].chunk.chunk_id == "a"
    assert response.results[0].retrieval_method == "hybrid"
