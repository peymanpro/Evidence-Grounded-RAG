import math
import re
from collections import Counter

from .models import Chunk, SearchResult


def _tokens(text: str) -> list[str]:
    return re.findall(r"[\w-]+", text.lower())


class LexicalRetriever:
    """Small deterministic BM25-like retriever for the first retrieval baseline."""

    def __init__(self, chunks: list[Chunk]) -> None:
        self._chunks = chunks
        self._terms = [_tokens(c.text) for c in chunks]
        self._avgdl = sum(map(len, self._terms), 0) / len(self._terms) if self._terms else 0.0
        self._df = Counter(term for terms in self._terms for term in set(terms))
        self._n = len(chunks)

    def search(self, query: str, k: int = 5) -> list[SearchResult]:
        if k <= 0:
            return []
        query_terms = _tokens(query)
        if not query_terms or not self._chunks:
            return []

        results: list[SearchResult] = []
        for chunk, terms in zip(self._chunks, self._terms):
            frequencies = Counter(terms)
            score = 0.0
            for term in query_terms:
                if term not in frequencies:
                    continue
                df = self._df[term]
                idf = math.log(1 + (self._n - df + 0.5) / (df + 0.5))
                tf = frequencies[term]
                dl = len(terms)
                denom = tf + 1.5 * (0.25 + 0.75 * dl / self._avgdl) if self._avgdl else 1.0
                score += idf * (tf * 2.5) / denom
            if score > 0:
                results.append(SearchResult(chunk, score, "lexical"))
        return sorted(results, key=lambda x: x.score, reverse=True)[:k]


def reciprocal_rank_fusion(
    result_sets: list[list[SearchResult]], k: int = 60
) -> list[SearchResult]:
    scores: dict[str, float] = {}
    items: dict[str, SearchResult] = {}
    for results in result_sets:
        for rank, result in enumerate(results, start=1):
            scores[result.chunk.chunk_id] = scores.get(result.chunk.chunk_id, 0.0) + 1 / (k + rank)
            items[result.chunk.chunk_id] = result

    return [
        SearchResult(items[chunk_id].chunk, score, "hybrid")
        for chunk_id, score in sorted(scores.items(), key=lambda item: item[1], reverse=True)
    ]
