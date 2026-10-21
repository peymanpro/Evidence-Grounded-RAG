from collections.abc import Sequence

from evidence_rag.models import Chunk
from evidence_rag.pipeline import RetrievalPipeline


class CountingEmbedder:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        batch = list(texts)
        self.calls.append(batch)
        return [[1.0, float(index + 1)] for index, _ in enumerate(batch)]


def test_pipeline_returns_ranked_evidence() -> None:
    chunks = [
        Chunk("a", "doc", "vector databases store embeddings", 0),
        Chunk("b", "doc", "HTTP caching reduces latency", 1),
    ]

    response = RetrievalPipeline(chunks).search("embeddings", k=1)

    assert response.results[0].chunk.chunk_id == "a"
    assert response.results[0].retrieval_method == "hybrid"


def test_pipeline_reuses_persistent_embeddings_after_restart(tmp_path) -> None:
    chunks = [
        Chunk("a", "doc", "vector databases store embeddings", 0),
        Chunk("b", "doc", "HTTP caching reduces latency", 1),
    ]
    embedder = CountingEmbedder()
    path = tmp_path / "vectors.sqlite3"

    first = RetrievalPipeline(
        chunks,
        embedder=embedder,
        vector_store_path=path,
        embedding_model_key="test-model",
    )
    first.close()
    second = RetrievalPipeline(
        chunks,
        embedder=embedder,
        vector_store_path=path,
        embedding_model_key="test-model",
    )
    second.close()

    assert embedder.calls == [
        ["vector databases store embeddings", "HTTP caching reduces latency"]
    ]


def test_pipeline_removes_chunks_missing_from_new_corpus(tmp_path) -> None:
    path = tmp_path / "vectors.sqlite3"
    old_chunks = [Chunk("old", "doc", "obsolete content", 0)]
    current_chunks = [Chunk("current", "doc", "current evidence", 0)]

    first = RetrievalPipeline(old_chunks, vector_store_path=path)
    first.close()
    second = RetrievalPipeline(current_chunks, vector_store_path=path)
    response = second.search("current evidence", k=5)
    second.close()

    assert {result.chunk.chunk_id for result in response.results} == {"current"}
