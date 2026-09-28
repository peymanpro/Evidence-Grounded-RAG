from __future__ import annotations

import os

from fastapi import FastAPI
from pydantic import BaseModel

from .generation import UnconfiguredGenerator
from .models import Chunk
from .service import EvidenceRAGService


app = FastAPI(title="Evidence-Grounded RAG", version="0.2.0")
_service: EvidenceRAGService | None = None


class AskRequest(BaseModel):
    question: str
    retrieval_k: int = 12
    evidence_k: int = 5


class AskResponse(BaseModel):
    answer: str
    citations: list[dict[str, str]]


def configure_service(chunks: list[Chunk], generator=None, embedder=None) -> None:
    global _service
    _service = EvidenceRAGService(
        chunks,
        generator or UnconfiguredGenerator(),
        embedder=embedder,
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "evidence-grounded-rag"}


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    if _service is None:
        return AskResponse(
            answer="The RAG service is not configured with a knowledge corpus.",
            citations=[],
        )
    result = _service.answer(request.question, request.retrieval_k, request.evidence_k)
    return AskResponse(
        answer=result.answer,
        citations=[
            {"id": item.citation_id, "chunk_id": item.result.chunk.chunk_id}
            for item in result.evidence
        ],
    )
