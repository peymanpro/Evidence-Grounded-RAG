# Evidence-Grounded-RAG

A research-oriented RAG system focused on retrieving reliable evidence, grounding generated answers in that evidence, and measuring retrieval and answer quality.

## Current status

**RAG MVP with environment-driven startup, persistent indexing, and container validation.** When configured with an OpenAI-compatible provider, the service loads a Markdown corpus, reuses matching cached embeddings, and can select either SQLite or PostgreSQL/pgvector as its semantic index. CI runs linting, unit tests, PostgreSQL integration tests, Compose validation, image build, and a live container health smoke test.

This is not yet a production-readiness claim. SQLite search scans vectors in application code; pgvector uses database-side cosine search and creates an HNSW index for supported embedding dimensions. Quality/performance benchmarks on a representative corpus, request observability, security hardening, and cloud deployment remain open.

## Deployment track (active)

### Container, bootstrap, and persistent index — completed

- [x] Non-root Docker image for the FastAPI service
- [x] Docker build context excludes local environments, databases, and secret files
- [x] Local Compose service binds to loopback and persists data through a host volume
- [x] Optional local PostgreSQL/pgvector Compose profile
- [x] Read-only container filesystem, dropped Linux capabilities, and no privilege escalation
- [x] CI runs Ruff and pytest on branch pushes and pull requests
- [x] CI validates Compose, builds the image, and smoke-tests GET /health in a running container
- [x] Recursive Markdown corpus loader with stable relative-path document IDs
- [x] Environment-driven API startup for OpenAI-compatible embedding and generation providers
- [x] Explicit HTTP 503 behavior when the service has no RAG configuration
- [x] SQLite vector index integrated into RetrievalPipeline and API startup
- [x] Optional PostgreSQL/pgvector backend integrated into the same retrieval interface
- [x] Content- and model-aware cached embedding reuse across restarts
- [x] New/changed chunks are re-embedded and stale chunks are removed from the active index
- [x] CI runs pgvector integration tests against a real PostgreSQL service
- [x] Container quick-start, environment template, and backend limitations documented

### Remaining deployment work

- [ ] Benchmark SQLite versus pgvector on a versioned, representative corpus
- [ ] Add a measured retrieval and answer-quality benchmark report
- [ ] Add a cross-encoder reranker and measure its impact
- [ ] Connect request-level LLM traces and operational metrics
- [ ] Add authentication, rate limiting, request limits, and production secret management
- [ ] Deploy to a cloud environment and verify the running service end to end

A successful health check proves that the container starts and responds. It does not prove answer quality or production readiness.

## Roadmap

### Phase 0 — Foundation
- [x] Project structure and documentation
- [x] Clear provider and component boundaries
- [x] Automated tests and CI

### Phase 1 — Ingestion
- [x] Document model, Markdown source, and basic metadata
- [x] Structure-aware paragraph chunking
- [x] Recursive corpus loading with deterministic IDs
- [ ] Heading/section metadata
- [ ] Additional source formats

### Phase 2 — Embeddings and Index
- [x] Embedding provider boundary and deterministic local baseline
- [x] OpenAI-compatible embedding adapter
- [x] In-memory vector search
- [x] Persistent SQLite index with embedding cache
- [x] PostgreSQL/pgvector index with cosine search
- [x] Embedding reuse across restarts and model-change invalidation
- [ ] Benchmark SQLite versus pgvector on a representative corpus

### Phase 3 — Retrieval
- [x] Lexical and semantic retrieval baselines
- [x] Hybrid retrieval with Reciprocal Rank Fusion
- [x] Deterministic second-stage reranking boundary
- [x] Retrieval evidence and evaluation metrics
- [ ] Cross-encoder reranker
- [ ] Real-corpus retrieval benchmark

### Phase 4 — Grounded Generation
- [x] Evidence selection and citation-ready context
- [x] OpenAI-compatible LLM adapter
- [x] Citation verification and insufficient-evidence path
- [ ] Model-specific grounding benchmark

### Phase 5 — Evaluation and Operations
- [x] Recall@k, Precision@k, reciprocal rank, and nDCG@k
- [x] Benchmark dataset format
- [ ] Measured benchmark report on a versioned corpus
- [ ] Latency, token usage, and cost tracking
- [ ] Request-level traces and failure-case analysis

### Phase 6 — Application
- [x] FastAPI health and ask endpoints
- [x] Environment-driven provider startup and Markdown corpus loading
- [x] Configurable semantic-index backend
- [ ] Authentication and request validation limits
- [ ] Browser demo, only if it adds value to evaluating the RAG system

### Phase 7 — Hardening and Release
- [x] Security boundaries and prompt-injection considerations documented
- [x] Local container baseline
- [ ] Rate limiting and production secret management
- [ ] Operational monitoring and backups
- [ ] Cloud deployment
- [ ] Release notes with evaluated limitations

## Non-goals

- A generic chatbot without measurable retrieval quality
- Hiding retrieval decisions behind one framework abstraction
- Claiming production readiness without evidence
- Optimizing for technology count

## Guiding principles

1. Evidence before generation.
2. Retrieval quality is measured independently from answer quality.
3. Major architectural choices need explicit reasons.
4. Failure cases are part of the project.
5. Keep every stage runnable.
6. Prefer clear boundaries over unnecessary abstraction.
