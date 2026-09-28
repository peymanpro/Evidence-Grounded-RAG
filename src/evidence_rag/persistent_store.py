from __future__ import annotations

import json
import sqlite3

from .models import Chunk, SearchResult
from .vector_store import cosine_similarity


class SQLiteVectorStore:
    """Small persistent vector store for reproducible local deployments."""

    def __init__(self, path: str = "data/vectors.sqlite3") -> None:
        self.path = path
        self._db = sqlite3.connect(path)
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS vectors (chunk_id TEXT PRIMARY KEY, document_id TEXT NOT NULL, "
            "text TEXT NOT NULL, position INTEGER NOT NULL, metadata TEXT NOT NULL, vector TEXT NOT NULL)"
        )
        self._db.commit()

    def close(self) -> None:
        self._db.close()

    def upsert(self, records: list[tuple[Chunk, list[float]]]) -> None:
        self._db.executemany(
            "INSERT OR REPLACE INTO vectors VALUES (?, ?, ?, ?, ?, ?)",
            [
                (c.chunk_id, c.document_id, c.text, c.position, json.dumps(c.metadata), json.dumps(v))
                for c, v in records
            ],
        )
        self._db.commit()

    def search(self, query_vector: list[float], k: int = 5) -> list[SearchResult]:
        rows = self._db.execute(
            "SELECT chunk_id, document_id, text, position, metadata, vector FROM vectors"
        ).fetchall()
        scored = []
        for row in rows:
            chunk = Chunk(row[0], row[1], row[2], row[3], json.loads(row[4]))
            score = cosine_similarity(query_vector, json.loads(row[5]))
            scored.append(SearchResult(chunk, score, "semantic"))
        return sorted(scored, key=lambda x: x.score, reverse=True)[:k]
