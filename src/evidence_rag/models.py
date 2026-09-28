from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Document:
    document_id: str
    source: str
    title: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    document_id: str
    text: str
    position: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SearchResult:
    chunk: Chunk
    score: float
    retrieval_method: str
