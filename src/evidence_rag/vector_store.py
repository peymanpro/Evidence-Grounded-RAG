from dataclasses import dataclass

from .models import Chunk, SearchResult


@dataclass(frozen=True)
class VectorRecord:
    chunk: Chunk
    vector: list[float]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        raise ValueError("vectors must have the same dimension")
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = sum(a * a for a in left) ** 0.5
    right_norm = sum(b * b for b in right) ** 0.5
    if not left_norm or not right_norm:
        return 0.0
    return dot / (left_norm * right_norm)


class InMemoryVectorStore:
    def __init__(self) -> None:
        self._records: list[VectorRecord] = []

    def add(self, records: list[VectorRecord]) -> None:
        self._records.extend(records)

    def search(self, query_vector: list[float], k: int = 5) -> list[SearchResult]:
        scored = [
            SearchResult(record.chunk, cosine_similarity(query_vector, record.vector), "semantic")
            for record in self._records
        ]
        return sorted(scored, key=lambda result: result.score, reverse=True)[:k]
