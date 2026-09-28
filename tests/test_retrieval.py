from evidence_rag.models import Chunk
from evidence_rag.retrieval import LexicalRetriever, reciprocal_rank_fusion


def test_lexical_retriever_returns_relevant_chunk_first() -> None:
    chunks = [
        Chunk("a", "doc", "PostgreSQL stores vectors with pgvector.", 0),
        Chunk("b", "doc", "Redis is useful for caching.", 1),
    ]

    results = LexicalRetriever(chunks).search("pgvector vectors", k=2)

    assert results[0].chunk.chunk_id == "a"
    assert results[0].retrieval_method == "lexical"


def test_rrf_combines_rankings_without_duplicates() -> None:
    a = Chunk("a", "doc", "alpha", 0)
    b = Chunk("b", "doc", "beta", 1)

    results = reciprocal_rank_fusion(
        [[type("R", (), {"chunk": a, "score": 1.0})(), type("R", (), {"chunk": b, "score": 0.5})()]],
    )

    assert [result.chunk.chunk_id for result in results] == ["a", "b"]
