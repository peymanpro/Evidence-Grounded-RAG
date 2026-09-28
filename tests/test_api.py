from fastapi.testclient import TestClient

from evidence_rag.api import app, configure_service
from evidence_rag.generation import Generator
from evidence_rag.models import Chunk


class StubGenerator:
    def generate(self, prompt: str) -> str:
        return "Grounded answer [E1]"


def test_health() -> None:
    client = TestClient(app)
    assert client.get("/health").json()["status"] == "ok"


def test_ask_returns_citations() -> None:
    configure_service(
        [Chunk("c1", "d1", "Python supports reliable software systems.", 0)],
        generator=StubGenerator(),
    )
    client = TestClient(app)
    response = client.post("/ask", json={"question": "Python software"})
    assert response.status_code == 200
    assert response.json()["citations"][0]["id"] == "E1"
