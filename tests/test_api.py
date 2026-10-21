from collections.abc import Sequence
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import evidence_rag.api as api_module
from evidence_rag.api import app, configure_service
from evidence_rag.models import Chunk


class StubGenerator:
    def generate(self, prompt: str) -> str:
        return "Grounded answer [E1]"


class StubEmbedder:
    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [[1.0, 0.0] for _ in texts]


def test_health() -> None:
    client = TestClient(app)
    assert client.get("/health").json()["status"] == "ok"


def test_ask_returns_503_when_unconfigured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(api_module, "_service", None)

    client = TestClient(app)
    response = client.post("/ask", json={"question": "Python software"})

    assert response.status_code == 503
    assert "RAG service is not configured" in response.json()["detail"]


def test_configure_service_requires_provider_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("RAG_API_KEY", "RAG_EMBEDDING_MODEL", "RAG_LLM_MODEL"):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(RuntimeError, match="Missing required RAG configuration"):
        api_module.configure_service_from_env()


def test_pgvector_backend_requires_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAG_API_KEY", "test-key")
    monkeypatch.setenv("RAG_EMBEDDING_MODEL", "test-embedding")
    monkeypatch.setenv("RAG_LLM_MODEL", "test-chat")
    monkeypatch.setenv("RAG_VECTOR_BACKEND", "pgvector")
    monkeypatch.delenv("RAG_DATABASE_URL", raising=False)

    with pytest.raises(RuntimeError, match="RAG_DATABASE_URL is required"):
        api_module.configure_service_from_env()


def test_lifespan_loads_corpus_and_configures_providers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    (corpus_dir / "guide.md").write_text(
        "# Guide\n\nPython supports reliable software.", encoding="utf-8"
    )

    monkeypatch.setattr(api_module, "_service", None)
    monkeypatch.setenv("RAG_API_KEY", "test-key")
    monkeypatch.setenv("RAG_EMBEDDING_MODEL", "test-embedding")
    monkeypatch.setenv("RAG_LLM_MODEL", "test-chat")
    monkeypatch.setenv("RAG_CORPUS_DIR", str(corpus_dir))
    monkeypatch.setenv("RAG_VECTOR_BACKEND", "sqlite")
    monkeypatch.setenv("RAG_VECTOR_DB_PATH", str(tmp_path / "vectors.sqlite3"))
    monkeypatch.setattr(api_module, "configured_generator", lambda: StubGenerator())
    monkeypatch.setattr(
        api_module.OpenAICompatibleEmbedder,
        "from_env",
        classmethod(lambda cls: StubEmbedder()),
    )

    with TestClient(app) as client:
        response = client.post("/ask", json={"question": "What does the guide say?"})

    assert response.status_code == 200
    assert response.json()["answer"] == "Grounded answer [E1]"
    assert response.json()["citations"][0]["chunk_id"] == "guide:0"


def test_lifespan_loads_pgvector_backend(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database_url = os.getenv("RAG_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("RAG_TEST_DATABASE_URL is not configured")
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    (corpus_dir / "guide.md").write_text(
        "# Guide\n\nPython supports reliable software.", encoding="utf-8"
    )

    monkeypatch.setattr(api_module, "_service", None)
    monkeypatch.setenv("RAG_API_KEY", "test-key")
    monkeypatch.setenv("RAG_EMBEDDING_MODEL", "test-embedding")
    monkeypatch.setenv("RAG_LLM_MODEL", "test-chat")
    monkeypatch.setenv("RAG_VECTOR_BACKEND", "pgvector")
    monkeypatch.setenv("RAG_DATABASE_URL", database_url)
    monkeypatch.setenv("RAG_CORPUS_DIR", str(corpus_dir))
    monkeypatch.setattr(api_module, "configured_generator", lambda: StubGenerator())
    monkeypatch.setattr(
        api_module.OpenAICompatibleEmbedder,
        "from_env",
        classmethod(lambda cls: StubEmbedder()),
    )

    with TestClient(app) as client:
        response = client.post("/ask", json={"question": "What does the guide say?"})

    assert response.status_code == 200
    assert response.json()["answer"] == "Grounded answer [E1]"
    assert response.json()["citations"][0]["chunk_id"] == "guide:0"


def test_ask_returns_citations(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(api_module, "_service", None)
    configure_service(
        [Chunk("c1", "d1", "Python supports reliable software systems.", 0)],
        generator=StubGenerator(),
    )
    client = TestClient(app)
    response = client.post("/ask", json={"question": "Python software"})

    assert response.status_code == 200
    assert response.json()["citations"][0]["id"] == "E1"
