from dataclasses import dataclass

from .embeddings import Embedder, HashingEmbedder
from .models import Chunk, SearchResult
from .retrieval import LexicalRetriever, reciprocal_rank_fusion
from .vector_store import InMemoryVectorStore, VectorIndex


@dataclass(frozen=True)
class RetrievalResponse:
    query: str
    results: list[SearchResult]


class RetrievalPipeline:
    """Orchestrates lexical and semantic retrieval without owning providers."""

    def __init__(
        self,
        chunks: list[Chunk],
        embedder: Embedder | None = None,
        vector_store: VectorIndex | None = None,
    ) -> None:
        self._chunks = chunks
        self._lexical = LexicalRetriever(chunks)
        self._embedder = embedder or HashingEmbedder()
        self._vector_store = vector_store or InMemoryVectorStore()
        if chunks:
            self._vector_store.index(chunks, self._embedder)

    def search(self, query: str, k: int = 5) -> RetrievalResponse:
        if k <= 0:
            return RetrievalResponse(query=query, results=[])
        lexical = self._lexical.search(query, k=max(k, 10))
        semantic = self._vector_store.search(self._embedder.embed([query])[0], k=max(k, 10))
        hybrid = reciprocal_rank_fusion([lexical, semantic])
        return RetrievalResponse(query=query, results=hybrid[:k])
