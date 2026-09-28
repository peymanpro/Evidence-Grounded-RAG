from __future__ import annotations

import re
from collections import Counter

from .models import SearchResult


def _tokens(text: str) -> list[str]:
    return re.findall(r"[\w-]+", text.lower())


class LexicalReranker:
    """Deterministic second-stage reranker using query-term coverage.

    This is intentionally lightweight; a cross-encoder can implement the same
    interface later without changing the pipeline.
    """

    def rerank(self, query: str, results: list[SearchResult], k: int = 5) -> list[SearchResult]:
        query_terms = set(_tokens(query))
        if not query_terms:
            return results[:k]

        scored: list[tuple[float, SearchResult]] = []
        for result in results:
            terms = Counter(_tokens(result.chunk.text))
            covered = sum(1 for term in query_terms if terms[term])
            coverage = covered / len(query_terms)
            density = sum(terms[term] for term in query_terms) / max(len(_tokens(result.chunk.text)), 1)
            score = coverage + min(density, 1.0) * 0.1 + result.score * 0.01
            scored.append((score, result))
        return [result for _, result in sorted(scored, key=lambda x: x[0], reverse=True)[:k]]
