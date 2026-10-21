from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from .embeddings import Embedder
from .models import Chunk, SearchResult


@dataclass(frozen=True)
class IndexReport:
    embedded: int
    reused: int
    deleted: int
    dimension: int
    model_changed: bool = False


class VectorIndex(Protocol):
    """Storage contract for semantic vectors used by the retrieval pipeline."""

    def index(self, chunks: list[Chunk], embedder: Embedder) -> IndexReport: ...

    def search(self, query_vector: list[float], k: int = 5) -> list[SearchResult]: ...


@dataclass(frozen=True)
class VectorRecord:
    chunk: Chunk
    vector: list[float]


def validate_vectors(vectors: Sequence[Sequence[float]], expected_count: int) -> int:
    if len(vectors) != expected_count:
        raise ValueError(
            f"embedder returned {len(vectors)} vectors for {expected_count} inputs"
        )
    if not vectors:
        return 0

    dimension = len(vectors[0])
    if dimension == 0:
        raise ValueError("embedding vectors must have at least one dimension")
    if any(len(vector) != dimension for vector in vectors):
        raise ValueError("embedding vectors must all have the same dimension")
    return dimension


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
    """Small in-memory implementation used by unit tests and offline examples."""

    def __init__(self) -> None:
        self._records: list[VectorRecord] = []

    def add(self, records: list[VectorRecord]) -> None:
        self._records.extend(records)

    def index(self, chunks: list[Chunk], embedder: Embedder) -> IndexReport:
        vectors = embedder.embed([chunk.text for chunk in chunks])
        dimension = validate_vectors(vectors, len(chunks))
        self._records = [
            VectorRecord(chunk, list(vector))
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]
        return IndexReport(
            embedded=len(chunks),
            reused=0,
            deleted=0,
            dimension=dimension,
        )

    def search(self, query_vector: list[float], k: int = 5) -> list[SearchResult]:
        if k <= 0:
            return []
        scored = [
            SearchResult(record.chunk, cosine_similarity(query_vector, record.vector), "semantic")
            for record in self._records
        ]
        return sorted(scored, key=lambda result: result.score, reverse=True)[:k]
