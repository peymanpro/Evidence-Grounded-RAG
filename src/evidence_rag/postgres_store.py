from __future__ import annotations

from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from hashlib import sha256
import json
import os
import re
from typing import Any

import psycopg
from pgvector.psycopg import register_vector

from .embeddings import Embedder
from .models import Chunk, SearchResult
from .vector_store import IndexReport, validate_vectors


class PostgresVectorStore:
    """Persistent pgvector index with incremental, model-aware embedding reuse.

    A stable table prefix isolates indexes that share one database. The prefix is
    restricted to simple SQL identifiers because table names cannot be parameters.
    """

    def __init__(self, dsn: str, table_prefix: str = "rag") -> None:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,29}", table_prefix):
            raise ValueError(
                "table_prefix must start with a letter or underscore and contain "
                "at most 30 letters, digits, or underscores"
            )
        self.dsn = dsn
        self.table_prefix = table_prefix.lower()
        self.chunks_table = f"{self.table_prefix}_chunks"
        self.state_table = f"{self.table_prefix}_index_state"
        self.index_name = f"{self.table_prefix}_chunks_embedding_hnsw_idx"
        lock_digest = sha256(f"{self.table_prefix}:index".encode("utf-8")).digest()[:8]
        self._lock_id = int.from_bytes(lock_digest, byteorder="big", signed=True)
        self._dimension: int | None = None

    @classmethod
    def from_env(cls) -> PostgresVectorStore:
        dsn = os.getenv("RAG_DATABASE_URL", "").strip()
        if not dsn:
            raise RuntimeError("RAG_DATABASE_URL is required for PostgreSQL vector storage")
        return cls(dsn, table_prefix=os.getenv("RAG_VECTOR_TABLE_PREFIX", "rag"))

    @contextmanager
    def _connection(self, ensure_extension: bool = False) -> Iterator[Any]:
        with psycopg.connect(self.dsn) as connection:
            if ensure_extension:
                connection.execute("CREATE EXTENSION IF NOT EXISTS vector")
            register_vector(connection)
            yield connection

    @staticmethod
    def _embedder_identity(embedder: Embedder) -> str:
        identity: dict[str, str | int | float | bool] = {
            "class": f"{type(embedder).__module__}.{type(embedder).__qualname__}"
        }
        for attribute in ("model", "model_name", "base_url", "dimensions", "dimension", "revision"):
            value = getattr(embedder, attribute, None)
            if isinstance(value, (str, int, float, bool)):
                identity[attribute] = value
        return json.dumps(identity, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def _content_hash(chunk: Chunk) -> str:
        return sha256(chunk.text.encode("utf-8")).hexdigest()

    @staticmethod
    def _metadata_json(metadata: dict[str, Any]) -> str:
        try:
            return json.dumps(metadata, sort_keys=True, separators=(",", ":"))
        except (TypeError, ValueError) as exc:
            raise ValueError("chunk metadata must be JSON-serializable") from exc

    def _create_chunks_table(self, connection: Any, dimension: int) -> None:
        connection.execute(
            f"""
            CREATE TABLE {self.chunks_table} (
                chunk_id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                chunk_text TEXT NOT NULL,
                position INTEGER NOT NULL,
                metadata JSONB NOT NULL,
                content_sha TEXT NOT NULL,
                embedding vector({dimension}) NOT NULL
            )
            """
        )
        if dimension <= 2000:
            connection.execute(
                f"""
                CREATE INDEX IF NOT EXISTS {self.index_name}
                ON {self.chunks_table} USING hnsw (embedding vector_cosine_ops)
                """
            )

    def _upsert(self, connection: Any, chunks: Sequence[Chunk], vectors: Sequence[Sequence[float]]) -> None:
        if not chunks:
            return
        query = f"""
            INSERT INTO {self.chunks_table}
                (chunk_id, document_id, chunk_text, position, metadata, content_sha, embedding)
            VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s)
            ON CONFLICT (chunk_id) DO UPDATE SET
                document_id = EXCLUDED.document_id,
                chunk_text = EXCLUDED.chunk_text,
                position = EXCLUDED.position,
                metadata = EXCLUDED.metadata,
                content_sha = EXCLUDED.content_sha,
                embedding = EXCLUDED.embedding
        """
        rows = [
            (
                chunk.chunk_id,
                chunk.document_id,
                chunk.text,
                chunk.position,
                self._metadata_json(chunk.metadata),
                self._content_hash(chunk),
                list(vector),
            )
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]
        with connection.cursor() as cursor:
            cursor.executemany(query, rows)

    def index(self, chunks: list[Chunk], embedder: Embedder) -> IndexReport:
        if not chunks:
            raise ValueError("cannot index an empty chunk collection")
        chunk_ids = [chunk.chunk_id for chunk in chunks]
        if len(set(chunk_ids)) != len(chunk_ids):
            raise ValueError("chunk_id values must be unique within an index")

        model_id = self._embedder_identity(embedder)

        # A session lock prevents two app instances from embedding and replacing
        # the same named index at the same time. No transaction is held open while
        # waiting on the external embedding provider.
        with psycopg.connect(self.dsn, autocommit=True) as lock_connection:
            lock_connection.execute("SELECT pg_advisory_lock(%s)", (self._lock_id,))
            try:
                return self._index_locked(chunks, embedder, model_id)
            finally:
                lock_connection.execute("SELECT pg_advisory_unlock(%s)", (self._lock_id,))

    def _index_locked(
        self, chunks: list[Chunk], embedder: Embedder, model_id: str
    ) -> IndexReport:
        chunk_ids = [chunk.chunk_id for chunk in chunks]
        with self._connection(ensure_extension=True) as connection:
            connection.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.state_table} (
                    singleton SMALLINT PRIMARY KEY CHECK (singleton = 1),
                    model_id TEXT NOT NULL,
                    dimension INTEGER NOT NULL
                )
                """
            )
            state_row = connection.execute(
                f"SELECT model_id, dimension FROM {self.state_table} WHERE singleton = 1"
            ).fetchone()
            table_exists = (
                connection.execute("SELECT to_regclass(%s)", (self.chunks_table,)).fetchone()[0]
                is not None
            )
            existing_rows = (
                connection.execute(
                    f"""
                    SELECT chunk_id, content_sha, document_id, chunk_text, position, metadata
                    FROM {self.chunks_table}
                    """
                ).fetchall()
                if table_exists
                else []
            )

        old_model_id, old_dimension = state_row if state_row else (None, None)
        state_exists = state_row is not None
        existing = {
            row[0]: {
                "content_sha": row[1],
                "document_id": row[2],
                "chunk_text": row[3],
                "position": row[4],
                "metadata": row[5],
            }
            for row in existing_rows
        }
        current_ids = {chunk.chunk_id for chunk in chunks}
        deleted_count = sum(chunk_id not in current_ids for chunk_id in existing)

        full_rebuild = not state_exists or not table_exists or old_model_id != model_id
        model_changed = bool(state_exists and old_model_id != model_id)
        chunks_to_embed: list[Chunk]
        vectors: list[list[float]]
        unchanged: list[Chunk] = []

        if full_rebuild:
            chunks_to_embed = list(chunks)
            vectors = embedder.embed([chunk.text for chunk in chunks_to_embed])
            dimension = validate_vectors(vectors, len(chunks_to_embed))
        else:
            chunks_to_embed = [
                chunk
                for chunk in chunks
                if chunk.chunk_id not in existing
                or existing[chunk.chunk_id]["content_sha"] != self._content_hash(chunk)
            ]
            unchanged = [chunk for chunk in chunks if chunk not in chunks_to_embed]
            vectors = (
                embedder.embed([chunk.text for chunk in chunks_to_embed])
                if chunks_to_embed
                else []
            )
            changed_dimension = validate_vectors(vectors, len(chunks_to_embed))
            if chunks_to_embed and changed_dimension != old_dimension:
                # A provider can change dimensions behind a stable model name.
                # Rebuild every vector rather than mixing incompatible spaces.
                chunks_to_embed = list(chunks)
                vectors = embedder.embed([chunk.text for chunk in chunks_to_embed])
                dimension = validate_vectors(vectors, len(chunks_to_embed))
                full_rebuild = True
                model_changed = True
                unchanged = []
            else:
                dimension = old_dimension

        validate_vectors(vectors, len(chunks_to_embed))
        if dimension <= 0:
            raise ValueError("embedding dimension must be positive")

        rebuild_table = (
            not table_exists
            or not state_exists
            or (old_dimension is not None and old_dimension != dimension)
        )

        with self._connection() as connection:
            if rebuild_table:
                if table_exists:
                    connection.execute(f"DROP TABLE {self.chunks_table}")
                self._create_chunks_table(connection, dimension)
            elif dimension <= 2000:
                connection.execute(
                    f"""
                    CREATE INDEX IF NOT EXISTS {self.index_name}
                    ON {self.chunks_table} USING hnsw (embedding vector_cosine_ops)
                    """
                )

            self._upsert(connection, chunks_to_embed, vectors)

            if unchanged and not rebuild_table:
                metadata_updates = [
                    (
                        chunk.document_id,
                        chunk.text,
                        chunk.position,
                        self._metadata_json(chunk.metadata),
                        chunk.chunk_id,
                    )
                    for chunk in unchanged
                ]
                with connection.cursor() as cursor:
                    cursor.executemany(
                        f"""
                        UPDATE {self.chunks_table}
                        SET document_id = %s, chunk_text = %s, position = %s, metadata = %s::jsonb
                        WHERE chunk_id = %s
                        """,
                        metadata_updates,
                    )

            connection.execute(
                f"DELETE FROM {self.chunks_table} WHERE NOT (chunk_id = ANY(%s::text[]))",
                (chunk_ids,),
            )
            connection.execute(
                f"""
                INSERT INTO {self.state_table} (singleton, model_id, dimension)
                VALUES (1, %s, %s)
                ON CONFLICT (singleton) DO UPDATE SET
                    model_id = EXCLUDED.model_id,
                    dimension = EXCLUDED.dimension
                """,
                (model_id, dimension),
            )

        self._dimension = dimension
        return IndexReport(
            embedded=len(chunks_to_embed),
            reused=len(chunks) - len(chunks_to_embed),
            deleted=deleted_count,
            dimension=dimension,
            model_changed=model_changed,
        )

    def search(self, query_vector: list[float], k: int = 5) -> list[SearchResult]:
        if k <= 0:
            return []
        if self._dimension is None:
            raise RuntimeError("index() must complete before searching the PostgreSQL vector store")
        if len(query_vector) != self._dimension:
            raise ValueError(
                f"query embedding has dimension {len(query_vector)}; expected {self._dimension}"
            )

        with self._connection() as connection:
            rows = connection.execute(
                f"""
                SELECT chunk_id, document_id, chunk_text, position, metadata,
                       1 - (embedding <=> %s) AS score
                FROM {self.chunks_table}
                ORDER BY embedding <=> %s
                LIMIT %s
                """,
                (query_vector, query_vector, k),
            ).fetchall()

        return [
            SearchResult(
                Chunk(
                    chunk_id=row[0],
                    document_id=row[1],
                    text=row[2],
                    position=row[3],
                    metadata=row[4],
                ),
                float(row[5]),
                "semantic",
            )
            for row in rows
        ]
