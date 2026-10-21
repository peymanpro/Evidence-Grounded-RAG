from dataclasses import dataclass
from pathlib import Path

from .embeddings import Embedder, HashingEmbedder
from .models import Chunk, SearchResult
from .persistent_store import SQLiteVectorStore
from .retrieval import LexicalRetriever, reciprocal_rank_fusion
from .vector_store import InMemoryVectorStore, VectorRecord


@dataclass(frozen=True)
class RetrievalResponse:
    query: str
    results: list[SearchResult]


class RetrievalPipeline:
    """Orchestrates lexical retrieval with memory, SQLite, or pgvector indexing."""

    def __init__(
        self,
        chunks: list[Chunk],
        embedder: Embedder | None = None,
        vector_store_path: str | Path | None = None,
        embedding_model_key: str = "default",
        vector_store_backend: str | None = None,
        database_url: str | None = None,
    ) -> None:
        self._chunks = chunks
        self._lexical = LexicalRetriever(chunks)
        self._embedder = embedder or HashingEmbedder()
        backend = vector_store_backend or ("sqlite" if vector_store_path is not None else "memory")

        if backend == "memory":
            if database_url is not None:
                raise ValueError("database_url is only valid with the pgvector backend")
            vectors = self._embedder.embed([chunk.text for chunk in chunks])
            if len(vectors) != len(chunks):
                raise ValueError(
                    "Embedder returned a different number of vectors than input chunks"
                )
            vector_store = InMemoryVectorStore()
            vector_store.add(
                [
                    VectorRecord(chunk, vector)
                    for chunk, vector in zip(chunks, vectors, strict=True)
                ]
            )
            self._vector_store = vector_store
        elif backend == "sqlite":
            if database_url is not None:
                raise ValueError("database_url is only valid with the pgvector backend")
            path = vector_store_path or "data/vectors.sqlite3"
            vector_store = SQLiteVectorStore(path)
            vector_store.sync_embeddings(chunks, self._embedder, embedding_model_key)
            self._vector_store = vector_store
        elif backend == "pgvector":
            if not database_url:
                raise ValueError("database_url is required for the pgvector backend")
            from .pgvector_store import PgVectorStore

            vector_store = PgVectorStore(database_url)
            vector_store.sync_embeddings(chunks, self._embedder, embedding_model_key)
            self._vector_store = vector_store
        else:
            raise ValueError(
                "vector_store_backend must be one of: memory, sqlite, pgvector"
            )

    def close(self) -> None:
        close = getattr(self._vector_store, "close", None)
        if callable(close):
            close()

    def search(self, query: str, k: int = 5) -> RetrievalResponse:
        if k <= 0:
            return RetrievalResponse(query=query, results=[])

        lexical = self._lexical.search(query, k=max(k, 10))
        semantic = self._vector_store.search(
            self._embedder.embed([query])[0], k=max(k, 10)
        )
        hybrid = reciprocal_rank_fusion([lexical, semantic])
        return RetrievalResponse(query=query, results=hybrid[:k])
