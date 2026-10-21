import os
from collections.abc import Sequence

import pytest

from evidence_rag.models import Chunk


class CountingEmbedder:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        batch = list(texts)
        self.calls.append(batch)
        return [[float(index + 1), 1.0, 0.5] for index, _ in enumerate(batch)]


def _store():
    database_url = os.getenv("RAG_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("RAG_TEST_DATABASE_URL is not configured")
    pytest.importorskip("psycopg")
    pytest.importorskip("pgvector")
    from evidence_rag.pgvector_store import PgVectorStore

    return PgVectorStore(database_url)


def test_pgvector_store_persists_vectors_and_searches_by_cosine() -> None:
    store = _store()
    embedder = CountingEmbedder()
    chunks = [
        Chunk("pgvector-a", "test", "first vector document", 0),
        Chunk("pgvector-b", "test", "second vector document", 1),
    ]

    try:
        store.sync_embeddings(chunks, embedder, "pgvector-roundtrip-v1")
        results = store.search([1.0, 1.0, 0.5], k=1)
    finally:
        store.close()

    assert results
    assert results[0].chunk.chunk_id == "pgvector-a"
    assert len(embedder.calls) == 1


def test_pgvector_store_reuses_embeddings_after_reconnect() -> None:
    chunks = [Chunk("pgvector-cache", "test", "cached embedding content", 0)]
    first_embedder = CountingEmbedder()
    first = _store()
    try:
        first.sync_embeddings(chunks, first_embedder, "pgvector-cache-v1")
    finally:
        first.close()

    second_embedder = CountingEmbedder()
    second = _store()
    try:
        second.sync_embeddings(chunks, second_embedder, "pgvector-cache-v1")
        results = second.search([1.0, 1.0, 0.5], k=1)
    finally:
        second.close()

    assert first_embedder.calls == [["cached embedding content"]]
    assert second_embedder.calls == []
    assert results[0].chunk.chunk_id == "pgvector-cache"


def test_pgvector_store_refreshes_changed_chunks_and_model() -> None:
    store = _store()
    embedder = CountingEmbedder()
    original = Chunk("pgvector-update", "test", "original text", 0)
    changed = Chunk("pgvector-update", "test", "updated text", 0)

    try:
        store.sync_embeddings([original], embedder, "pgvector-update-v1")
        store.sync_embeddings([changed], embedder, "pgvector-update-v1")
        store.sync_embeddings([changed], embedder, "pgvector-update-v2")
        results = store.search([1.0, 1.0, 0.5], k=1)
    finally:
        store.close()

    assert embedder.calls == [["original text"], ["updated text"], ["updated text"]]
    assert results[0].chunk.text == "updated text"
