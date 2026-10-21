from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .embeddings import Embedder
from .generation import Generator, UnconfiguredGenerator
from .models import Chunk
from .runtime import build_service_from_environment
from .service import EvidenceRAGService

logger = logging.getLogger(__name__)
_service: EvidenceRAGService | None = None


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    global _service
    _service = None
    try:
        # Provider calls can block while the initial corpus is embedded.
        _service = await asyncio.to_thread(build_service_from_environment)
        yield
    finally:
        _service = None


app = FastAPI(title="Evidence-Grounded RAG", version="0.2.0", lifespan=lifespan)


class AskRequest(BaseModel):
    question: str
    retrieval_k: int = 12
    evidence_k: int = 5


class AskResponse(BaseModel):
    answer: str
    citations: list[dict[str, str]]


def configure_service(
    chunks: list[Chunk],
    generator: Generator | None = None,
    embedder: Embedder | None = None,
) -> None:
    """Configure the service explicitly; useful for tests and embedding use cases."""
    global _service
    _service = EvidenceRAGService(
        chunks,
        generator=generator or UnconfiguredGenerator(),
        embedder=embedder,
    )


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness endpoint; a healthy process may still lack RAG configuration."""
    return {"status": "ok", "service": "evidence-grounded-rag"}


@app.get("/ready")
def readiness() -> dict[str, str]:
    if _service is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "RAG service is not configured. Set RAG_API_KEY, "
                "RAG_EMBEDDING_MODEL, and RAG_LLM_MODEL, and provide Markdown "
                "documents through RAG_CORPUS_DIR."
            ),
        )
    return {"status": "ready", "service": "evidence-grounded-rag"}


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    if _service is None:
        raise HTTPException(
            status_code=503,
            detail="RAG service is not configured; see GET /ready for requirements.",
        )
    result = _service.answer(request.question, request.retrieval_k, request.evidence_k)
    return AskResponse(
        answer=result.answer,
        citations=[
            {"id": item.citation_id, "chunk_id": item.result.chunk.chunk_id}
            for item in result.evidence
        ],
    )
