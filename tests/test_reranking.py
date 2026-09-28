from evidence_rag.models import Chunk, SearchResult
from evidence_rag.reranking import LexicalReranker


def test_reranker_prefers_query_coverage() -> None:
    results = [
        SearchResult(Chunk("a", "d", "database architecture", 0), 1.0, "hybrid"),
        SearchResult(Chunk("b", "d", "database vector search architecture", 1), 0.9, "hybrid"),
    ]
    ranked = LexicalReranker().rerank("database vector", results, k=2)
    assert ranked[0].chunk.chunk_id == "b"
