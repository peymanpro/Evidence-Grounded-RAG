from __future__ import annotations

import logging
import os
from pathlib import Path

from .chunking import chunk_document
from .ingestion import load_markdown
from .postgres_store import PostgresVectorStore
from .providers import OpenAICompatibleEmbedder, OpenAICompatibleGenerator
from .service import EvidenceRAGService
from .vector_store import InMemoryVectorStore

logger = logging.getLogger(__name__)

_PROVIDER_SETTINGS = ("RAG_API_KEY", "RAG_EMBEDDING_MODEL", "RAG_LLM_MODEL")


def build_service_from_environment() -> EvidenceRAGService | None:
    """Build the in-memory RAG service when provider settings and a corpus exist.

    With no provider settings, return None so liveness checks still work in local
    development and CI. Partial provider configuration is treated as an error.
    """
    configured = {
        name: bool(os.getenv(name, "").strip())
        for name in _PROVIDER_SETTINGS
    }
    if not any(configured.values()):
        logger.info("RAG provider is not configured; /ask and /ready will report unavailable")
        return None

    missing = [name for name, present in configured.items() if not present]
    if missing:
        names = ", ".join(missing)
        raise RuntimeError(f"Incomplete RAG provider configuration; missing: {names}")

    corpus_dir = Path(os.getenv("RAG_CORPUS_DIR", "data/knowledge")).expanduser()
    if not corpus_dir.is_dir():
        raise RuntimeError(f"RAG_CORPUS_DIR is not a directory: {corpus_dir}")

    markdown_files = sorted(path for path in corpus_dir.rglob("*.md") if path.is_file())
    if not markdown_files:
        raise RuntimeError(f"No Markdown documents found in RAG_CORPUS_DIR: {corpus_dir}")

    chunks = []
    for path in markdown_files:
        document_id = path.relative_to(corpus_dir).with_suffix("").as_posix()
        document = load_markdown(path, document_id=document_id)
        chunks.extend(chunk_document(document))

    if not chunks:
        raise RuntimeError(f"No non-empty chunks created from RAG_CORPUS_DIR: {corpus_dir}")

    embedder = OpenAICompatibleEmbedder.from_env()
    generator = OpenAICompatibleGenerator.from_env()
    database_url = os.getenv("RAG_DATABASE_URL", "").strip()
    vector_store = (
        PostgresVectorStore.from_env()
        if database_url
        else InMemoryVectorStore()
    )
    logger.info("Loaded %d Markdown files and %d chunks for RAG", len(markdown_files), len(chunks))
    logger.info(
        "Using %s vector index",
        "PostgreSQL/pgvector" if database_url else "in-memory",
    )
    return EvidenceRAGService(
        chunks,
        generator=generator,
        embedder=embedder,
        vector_store=vector_store,
    )
