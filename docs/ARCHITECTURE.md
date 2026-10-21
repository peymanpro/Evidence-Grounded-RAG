# Architecture

The project is intentionally built as an explicit pipeline rather than a single RAG framework call.

## Planned boundaries

1. **Ingestion** — turn source material into normalized documents.
2. **Chunking** — preserve useful structure while producing retrievable units.
3. **Embedding** — map chunks and queries into a shared vector space.
4. **Indexing** — persist chunks, vectors, and metadata.
5. **Retrieval** — combine semantic and lexical signals.
6. **Reranking** — improve ordering of candidate evidence.
7. **Context construction** — select evidence within a controlled context budget.
8. **Generation** — produce an answer constrained by retrieved evidence.
9. **Evaluation** — measure retrieval and grounding independently.

The first implementation keeps provider-specific concerns out of the core models so retrieval and evaluation can be tested without requiring an LLM provider.


## Vector index implementations

The retrieval pipeline depends on the small `VectorIndex` contract instead of a concrete storage implementation:

- `InMemoryVectorStore` is the fast offline implementation used by unit tests and examples.
- `PostgresVectorStore` persists chunk text, source metadata, content hashes, and embedding vectors in PostgreSQL with pgvector.

When `RAG_DATABASE_URL` is present, application startup selects the PostgreSQL implementation. The index records the embedding model identity and vector dimension. It embeds new chunks and chunks whose text changed, updates metadata for unchanged chunks without recalculating their vectors, and removes chunks that disappeared from the source corpus. A model-identity or dimension change triggers a full re-index to prevent mixing embedding spaces.

The index uses cosine similarity and creates an HNSW index when the vector dimension is supported by pgvector's HNSW index limits. It does not claim that a particular corpus has good retrieval quality until that quality is measured by the benchmark suite.
