import pytest
from fastapi.testclient import TestClient

import evidence_rag.api as api_module
from evidence_rag.api import app, configure_service
from evidence_rag.models import Chunk


class StubGenerator:
    def generate(self, prompt: str) -> str:
        return "Grounded answer [E1]"


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


def test_ask_returns_citations() -> None:
    configure_service(
        [Chunk("c1", "d1", "Python supports reliable software systems.", 0)],
        generator=StubGenerator(),
    )
    client = TestClient(app)
    response = client.post("/ask", json={"question": "Python software"})

    assert response.status_code == 200
    assert response.json()["citations"][0]["id"] == "E1"
