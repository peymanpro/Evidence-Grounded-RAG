from evidence_rag.models import Chunk
from evidence_rag.vector_store import InMemoryVectorStore, VectorRecord


def test_vector_store_ranks_by_cosine_similarity() -> None:
    a = Chunk("a", "doc", "alpha", 0)
    b = Chunk("b", "doc", "beta", 1)
    store = InMemoryVectorStore()
    store.add([VectorRecord(a, [1.0, 0.0]), VectorRecord(b, [0.0, 1.0])])

    results = store.search([0.9, 0.1], k=2)

    assert results[0].chunk.chunk_id == "a"
