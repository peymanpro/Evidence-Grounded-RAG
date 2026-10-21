from __future__ import annotations

from collections.abc import Sequence
import os
from pathlib import Path

import psycopg
import pytest

from evidence_rag.embeddings import HashingEmbedder
from evidence_rag.models import Chunk
from evidence_rag.postgres_store import PostgresVectorStore


class StubGenerator:
    def generate(self, prompt: str) -> str:
        return "Grounded answer [E1]"


class CountingEmbedder:
    def __init__(self, model: str = "test-embedding-model-v1") -> None:
        self.model = model
        self.embedded_texts: list[str] = []

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        self.embedded_texts.extend(texts)
        vectors = []
        for text in texts:
            normalized = text.lower()
            vectors.append(
                [
                    float("apple" in normalized or "fruit" in normalized),
                    float("car" in normalized or "road" in normalized),
                    float("banana" in normalized),
                ]
            )
        return vectors


@pytest.fixture
def database_dsn():
    dsn = os.getenv("RAG_TEST_DATABASE_URL")
    if not dsn:
        pytest.skip("Set RAG_TEST_DATABASE_URL to run PostgreSQL/pgvector integration tests")

    chunk_table = "test_rag_vector_store_chunks"
    state_table = "test_rag_vector_store_index_state"
    with psycopg.connect(dsn) as connection:
        connection.execute(f"DROP TABLE IF EXISTS {chunk_table} CASCADE")
        connection.execute(f"DROP TABLE IF EXISTS {state_table} CASCADE")

    try:
        yield dsn
    finally:
        with psycopg.connect(dsn) as connection:
            connection.execute(f"DROP TABLE IF EXISTS {chunk_table} CASCADE")
            connection.execute(f"DROP TABLE IF EXISTS {state_table} CASCADE")


def sample_chunks() -> list[Chunk]:
    return [
        Chunk("fruit:0", "fruit", "Apple fruit grows in an orchard.", 0, {"kind": "fruit"}),
        Chunk("road:0", "road", "A car travels along a road.", 0, {"kind": "vehicle"}),
    ]


def test_postgres_index_persists_and_reuses_unchanged_embeddings(database_dsn: str) -> None:
    embedder = CountingEmbedder()
    store = PostgresVectorStore(database_dsn, table_prefix="test_rag_vector_store")

    first = store.index(sample_chunks(), embedder)
    assert first.embedded == 2
    assert first.reused == 0
    assert first.dimension == 3

    results = store.search([1.0, 0.0, 0.0], k=1)
    assert results[0].chunk.chunk_id == "fruit:0"
    assert results[0].chunk.metadata == {"kind": "fruit"}

    restarted_store = PostgresVectorStore(database_dsn, table_prefix="test_rag_vector_store")
    second = restarted_store.index(sample_chunks(), embedder)
    assert second.embedded == 0
    assert second.reused == 2
    assert second.deleted == 0
    assert len(embedder.embedded_texts) == 2

    persisted_results = restarted_store.search([0.0, 1.0, 0.0], k=1)
    assert persisted_results[0].chunk.chunk_id == "road:0"


def test_postgres_index_updates_changed_and_removed_chunks(database_dsn: str) -> None:
    embedder = CountingEmbedder()
    store = PostgresVectorStore(database_dsn, table_prefix="test_rag_vector_store")
    store.index(sample_chunks(), embedder)

    updated = [
        Chunk("fruit:0", "fruit", "Banana fruit from a tropical plant.", 0, {"kind": "fruit"}),
        Chunk("new:0", "new", "Apple fruit is nutritious.", 0, {"kind": "new"}),
    ]
    report = store.index(updated, embedder)

    assert report.embedded == 2
    assert report.reused == 0
    assert report.deleted == 1
    result_ids = {result.chunk.chunk_id for result in store.search([0.0, 0.0, 1.0], k=5)}
    assert "fruit:0" in result_ids
    assert "new:0" in result_ids
    assert "road:0" not in result_ids


def test_postgres_index_reembeds_when_model_identity_changes(database_dsn: str) -> None:
    store = PostgresVectorStore(database_dsn, table_prefix="test_rag_vector_store")
    first_embedder = CountingEmbedder("embedding-v1")
    store.index(sample_chunks(), first_embedder)

    second_embedder = CountingEmbedder("embedding-v2")
    report = store.index(sample_chunks(), second_embedder)

    assert report.model_changed
    assert report.embedded == 2
    assert len(second_embedder.embedded_texts) == 2


def test_runtime_selects_postgres_store_when_database_url_is_configured(
    database_dsn: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from evidence_rag import runtime

    corpus_dir = tmp_path / "knowledge"
    corpus_dir.mkdir()
    (corpus_dir / "guide.md").write_text(
        "# Retrieval guide\n\nRetrieval evaluation measures relevant documents.",
        encoding="utf-8",
    )
    monkeypatch.setenv("RAG_API_KEY", "test-key")
    monkeypatch.setenv("RAG_EMBEDDING_MODEL", "test-embedding")
    monkeypatch.setenv("RAG_LLM_MODEL", "test-model")
    monkeypatch.setenv("RAG_DATABASE_URL", database_dsn)
    monkeypatch.setenv("RAG_VECTOR_TABLE_PREFIX", "test_rag_vector_store")
    monkeypatch.setenv("RAG_CORPUS_DIR", str(corpus_dir))
    monkeypatch.setattr(
        runtime.OpenAICompatibleEmbedder,
        "from_env",
        classmethod(lambda cls: HashingEmbedder()),
    )
    monkeypatch.setattr(
        runtime.OpenAICompatibleGenerator,
        "from_env",
        classmethod(lambda cls: StubGenerator()),
    )

    service = runtime.build_service_from_environment()

    assert service is not None
    assert isinstance(service.retrieval._vector_store, PostgresVectorStore)
    result = service.answer("What does retrieval evaluation measure?")
    assert result.answer == "Grounded answer [E1]"
    assert result.evidence
