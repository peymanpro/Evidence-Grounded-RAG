from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from evidence_rag import api
from evidence_rag.api import app, configure_service
from evidence_rag.embeddings import HashingEmbedder
from evidence_rag.generation import Generator
from evidence_rag.models import Chunk


class StubGenerator:
    def generate(self, prompt: str) -> str:
        return "Grounded answer [E1]"


def test_health() -> None:
    client = TestClient(app)
    assert client.get("/health").json()["status"] == "ok"


def test_ready_returns_503_when_unconfigured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(api, "_service", None)
    response = TestClient(app).get("/ready")
    assert response.status_code == 503


def test_ask_returns_503_when_unconfigured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(api, "_service", None)
    response = TestClient(app).post("/ask", json={"question": "Any question?"})
    assert response.status_code == 503


def test_ask_returns_citations() -> None:
    configure_service(
        [Chunk("c1", "d1", "Python supports reliable software systems.", 0)],
        generator=StubGenerator(),
    )
    client = TestClient(app)
    response = client.post("/ask", json={"question": "Python software"})
    assert response.status_code == 200
    assert response.json()["citations"][0]["id"] == "E1"


def test_build_service_skips_when_provider_is_not_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from evidence_rag.runtime import build_service_from_environment

    for name in ("RAG_API_KEY", "RAG_EMBEDDING_MODEL", "RAG_LLM_MODEL"):
        monkeypatch.delenv(name, raising=False)

    assert build_service_from_environment() is None


def test_build_service_rejects_partial_provider_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from evidence_rag.runtime import build_service_from_environment

    monkeypatch.setenv("RAG_API_KEY", "test-key")
    monkeypatch.delenv("RAG_EMBEDDING_MODEL", raising=False)
    monkeypatch.delenv("RAG_LLM_MODEL", raising=False)

    with pytest.raises(RuntimeError, match="RAG_EMBEDDING_MODEL"):
        build_service_from_environment()


def test_build_service_loads_markdown_corpus_without_network(
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
    result = service.answer("What does retrieval evaluation measure?")
    assert result.answer == "Grounded answer [E1]"
    assert result.evidence
