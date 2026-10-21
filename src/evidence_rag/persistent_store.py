from __future__ import annotations

import json
import sqlite3
from collections.abc import Sequence
from pathlib import Path

from .embeddings import Embedder
from .models import Chunk, SearchResult
from .vector_store import cosine_similarity


class SQLiteVectorStore:
    """Persistent vector index with content- and model-aware embedding reuse."""

    def __init__(self, path: str | Path = "data/vectors.sqlite3") -> None:
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)

        self._db = sqlite3.connect(self.path)
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS vectors ("
            "chunk_id TEXT PRIMARY KEY, document_id TEXT NOT NULL, "
            "text TEXT NOT NULL, position INTEGER NOT NULL, "
            "metadata TEXT NOT NULL, vector TEXT NOT NULL, "
            "embedding_model TEXT NOT NULL DEFAULT 'default')"
        )
        columns = {
            row[1] for row in self._db.execute("PRAGMA table_info(vectors)").fetchall()
        }
        if "embedding_model" not in columns:
            self._db.execute(
                "ALTER TABLE vectors ADD COLUMN embedding_model "
                "TEXT NOT NULL DEFAULT 'default'"
            )
        self._db.commit()

    def close(self) -> None:
        self._db.close()

    def upsert(
        self,
        records: list[tuple[Chunk, list[float]]],
        embedding_model: str = "default",
    ) -> None:
        self._db.executemany(
            "INSERT OR REPLACE INTO vectors "
            "(chunk_id, document_id, text, position, metadata, vector, embedding_model) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    chunk.chunk_id,
                    chunk.document_id,
                    chunk.text,
                    chunk.position,
                    json.dumps(chunk.metadata, sort_keys=True, ensure_ascii=False),
                    json.dumps(vector),
                    embedding_model,
                )
                for chunk, vector in records
            ],
        )
        self._db.commit()

    def sync_embeddings(
        self,
        chunks: Sequence[Chunk],
        embedder: Embedder,
        embedding_model: str = "default",
    ) -> None:
        """Reuse matching vectors, embed changed/new chunks, and remove stale chunks."""
        self._db.execute(
            "CREATE TEMP TABLE IF NOT EXISTS active_chunk_ids "
            "(chunk_id TEXT PRIMARY KEY)"
        )
        self._db.execute("DELETE FROM active_chunk_ids")
        self._db.executemany(
            "INSERT OR IGNORE INTO active_chunk_ids (chunk_id) VALUES (?)",
            [(chunk.chunk_id,) for chunk in chunks],
        )
        self._db.execute(
            "DELETE FROM vectors WHERE chunk_id NOT IN "
            "(SELECT chunk_id FROM active_chunk_ids)"
        )
        self._db.commit()

        cached = self._cached_vectors(chunks, embedding_model)
        missing = [chunk for chunk in chunks if chunk.chunk_id not in cached]
        if not missing:
            return

        vectors = embedder.embed([chunk.text for chunk in missing])
        if len(vectors) != len(missing):
            raise ValueError(
                "Embedder returned a different number of vectors than input texts"
            )
        self.upsert(list(zip(missing, vectors, strict=True)), embedding_model)

    def _cached_vectors(
        self,
        chunks: Sequence[Chunk],
        embedding_model: str,
    ) -> dict[str, list[float]]:
        requested = {chunk.chunk_id: chunk for chunk in chunks}
        if not requested:
            return {}

        cached: dict[str, list[float]] = {}
        rows = self._db.execute(
            "SELECT chunk_id, document_id, text, position, metadata, vector, embedding_model "
            "FROM vectors"
        ).fetchall()
        for row in rows:
            chunk = requested.get(row[0])
            if chunk is None or row[6] != embedding_model:
                continue
            metadata = json.dumps(chunk.metadata, sort_keys=True, ensure_ascii=False)
            if (
                row[1] == chunk.document_id
                and row[2] == chunk.text
                and row[3] == chunk.position
                and row[4] == metadata
            ):
                cached[chunk.chunk_id] = json.loads(row[5])
        return cached

    def search(self, query_vector: list[float], k: int = 5) -> list[SearchResult]:
        if k <= 0:
            return []
        rows = self._db.execute(
            "SELECT chunk_id, document_id, text, position, metadata, vector FROM vectors"
        ).fetchall()
        scored = []
        for row in rows:
            chunk = Chunk(row[0], row[1], row[2], row[3], json.loads(row[4]))
            score = cosine_similarity(query_vector, json.loads(row[5]))
            scored.append(SearchResult(chunk, score, "semantic"))
        return sorted(scored, key=lambda item: item.score, reverse=True)[:k]
