from __future__ import annotations

from collections.abc import Sequence
from threading import RLock

import psycopg
from pgvector import Vector
from pgvector.psycopg import register_vector
from psycopg.types.json import Jsonb

from .embeddings import Embedder
from .models import Chunk, SearchResult


class PgVectorStore:
    """PostgreSQL/pgvector index with model-aware embedding reuse and cosine search."""

    _TABLE = "rag_vectors"
    _INDEX = "rag_vectors_embedding_hnsw"

    def __init__(self, database_url: str) -> None:
        if not database_url.strip():
            raise ValueError("database_url must not be empty")

        self._lock = RLock()
        self._conn = psycopg.connect(database_url)
        with self._lock:
            self._conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            self._conn.commit()
            register_vector(self._conn)
            with self._conn.transaction():
                self._conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS rag_vectors (
                        chunk_id TEXT PRIMARY KEY,
                        document_id TEXT NOT NULL,
                        text TEXT NOT NULL,
                        position INTEGER NOT NULL,
                        metadata JSONB NOT NULL,
                        embedding vector NOT NULL
                    )
                    """
                )
                self._conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS rag_vector_store_meta (
                        singleton SMALLINT PRIMARY KEY CHECK (singleton = 1),
                        embedding_model TEXT NOT NULL,
                        dimensions INTEGER
                    )
                    """
                )

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def sync_embeddings(
        self,
        chunks: Sequence[Chunk],
        embedder: Embedder,
        embedding_model: str,
    ) -> None:
        """Reuse matching vectors; replace changed content, model versions, and stale chunks."""
        if not embedding_model.strip():
            raise ValueError("embedding_model must not be empty")

        with self._lock, self._conn.transaction():
            meta = self._conn.execute(
                "SELECT embedding_model FROM rag_vector_store_meta WHERE singleton = 1"
            ).fetchone()
            if meta is None:
                self._conn.execute(
                    "INSERT INTO rag_vector_store_meta "
                    "(singleton, embedding_model, dimensions) VALUES (1, %s, NULL)",
                    (embedding_model,),
                )
            elif meta[0] != embedding_model:
                self._conn.execute("DELETE FROM rag_vectors")
                self._conn.execute(f"DROP INDEX IF EXISTS {self._INDEX}")
                self._conn.execute(
                    "UPDATE rag_vector_store_meta "
                    "SET embedding_model = %s, dimensions = NULL WHERE singleton = 1",
                    (embedding_model,),
                )

            if chunks:
                self._conn.execute(
                    "DELETE FROM rag_vectors WHERE NOT (chunk_id = ANY(%s))",
                    ([chunk.chunk_id for chunk in chunks],),
                )
            else:
                self._conn.execute("DELETE FROM rag_vectors")
                return

        cached = self._cached_vectors(chunks, embedding_model)
        missing = [chunk for chunk in chunks if chunk.chunk_id not in cached]
        if not missing:
            return

        vectors = embedder.embed([chunk.text for chunk in missing])
        if len(vectors) != len(missing):
            raise ValueError(
                "Embedder returned a different number of vectors than input texts"
            )
        dimensions_in_batch = {len(vector) for vector in vectors}
        if len(dimensions_in_batch) != 1 or 0 in dimensions_in_batch:
            raise ValueError(
                "Embedder must return non-empty vectors with one consistent dimension"
            )

        actual_dimensions = next(iter(dimensions_in_batch))
        with self._lock, self._conn.transaction():
            meta = self._conn.execute(
                "SELECT embedding_model, dimensions FROM rag_vector_store_meta "
                "WHERE singleton = 1"
            ).fetchone()
            if meta is None or meta[0] != embedding_model:
                raise RuntimeError("Embedding model configuration changed during index sync")
            stored_dimensions = meta[1]
            if stored_dimensions is not None and stored_dimensions != actual_dimensions:
                raise ValueError(
                    "Embedder dimension changed without changing the embedding model key"
                )
            if stored_dimensions is None:
                self._conn.execute(
                    f"ALTER TABLE {self._TABLE} ALTER COLUMN embedding "
                    f"TYPE vector({actual_dimensions}) "
                    f"USING embedding::vector({actual_dimensions})"
                )
                self._conn.execute(
                    "UPDATE rag_vector_store_meta SET dimensions = %s WHERE singleton = 1",
                    (actual_dimensions,),
                )
                # HNSW supports at most 2,000 dimensions for the standard vector type.
                if actual_dimensions <= 2000:
                    self._conn.execute(
                        f"CREATE INDEX IF NOT EXISTS {self._INDEX} ON {self._TABLE} "
                        "USING hnsw (embedding vector_cosine_ops)"
                    )

            with self._conn.cursor() as cursor:
                cursor.executemany(
                    """
                    INSERT INTO rag_vectors
                        (chunk_id, document_id, text, position, metadata, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (chunk_id) DO UPDATE SET
                        document_id = EXCLUDED.document_id,
                        text = EXCLUDED.text,
                        position = EXCLUDED.position,
                        metadata = EXCLUDED.metadata,
                        embedding = EXCLUDED.embedding
                    """,
                    [
                        (
                            chunk.chunk_id,
                            chunk.document_id,
                            chunk.text,
                            chunk.position,
                            Jsonb(chunk.metadata),
                            Vector(vector),
                        )
                        for chunk, vector in zip(missing, vectors, strict=True)
                    ],
                )

    def _cached_vectors(
        self,
        chunks: Sequence[Chunk],
        embedding_model: str,
    ) -> dict[str, list[float]]:
        requested = {chunk.chunk_id: chunk for chunk in chunks}
        if not requested:
            return {}

        with self._lock:
            rows = self._conn.execute(
                """
                SELECT chunk_id, document_id, text, position, metadata, embedding
                FROM rag_vectors
                """
            ).fetchall()
            meta = self._conn.execute(
                "SELECT embedding_model FROM rag_vector_store_meta WHERE singleton = 1"
            ).fetchone()
        if meta is None or meta[0] != embedding_model:
            return {}

        cached: dict[str, list[float]] = {}
        for row in rows:
            chunk = requested.get(row[0])
            if chunk is None:
                continue
            if (
                row[1] == chunk.document_id
                and row[2] == chunk.text
                and row[3] == chunk.position
                and row[4] == chunk.metadata
            ):
                cached[chunk.chunk_id] = list(row[5])
        return cached

    def search(self, query_vector: list[float], k: int = 5) -> list[SearchResult]:
        if k <= 0:
            return []
        vector = Vector(query_vector)
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT chunk_id, document_id, text, position, metadata,
                       1 - (embedding <=> %s) AS similarity
                FROM rag_vectors
                ORDER BY embedding <=> %s
                LIMIT %s
                """,
                (vector, vector, k),
            ).fetchall()
        return [
            SearchResult(
                chunk=Chunk(
                    chunk_id=row[0],
                    document_id=row[1],
                    text=row[2],
                    position=row[3],
                    metadata=row[4],
                ),
                score=float(row[5]),
                retrieval_method="semantic",
            )
            for row in rows
        ]
