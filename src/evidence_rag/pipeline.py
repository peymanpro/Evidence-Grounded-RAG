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
    """Orchestrates lexical retrieval with an in-memory or persistent semantic index."""

    def __init__(
        self,
        chunks: list[Chunk],
        embedder: Embedder | None = None,
        vector_store_path: str | Path | None = None,
        embedding_model_key: str = "default",
    ) -> None:
        self._chunks = chunks
        self._lexical = LexicalRetriever(chunks)
        self._embedder = embedder or HashingEmbedder()

        if vector_store_path is None:
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
            self._vector_store: InMemoryVectorStore | SQLiteVectorStore = vector_store
        else:
            vector_store = SQLiteVectorStore(vector_store_path)
            vector_store.sync_embeddings(chunks, self._embedder, embedding_model_key)
            self._vector_store = vector_store

    def close(self) -> None:
        if isinstance(self._vector_store, SQLiteVectorStore):
            self._vector_store.close()

    def search(self, query: str, k: int = 5) -> RetrievalResponse:
        if k <= 0:
            return RetrievalResponse(query=query, results=[])

        lexical = self._lexical.search(query, k=max(k, 10))
        semantic = self._vector_store.search(
            self._embedder.embed([query])[0], k=max(k, 10)
        )
        hybrid = reciprocal_rank_fusion([lexical, semantic])
        return RetrievalResponse(query=query, results=hybrid[:k])
