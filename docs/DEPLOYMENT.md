# Deployment

## Local development

Install the package and run the API with:

```bash
pip install -e ".[dev]"
uvicorn examples.api_server:app --reload
```

The API exposes `GET /health` and `POST /ask`.

## Docker Compose with SQLite (default)

Prerequisite: Docker Desktop or Docker Engine with the Compose v2 plugin.

Copy the example environment file and edit it locally. On Windows PowerShell:

```powershell
Copy-Item .env.example .env
notepad .env
```

Set `RAG_API_KEY`, `RAG_EMBEDDING_MODEL`, and `RAG_LLM_MODEL` for your OpenAI-compatible provider. Leave `RAG_VECTOR_BACKEND=sqlite` for the default local setup. Never commit `.env` or share its contents.

Build the image and start the API:

```powershell
docker compose config --quiet
docker compose up -d --build api
docker compose ps
Invoke-RestMethod http://127.0.0.1:8000/health
```

The API is published on localhost only. To use another local port, set `RAG_PORT` in `.env` and recreate the API service.

Stop it with:

```powershell
docker compose down
```

## Optional PostgreSQL + pgvector profile

Use this when you want the vector search and index to run in PostgreSQL, or when you want to benchmark it against SQLite. The Compose profile is intended for **local development only**; the default credentials are not production credentials.

1. In `.env`, set `RAG_VECTOR_BACKEND=pgvector`. Keep `RAG_DATABASE_URL` consistent with `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB`. The provided defaults work together for local development.
2. Start the optional database profile and wait until it is healthy:

   ```powershell
   docker compose --profile pgvector up -d postgres
   docker compose --profile pgvector ps
   ```

3. Build and start the API:

   ```powershell
   docker compose up -d --build api
   Invoke-RestMethod http://127.0.0.1:8000/health
   ```

4. Check service logs if startup fails:

   ```powershell
   docker compose logs --tail 100 api
   docker compose --profile pgvector logs --tail 100 postgres
   ```

PostgreSQL is bound to localhost, and its data is persisted under `data/postgres/`. The API connects to the database using the Docker service name `postgres`; from a process running directly on the host, that hostname is not available. Do not expose the database port to the public internet.

Use SQLite for small local corpora until measurements show a reason to switch. The pgvector backend creates an HNSW cosine index when the embedding dimension is supported; embeddings above 2,000 dimensions currently use exact PostgreSQL vector search without HNSW. Both backends reuse embeddings only when chunk content, metadata, and the configured embedding model key match. Changing models triggers re-embedding.

## Corpus, provider, and persisted index

The sample corpus is under `corpus/`; Compose mounts it read-only. Add or replace Markdown files there to use another corpus. When a non-empty `RAG_API_KEY` is configured, the API recursively loads Markdown files and initializes the embedding and generation adapters from environment variables.

Without `RAG_API_KEY`, the service intentionally starts in health-only mode: `GET /health` succeeds, while `POST /ask` returns HTTP 503 instead of pretending to have generated a grounded answer.

For SQLite, Compose persists the vector index at `data/vectors.sqlite3`. For PostgreSQL, the data directory is `data/postgres/`. These local data directories are excluded from Git. The SQLite backend scans vectors in application code; PostgreSQL/pgvector performs nearest-neighbor ordering in the database and uses HNSW when available. A benchmark on a versioned corpus is needed before claiming one backend is faster or more accurate for your workload.

The image runs as a non-root user. Compose also uses a read-only root filesystem, drops Linux capabilities, enables `no-new-privileges`, and binds published ports to loopback. These controls are a safer local baseline, not a substitute for a complete production security review.

## Provider and index settings

- `RAG_API_KEY`
- `RAG_API_BASE_URL` (optional; defaults to OpenAI-compatible `/v1`)
- `RAG_EMBEDDING_MODEL`
- `RAG_LLM_MODEL`
- `RAG_CORPUS_DIR` (defaults to `data/corpus` outside Docker)
- `RAG_CHUNK_MAX_CHARS` (defaults to `1200`)
- `RAG_VECTOR_BACKEND`: `sqlite` (default), `pgvector`, or `memory`
- `RAG_VECTOR_DB_PATH` (defaults to `data/vectors.sqlite3` for SQLite)
- `RAG_DATABASE_URL` (required for the pgvector backend)
- `RAG_PORT` (local API port)
- `PGVECTOR_PORT` (local PostgreSQL port)

The provider layer uses the OpenAI-compatible HTTP API so compatible hosted or self-hosted endpoints can be used without coupling the core to one SDK.

## Production boundary

Before public deployment, evaluate a representative knowledge corpus, add authentication and rate limiting, configure production secret management, add request-level traces and metrics, establish backups, and measure latency and cost. Cloud deployment remains a separate, cost-bearing step and requires an authorized account. See `ROADMAP.md` for the remaining work.
