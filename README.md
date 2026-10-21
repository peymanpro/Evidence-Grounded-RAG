# Evidence-Grounded-RAG

A research-oriented Retrieval-Augmented Generation system focused on evidence retrieval, grounded answers, citations, and measurable evaluation.

## What is implemented

- Recursive Markdown ingestion and structure-aware chunking with stable document IDs.
- Lexical retrieval, semantic retrieval, and hybrid fusion with Reciprocal Rank Fusion.
- An embedding-provider boundary, a deterministic offline baseline, and an OpenAI-compatible embedding adapter.
- In-memory retrieval, a persistent SQLite vector index, and an optional PostgreSQL/pgvector backend.
- Content- and model-aware reuse of cached embeddings across restarts.
- Evidence selection, grounded generation, citation verification, and explicit insufficient-evidence behavior.
- Retrieval metrics: Recall@k, Precision@k, reciprocal rank, and nDCG@k.
- A FastAPI API with provider and corpus configuration through environment variables.
- CI for Ruff, pytest, Compose validation, Docker image builds, a live health smoke test, and pgvector integration tests against PostgreSQL.

The local hashing embedder is a deterministic development baseline, not a production semantic embedding model.

## Architecture

```
Markdown corpus
      ↓
Ingestion and Chunking
      ↓
Embedding ───────────────→ Persistent Vector Index
      ↓                         ↓
Keyword Index ─────────→ Hybrid Retrieval
                                ↓
                             Reranking
                                ↓
                              Evidence
                                ↓
                              Context
                                ↓
                                LLM
                                ↓
                   Grounded Answer + Citations
                                ↓
                        Citation Verification
                                ↓
                            Evaluation
```

The important artifact is the evidence pipeline: what was retrieved, how it was ranked, which evidence reached generation, what was cited, and how those decisions can be measured.

## Quick start: Python

Requirements: Python 3.11 or later.

```bash
python -m venv .venv
# activate the environment using your platform's command
pip install -e ".[dev]"
ruff check .
pytest
python examples/basic_pipeline.py
```

To install the optional PostgreSQL backend locally:

```bash
pip install -e ".[dev,pgvector]"
```

## Run the API in Docker

Prerequisite: Docker Desktop or Docker Engine with the Compose v2 plugin.

```powershell
Copy-Item .env.example .env
notepad .env
docker compose config --quiet
docker compose up -d --build api
Invoke-RestMethod http://127.0.0.1:8000/health
```

Set RAG_API_KEY, RAG_EMBEDDING_MODEL, and RAG_LLM_MODEL in .env before asking questions. The sample corpus is under corpus/; Compose mounts it read-only. The SQLite vector database persists under data/. Never commit .env or real credentials.

Submit a question:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/ask -ContentType "application/json" -Body '{"question":"What does this project measure?"}'
```

Without provider credentials, the service intentionally runs in health-only mode: /health returns success and /ask returns HTTP 503 rather than a fake answer.

## Try PostgreSQL + pgvector locally

SQLite remains the default. For the optional PostgreSQL backend, update .env to use RAG_VECTOR_BACKEND=pgvector, then start the database profile before the API:

```powershell
docker compose --profile pgvector up -d postgres
docker compose --profile pgvector ps
docker compose up -d --build api
```

The provided PostgreSQL credentials are for local development only. Keep PostgreSQL bound to loopback and do not expose its port publicly. If you change the PostgreSQL user, password, or database name, update RAG_DATABASE_URL to match. More detail is in [Deployment](./docs/DEPLOYMENT.md).

## Configuration

- RAG_API_KEY
- RAG_API_BASE_URL (optional; defaults to OpenAI-compatible /v1)
- RAG_EMBEDDING_MODEL
- RAG_LLM_MODEL
- RAG_CORPUS_DIR (defaults to data/corpus outside Docker)
- RAG_CHUNK_MAX_CHARS (defaults to 1200)
- RAG_VECTOR_BACKEND: sqlite (default), pgvector, or memory
- RAG_VECTOR_DB_PATH (defaults to data/vectors.sqlite3 for SQLite)
- RAG_DATABASE_URL (required for pgvector)
- RAG_PORT and PGVECTOR_PORT (local ports)

Any OpenAI-compatible hosted or self-hosted HTTP endpoint can be used through the provider boundary.

## Project structure

- src/evidence_rag/models.py — core evidence models
- src/evidence_rag/ingestion.py — Markdown ingestion
- src/evidence_rag/bootstrap.py — recursive corpus loading
- src/evidence_rag/chunking.py — chunking
- src/evidence_rag/embeddings.py — embedding boundary and local baseline
- src/evidence_rag/providers.py — external embedding and LLM adapters
- src/evidence_rag/vector_store.py — in-memory vector index
- src/evidence_rag/persistent_store.py — SQLite vector index and embedding cache
- src/evidence_rag/pgvector_store.py — optional PostgreSQL/pgvector index
- src/evidence_rag/retrieval.py — lexical retrieval and rank fusion
- src/evidence_rag/reranking.py — second-stage reranking
- src/evidence_rag/pipeline.py — retrieval orchestration and index selection
- src/evidence_rag/grounding.py — evidence selection and context
- src/evidence_rag/generation.py — grounded generation boundary
- src/evidence_rag/verification.py — citation verification
- src/evidence_rag/service.py — end-to-end service
- src/evidence_rag/api.py — HTTP API and application startup
- src/evidence_rag/evaluation.py — retrieval evaluation
- docs/ARCHITECTURE.md, docs/EVALUATION.md, docs/SECURITY.md, docs/DEPLOYMENT.md — engineering documentation
- ROADMAP.md — development plan

## Related engineering work

- [AI Evaluation Engineering](https://github.com/peymanpro/AI-Evaluation-Engineering) provides a separate provider-neutral evaluation and regression-testing layer.
- [Production Agent Systems](https://github.com/peymanpro/Production-Agent-Systems) explores runtime policy, tool contracts, recovery, traces, and audit boundaries.

These repositories are independent projects; this RAG MVP does not depend on either one at runtime.

## Scope and limitations

This is an AI Engineering RAG MVP, **not a claim of production readiness**. SQLite scans vectors in application code; PostgreSQL/pgvector uses database-side cosine search and creates an HNSW index when the embedding dimension is supported. Embeddings above 2,000 dimensions currently use exact PostgreSQL vector search without HNSW. Benchmark both backends on a versioned corpus before making performance claims. A representative answer-quality benchmark, request-level observability, latency/cost tracking, authentication, rate limiting, backups, and reviewed cloud deployment remain open tasks.

See [ROADMAP.md](./ROADMAP.md) for the remaining work.
