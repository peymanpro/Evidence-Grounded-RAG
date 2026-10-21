# Evidence-Grounded-RAG project guide

Evidence-Grounded-RAG is a retrieval-augmented generation system designed to keep generated answers tied to retrieved source evidence.

## Ingestion

The initial ingestion pipeline reads Markdown documents. Each document is split into paragraph-aware chunks. Nested folders are supported, and relative paths provide stable document identifiers.

## Retrieval

The retrieval pipeline combines lexical retrieval and vector similarity with Reciprocal Rank Fusion. The current local default embedder is deterministic hashing for offline development and tests; it is not a substitute for a semantic embedding model.

## Grounded answers

The service selects a limited set of evidence chunks, includes those chunks in the model prompt, and verifies that cited evidence identifiers were actually supplied to the generator. If no evidence is retrieved, the service returns an insufficient-evidence answer instead of calling the model.

## API and runtime

The FastAPI service exposes GET /health for a health check and POST /ask for a question. A real question-answering configuration requires RAG_API_KEY, RAG_EMBEDDING_MODEL, RAG_LLM_MODEL, and a Markdown corpus directory.

## Production limitations

The current retrieval index is built in memory during service startup. Production use still requires evaluation on a representative corpus, persistent vector storage for larger workloads, authentication, rate limiting, secret management, request-level observability, and measured latency and cost.
