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
    vector_store_path: str | Path | None = None,
    embedding_model_key: str = "default",
    vector_store_backend: str | None = None,
    database_url: str | None = None,
) -> None:
    global _service
    _service = EvidenceRAGService(
        chunks,
        generator or UnconfiguredGenerator(),
        embedder=embedder,
        vector_store_path=vector_store_path,
        embedding_model_key=embedding_model_key,
        vector_store_backend=vector_store_backend,
        database_url=database_url,
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
    if max_chars <= 0:
        raise RuntimeError("RAG_CHUNK_MAX_CHARS must be a positive integer")

    backend = os.getenv("RAG_VECTOR_BACKEND", "sqlite").strip().lower()
    if backend not in {"sqlite", "pgvector", "memory"}:
        raise RuntimeError("RAG_VECTOR_BACKEND must be memory, sqlite, or pgvector")
    database_url = os.getenv("RAG_DATABASE_URL")
    if backend == "pgvector" and not database_url:
        raise RuntimeError("RAG_DATABASE_URL is required when RAG_VECTOR_BACKEND=pgvector")

    corpus_dir = Path(os.getenv("RAG_CORPUS_DIR", "data/corpus"))
    chunks = load_corpus(corpus_dir, max_chars=max_chars)
    base_url = os.getenv("RAG_API_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    embedding_model = os.environ["RAG_EMBEDDING_MODEL"]
    configure_service(
        chunks,
        generator=configured_generator(),
        embedder=OpenAICompatibleEmbedder.from_env(),
        vector_store_path=(
            os.getenv("RAG_VECTOR_DB_PATH", "data/vectors.sqlite3")
            if backend == "sqlite"
            else None
        ),
        embedding_model_key=f"{base_url}|{embedding_model}",
        vector_store_backend=backend,
        database_url=database_url if backend == "pgvector" else None,
    )


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    global _service
    configured_at_startup = False
    try:
        if os.getenv("RAG_API_KEY"):
            configure_service_from_env()
            configured_at_startup = True
        yield
    finally:
        if configured_at_startup and _service is not None:
            _service.close()
            _service = None


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
