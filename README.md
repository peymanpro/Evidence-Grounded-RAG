# Evidence-Grounded-RAG

A research-oriented Retrieval-Augmented Generation system focused on evidence retrieval, grounded answers, citations, and measurable evaluation.

## What is implemented

The project now provides an end-to-end RAG MVP with explicit architectural boundaries:

- document and chunk models with source metadata;
- Markdown ingestion and structure-aware chunking;
- deterministic lexical retrieval;
- an embedding provider boundary and deterministic offline baseline;
- an OpenAI-compatible embedding adapter;
- an in-memory vector-store implementation for offline examples;
- persistent semantic indexing with PostgreSQL and pgvector;
- incremental embedding reuse for unchanged chunks and model-aware index rebuilds;
- hybrid retrieval with Reciprocal Rank Fusion;
- a second-stage deterministic reranker boundary;
- evidence selection and citation-ready context;
- an OpenAI-compatible grounded generation adapter;
- citation verification for generated answers;
- explicit insufficient-evidence behavior;
- Recall@k, Precision@k, reciprocal rank, and nDCG@k;
- a versioned benchmark format;
- a small FastAPI HTTP service;
- automated tests and CI;
- security and deployment boundaries.

The local hashing embedder remains a deterministic development baseline. It is **not** presented as a production semantic embedding model.

## Architecture

```
Documents
   ↓
Parsing
   ↓
Structure-aware Chunking
   ↓
Embedding ───────────────→ Vector Index
   ↓                            ↓
Keyword Index ───────────→ Hybrid Retrieval
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

## Provider configuration

The production-oriented adapters use environment variables:

```text
RAG_API_KEY
RAG_API_BASE_URL       # optional, defaults to https://api.openai.com/v1
RAG_EMBEDDING_MODEL
RAG_LLM_MODEL
RAG_CORPUS_DIR         # defaults to data/knowledge; Compose uses /app/data/knowledge
RAG_DATABASE_URL       # optional outside Compose; when set, selects PostgreSQL/pgvector
RAG_VECTOR_TABLE_PREFIX # optional table prefix; defaults to rag
```

Any compatible hosted or self-hosted HTTP endpoint can be used through the provider boundary.

## Quick start

```bash
python -m venv .venv
# activate the environment using your platform's command
pip install -e ".[dev]"
pytest
python examples/basic_pipeline.py
```

Run the API example:

```bash
uvicorn examples.api_server:app --reload
```

The API exposes `GET /health`, `GET /ready`, and `POST /ask`. When provider settings are absent, the process remains live but `/ready` and `/ask` return HTTP 503. When configured, startup loads Markdown files from `RAG_CORPUS_DIR` and chunks them. If `RAG_DATABASE_URL` is set, semantic vectors are stored in PostgreSQL/pgvector; otherwise the API uses the in-memory index.

### Run with Docker Compose

Requires Docker Engine/Desktop with the Compose plugin.

Copy `.env.example` to `.env`. Set `RAG_API_KEY`, `RAG_EMBEDDING_MODEL`, and `RAG_LLM_MODEL` for your OpenAI-compatible provider, and add Markdown knowledge files under `data/knowledge`. The example PostgreSQL password is for local development only; change it before exposing any services. Use URL-safe characters for `POSTGRES_PASSWORD`, because Compose embeds it in the database connection URL.

```powershell
Copy-Item .env.example .env
# Edit .env, then:
docker compose up --build --detach
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/ready
docker compose logs --follow api
docker compose down
```

Compose starts the API and a PostgreSQL/pgvector service, waits for the database health check, and stores database files in the named `postgres-data` volume. PostgreSQL is not bound to a host port by default. `docker compose down` keeps the volume; `docker compose down -v` deletes it and the stored index.

When `RAG_DATABASE_URL` is configured, embeddings and vectors are persisted across API restarts. A stable embedding model identifier and base URL allow unchanged chunks to reuse stored embeddings; changed/new chunks are re-embedded. Changing the configured model identity triggers re-indexing. If your provider silently changes the model behind the same identifier, update the model identifier yourself.

**Current limitation:** this is not yet production-ready. The sample corpus is small, and the project still needs real-corpus benchmarks, authentication, rate limiting, operational monitoring, backups, and stronger failure handling before public exposure.

## Project structure

- `src/evidence_rag/models.py` — core evidence models
- `src/evidence_rag/ingestion.py` — source ingestion
- `src/evidence_rag/chunking.py` — chunking
- `src/evidence_rag/embeddings.py` — embedding boundary and local baseline
- `src/evidence_rag/providers.py` — external embedding and LLM adapters
- `src/evidence_rag/vector_store.py` — vector index contract and in-memory implementation
- `src/evidence_rag/postgres_store.py` — persistent PostgreSQL/pgvector index
- `src/evidence_rag/persistent_store.py` — SQLite persistence
- `src/evidence_rag/retrieval.py` — lexical retrieval and rank fusion
- `src/evidence_rag/reranking.py` — second-stage reranking
- `src/evidence_rag/pipeline.py` — retrieval orchestration
- `src/evidence_rag/grounding.py` — evidence selection/context
- `src/evidence_rag/generation.py` — grounded generation boundary
- `src/evidence_rag/verification.py` — citation verification
- `src/evidence_rag/service.py` — end-to-end service
- `src/evidence_rag/api.py` — HTTP API
- `src/evidence_rag/evaluation.py` — retrieval evaluation
- `docs/ARCHITECTURE.md` — architectural boundaries
- `docs/EVALUATION.md` — evaluation methodology
- `docs/SECURITY.md` — security boundaries
- `docs/DEPLOYMENT.md` — deployment guidance
- `ROADMAP.md` — development plan

## Related engineering work

- [AI Evaluation Engineering](https://github.com/peymanpro/AI-Evaluation-Engineering) provides a separate provider-neutral evaluation and regression-testing layer.
- [Production Agent Systems](https://github.com/peymanpro/Production-Agent-Systems) explores runtime policy, tool contracts, recovery, trace, and audit boundaries.

These repositories are independent projects. This RAG MVP does not depend on either one at runtime.

## Scope and honesty

This repository is **portfolio-ready as an AI Engineering RAG MVP**, not a claim of production readiness. A real deployment still requires an evaluated knowledge corpus, production embedding/LLM infrastructure, authentication, rate limiting, monitoring, backups, and measured operational behavior.

See [ROADMAP.md](./ROADMAP.md) for the remaining production work.
