# Deployment

## Local development

Install the package and run the API with:

```bash
pip install -e ".[dev]"
uvicorn examples.api_server:app --reload
```

The API exposes `GET /health` and `POST /ask`.

## Docker Compose

Prerequisite: Docker Desktop or Docker Engine with the Compose v2 plugin.

Copy the example environment file and edit it locally. On Windows PowerShell:

```powershell
Copy-Item .env.example .env
notepad .env
```

Set `RAG_API_KEY`, `RAG_EMBEDDING_MODEL`, and `RAG_LLM_MODEL` for your OpenAI-compatible provider. Leave `RAG_API_BASE_URL` at its default for the standard OpenAI API, or change it for a compatible service. Never commit `.env` or share its contents.

Build the image and start the API:

```bash
docker compose build
docker compose up -d
docker compose ps
```

The Compose configuration publishes the API on localhost only. The default URL is `http://127.0.0.1:8000`. On Windows PowerShell, verify the health endpoint with:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
docker compose logs -f api
```

To use a different local port:

```powershell
$env:RAG_PORT = "8080"
docker compose up -d --build
```

Stop the service with:

```bash
docker compose down
```

## Corpus, provider, and persisted index

The container includes a small safe sample corpus under `corpus/`; Compose mounts that directory read-only. Add or replace Markdown files there to use another corpus. The API recursively loads Markdown files when a non-empty `RAG_API_KEY` is configured, then initializes the embedding and generation adapters from environment variables.

Without `RAG_API_KEY`, the service intentionally starts in health-only mode: `GET /health` succeeds, while `POST /ask` returns HTTP 503 instead of pretending to have generated a grounded answer.

Compose mounts `./data` at `/app/data` and stores vectors in `/app/data/vectors.sqlite3`. That host directory survives container recreation and is excluded from Git. The standalone Python API defaults to `data/vectors.sqlite3` unless `RAG_VECTOR_DB_PATH` is set.

The SQLite index reuses cached vectors when chunk text, metadata, and embedding model configuration match. New or changed chunks are embedded; stale chunks are removed from the current index. Changing the embedding provider URL or model triggers re-embedding. This avoids repeated embedding calls on every restart for an unchanged small corpus.

**Scale limitation:** semantic search currently scans the SQLite vectors and calculates cosine similarity in application code. This is a durable local index, not a high-scale vector database. Before using a large corpus, benchmark it and consider PostgreSQL with pgvector or a dedicated vector database. Also note that changing the embedding model triggers a rebuild, which calls the configured embedding API for all chunks.

The image runs as a non-root user. Compose also uses a read-only root filesystem, drops Linux capabilities, enables `no-new-privileges`, and binds the published port to loopback. These controls are a safer local baseline, not a substitute for a complete production security review.

## Provider configuration

The OpenAI-compatible adapters use:

- `RAG_API_KEY`
- `RAG_API_BASE_URL` (optional; defaults to OpenAI-compatible `/v1`)
- `RAG_EMBEDDING_MODEL`
- `RAG_LLM_MODEL`
- `RAG_CORPUS_DIR` (defaults to `data/corpus` outside Docker)
- `RAG_CHUNK_MAX_CHARS` (defaults to `1200`)
- `RAG_VECTOR_DB_PATH` (defaults to `data/vectors.sqlite3` outside Docker)

The provider layer is deliberately HTTP-based so compatible hosted or self-hosted services can be used without coupling the core to one SDK.

## Production boundary

Before public deployment, evaluate a representative knowledge corpus, add authentication and rate limiting, configure production secret management, add request-level traces and metrics, establish backups, and measure latency and cost. For larger datasets, replace or supplement the SQLite cosine-scan index with a database-backed vector-search engine. Cloud deployment remains a separate, cost-bearing step and should be performed against an authorized account. The remaining implementation work is tracked in `ROADMAP.md`.
