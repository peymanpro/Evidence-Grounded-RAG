from collections.abc import Sequence
from math import sqrt
import re
from typing import Protocol


class Embedder(Protocol):
    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


class HashingEmbedder:
    """Deterministic local baseline used for tests and offline experiments.

    It is not intended to replace a semantic embedding model. A real provider
    can implement the Embedder protocol without changing retrieval orchestration.
    """

    def __init__(self, dimensions: int = 256) -> None:
        if dimensions <= 0:
            raise ValueError("dimensions must be positive")
        self.dimensions = dimensions

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in re.findall(r"[\w-]+", text.lower()):
            vector[hash(token) % self.dimensions] += 1.0
        norm = sqrt(sum(value * value for value in vector))
        return [value / norm for value in vector] if norm else vector
