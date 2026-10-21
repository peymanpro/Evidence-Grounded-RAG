# Evidence-Grounded-RAG

A research-oriented Retrieval-Augmented Generation system focused on evidence retrieval, grounded answers, citations, and measurable evaluation.

## What is implemented

The project now provides an end-to-end RAG MVP with explicit architectural boundaries:

- document and chunk models with source metadata;
- recursive Markdown corpus loading and structure-aware chunking;
- deterministic lexical retrieval;
- an embedding provider boundary and deterministic offline baseline;
- an OpenAI-compatible embedding adapter;
- in-memory semantic retrieval and an SQLite-backed persistent semantic index;
- content- and model-aware embedding cache reuse across restarts;
- hybrid retrieval with Reciprocal Rank Fusion;
- a second-stage deterministic reranker boundary;
- evidence selection and citation-ready context;
- an OpenAI-compatible grounded generation adapter;
- citation verification for generated answers;
- explicit insufficient-evidence behavior;
- Recall@k, Precision@k, reciprocal rank, and nDCG@k;
- a versioned benchmark format;
- a FastAPI service with health and question-answering endpoints;
- environment-driven provider and corpus startup;
- automated tests, linting, container build, Compose validation, and container health smoke test in CI.

The local hashing embedder remains a deterministic development baseline. It is **not** presented as a production semantic embedding model.

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

The important artifact is the evidence pipeline, not a chat UI: what was retrieved, how it was ranked, what evidence reached generation, what was cited, and how those decisions can be measured.

## Quick start

Requirements: Python 3.11 or later. From a fresh clone:

```bash
python -m venv .venv
# activate the environment using your platform's command
pip install -e ".[dev]"
ruff check .
pytest
python examples/basic_pipeline.py
```

## Run the API in Docker

Prerequisite: Docker Desktop or Docker Engine with the Compose v2 plugin.

```powershell
Copy-Item .env.example .env
notepad .env
docker compose config --quiet
docker compose up -d --build
Invoke-RestMethod http://127.0.0.1:8000/health
```

Set RAG_API_KEY, RAG_EMBEDDING_MODEL, and RAG_LLM_MODEL in .env before asking questions. The sample corpus is under corpus/; Compose mounts it read-only. The SQLite vector database is stored in ./data and persists outside the container. Never commit .env or real credentials.

Send a question:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/ask -ContentType "application/json" -Body '{"question":"What does this project measure?"}'
```

Without provider credentials, the service intentionally runs in health-only mode: /health returns success and /ask returns HTTP 503. This is preferable to returning a fake answer.

See [Deployment](./docs/DEPLOYMENT.md) for configuration and limitations.

## Provider configuration

The OpenAI-compatible adapters use environment variables:

- RAG_API_KEY
- RAG_API_BASE_URL (optional; defaults to OpenAI-compatible /v1)
- RAG_EMBEDDING_MODEL
- RAG_LLM_MODEL
- RAG_CORPUS_DIR (defaults to data/corpus outside Docker)
- RAG_CHUNK_MAX_CHARS (defaults to 1200)
- RAG_VECTOR_DB_PATH (defaults to data/vectors.sqlite3 outside Docker)

Any compatible hosted or self-hosted HTTP endpoint can be used through the provider boundary.

## Project structure

- src/evidence_rag/models.py — core evidence models
- src/evidence_rag/ingestion.py — single-document Markdown ingestion
- src/evidence_rag/bootstrap.py — recursive corpus loading
- src/evidence_rag/chunking.py — chunking
- src/evidence_rag/embeddings.py — embedding boundary and local baseline
- src/evidence_rag/providers.py — external embedding and LLM adapters
- src/evidence_rag/vector_store.py — in-memory vector search
- src/evidence_rag/persistent_store.py — SQLite vector index and embedding cache
- src/evidence_rag/retrieval.py — lexical retrieval and rank fusion
- src/evidence_rag/reranking.py — second-stage reranking
- src/evidence_rag/pipeline.py — retrieval orchestration and index selection
- src/evidence_rag/grounding.py — evidence selection/context
- src/evidence_rag/generation.py — grounded generation boundary
- src/evidence_rag/verification.py — citation verification
- src/evidence_rag/service.py — end-to-end service
- src/evidence_rag/api.py — HTTP API and application startup
- src/evidence_rag/evaluation.py — retrieval evaluation
- docs/ARCHITECTURE.md — architectural boundaries
- docs/EVALUATION.md — evaluation methodology
- docs/SECURITY.md — security boundaries
- docs/DEPLOYMENT.md — deployment guidance
- ROADMAP.md — development plan

## Related engineering work

- [AI Evaluation Engineering](https://github.com/peymanpro/AI-Evaluation-Engineering) provides a separate provider-neutral evaluation and regression-testing layer.
- [Production Agent Systems](https://github.com/peymanpro/Production-Agent-Systems) explores runtime policy, tool contracts, recovery, trace, and audit boundaries.

These repositories are independent projects. This RAG MVP does not depend on either one at runtime.

## Scope and honesty

This repository is an AI Engineering RAG MVP, **not yet a claim of production readiness**. The API uses a persistent SQLite vector index when it starts with provider configuration, but semantic search currently scans the stored vectors in application code. The lexical index is rebuilt in memory at startup. A representative real-corpus benchmark, request-level observability, latency/cost tracking, authentication, rate limiting, backups, and a reviewed cloud deployment remain open tasks. For larger corpora, measure the SQLite baseline before choosing PostgreSQL with pgvector or another vector-search service.

See [ROADMAP.md](./ROADMAP.md) for the remaining production work.
