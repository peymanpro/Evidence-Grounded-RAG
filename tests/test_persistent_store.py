from evidence_rag.models import Chunk
from evidence_rag.persistent_store import SQLiteVectorStore


def test_sqlite_vector_store_round_trip(tmp_path) -> None:
    store = SQLiteVectorStore(str(tmp_path / "vectors.sqlite3"))
    chunk = Chunk("c1", "d1", "hello vector", 0)
    store.upsert([(chunk, [1.0, 0.0])])
    results = store.search([1.0, 0.0], k=1)
    store.close()
    assert results[0].chunk.chunk_id == "c1"
