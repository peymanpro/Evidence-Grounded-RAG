from dataclasses import dataclass

from .models import Chunk, SearchResult
from .retrieval import LexicalRetriever, reciprocal_rank_fusion


@dataclass(frozen=True)
class RetrievalResponse:
    query: str
    results: list[SearchResult]


class RetrievalPipeline:
    """Keeps retrieval orchestration separate from indexing and generation."""

    def __init__(self, chunks: list[Chunk]) -> None:
        self._lexical = LexicalRetriever(chunks)

    def search(self, query: str, k: int = 5) -> RetrievalResponse:
        lexical = self._lexical.search(query, k=k)
        # The second signal will be supplied by the embedding retriever in a later phase.
        hybrid = reciprocal_rank_fusion([lexical])
        return RetrievalResponse(query=query, results=hybrid[:k])
