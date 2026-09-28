from dataclasses import dataclass

from .embeddings import Embedder, HashingEmbedder
from .models import Chunk, SearchResult
from .retrieval import LexicalRetriever, reciprocal_rank_fusion
from .vector_store import InMemoryVectorStore, VectorRecord


@dataclass(frozen=True)
class RetrievalResponse:
    query: str
    results: list[SearchResult]


class RetrievalPipeline:
    """Orchestrates lexical and semantic retrieval without owning providers."""

    def __init__(self, chunks: list[Chunk], embedder: Embedder | None = None) -> None:
        self._chunks = chunks
        self._lexical = LexicalRetriever(chunks)
        self._embedder = embedder or HashingEmbedder()
        vectors = self._embedder.embed([chunk.text for chunk in chunks])
        self._vector_store = InMemoryVectorStore()
        self._vector_store.add(
            [VectorRecord(chunk, vector) for chunk, vector in zip(chunks, vectors)]
        )

    def search(self, query: str, k: int = 5) -> RetrievalResponse:
        lexical = self._lexical.search(query, k=max(k, 10))
        semantic = self._vector_store.search(self._embedder.embed([query])[0], k=max(k, 10))
        hybrid = reciprocal_rank_fusion([lexical, semantic])
        return RetrievalResponse(query=query, results=hybrid[:k])
