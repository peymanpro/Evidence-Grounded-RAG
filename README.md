# Evidence-Grounded-RAG

A research-oriented Retrieval-Augmented Generation system focused on evidence retrieval, grounded answers, citations, and measurable evaluation.

## What is implemented

The project now provides an end-to-end RAG MVP with explicit architectural boundaries:

- document and chunk models with source metadata;
- Markdown ingestion and structure-aware chunking;
- deterministic lexical retrieval;
- an embedding provider boundary and deterministic offline baseline;
- an OpenAI-compatible embedding adapter;
- in-memory and persistent SQLite vector storage;
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

The API exposes `GET /health`, `GET /ready`, and `POST /ask`. When provider settings are absent, the process remains live but `/ready` and `/ask` return HTTP 503. When configured, startup loads Markdown files from `RAG_CORPUS_DIR`, chunks them, and builds an in-memory retrieval index.

### Run with Docker Compose

Requires Docker Engine/Desktop with the Compose plugin.

Copy `.env.example` to `.env` and set `RAG_API_KEY`, `RAG_EMBEDDING_MODEL`, and `RAG_LLM_MODEL` for your OpenAI-compatible provider. Add your own Markdown files to `data/knowledge`.

```powershell
Copy-Item .env.example .env
# Edit .env, then:
docker compose up --build --detach
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/ready
docker compose logs --follow api
docker compose down
```

Set `RAG_PORT` in your environment to map the API to a different host port. If provider settings are absent, only the liveness endpoint succeeds; `/ready` and `/ask` return HTTP 503.

**Current limitation:** the corpus is loaded into an in-memory index and embedded during each startup. This is suitable for validating a small corpus, not for large or production workloads. The upcoming persistence phase will address durable indexing and avoiding repeated embedding work. Do not expose this MVP publicly as a production service.

## Project structure

- `src/evidence_rag/models.py` — core evidence models
- `src/evidence_rag/ingestion.py` — source ingestion
- `src/evidence_rag/chunking.py` — chunking
- `src/evidence_rag/embeddings.py` — embedding boundary and local baseline
- `src/evidence_rag/providers.py` — external embedding and LLM adapters
- `src/evidence_rag/vector_store.py` — in-memory vector search
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
