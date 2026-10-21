from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .bootstrap import load_corpus
from .embeddings import Embedder
from .generation import Generator, UnconfiguredGenerator
from .models import Chunk
from .providers import OpenAICompatibleEmbedder, configured_generator
from .service import EvidenceRAGService

_service: EvidenceRAGService | None = None


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
    global _service
    _service = EvidenceRAGService(
        chunks,
        generator or UnconfiguredGenerator(),
        embedder=embedder,
    )


def configure_service_from_env() -> None:
    required_variables = ("RAG_API_KEY", "RAG_EMBEDDING_MODEL", "RAG_LLM_MODEL")
    missing = [name for name in required_variables if not os.getenv(name)]
    if missing:
        raise RuntimeError(
            "Missing required RAG configuration: " + ", ".join(missing)
        )

    try:
        max_chars = int(os.getenv("RAG_CHUNK_MAX_CHARS", "1200"))
    except ValueError as exc:
        raise RuntimeError("RAG_CHUNK_MAX_CHARS must be an integer") from exc

    corpus_dir = Path(os.getenv("RAG_CORPUS_DIR", "data/corpus"))
    chunks = load_corpus(corpus_dir, max_chars=max_chars)
    configure_service(
        chunks,
        generator=configured_generator(),
        embedder=OpenAICompatibleEmbedder.from_env(),
    )


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    if os.getenv("RAG_API_KEY"):
        configure_service_from_env()
    yield


app = FastAPI(title="Evidence-Grounded RAG", version="0.2.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "evidence-grounded-rag"}


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    if _service is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "RAG service is not configured. Set the provider environment variables "
                "and point RAG_CORPUS_DIR to a Markdown corpus."
            ),
        )
    result = _service.answer(request.question, request.retrieval_k, request.evidence_k)
    return AskResponse(
        answer=result.answer,
        citations=[
            {"id": item.citation_id, "chunk_id": item.result.chunk.chunk_id}
            for item in result.evidence
        ],
    )
