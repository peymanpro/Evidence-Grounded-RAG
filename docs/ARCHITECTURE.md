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
