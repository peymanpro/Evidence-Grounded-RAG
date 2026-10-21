from collections.abc import Sequence

from evidence_rag.models import Chunk
from evidence_rag.persistent_store import SQLiteVectorStore


class CountingEmbedder:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        batch = list(texts)
        self.calls.append(batch)
        return [[float(index + 1), 1.0] for index, _ in enumerate(batch)]


def test_sqlite_vector_store_round_trip(tmp_path) -> None:
    store = SQLiteVectorStore(str(tmp_path / "vectors.sqlite3"))
    chunk = Chunk("c1", "d1", "hello vector", 0)
    store.upsert([(chunk, [1.0, 0.0])])
    results = store.search([1.0, 0.0], k=1)
    store.close()
    assert results[0].chunk.chunk_id == "c1"


def test_sync_embeddings_reuses_vectors_after_reopen(tmp_path) -> None:
    path = tmp_path / "nested" / "vectors.sqlite3"
    chunk = Chunk("c1", "d1", "hello vector", 0, {"source": "guide.md"})
    embedder = CountingEmbedder()

    first_store = SQLiteVectorStore(path)
    first_store.sync_embeddings([chunk], embedder, embedding_model="provider/model-v1")
    first_store.close()

    second_store = SQLiteVectorStore(path)
    second_store.sync_embeddings([chunk], embedder, embedding_model="provider/model-v1")
    results = second_store.search([1.0, 1.0], k=1)
    second_store.close()

    assert embedder.calls == [["hello vector"]]
    assert results[0].chunk.chunk_id == "c1"


def test_sync_embeddings_refreshes_changed_content_and_model(tmp_path) -> None:
    store = SQLiteVectorStore(tmp_path / "vectors.sqlite3")
    embedder = CountingEmbedder()
    original = Chunk("c1", "d1", "old content", 0)
    changed = Chunk("c1", "d1", "new content", 0)

    store.sync_embeddings([original], embedder, embedding_model="model-v1")
    store.sync_embeddings([changed], embedder, embedding_model="model-v1")
    store.sync_embeddings([changed], embedder, embedding_model="model-v2")
    results = store.search([1.0, 1.0], k=1)
    store.close()

    assert embedder.calls == [["old content"], ["new content"], ["new content"]]
    assert results[0].chunk.text == "new content"
