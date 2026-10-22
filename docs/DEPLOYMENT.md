# Deployment

## Local

Install the package and run the API with:

```bash
pip install -e ".[dev]"
uvicorn examples.api_server:app --reload
```

The API exposes `GET /health`, `GET /ready`, and `POST /ask`. The liveness endpoint remains healthy without provider settings; readiness and asking return HTTP 503 until the RAG service is configured.

## Provider configuration

The OpenAI-compatible adapters use:

- `RAG_API_KEY`
- `RAG_API_BASE_URL` (optional; defaults to OpenAI-compatible `/v1`)
- `RAG_EMBEDDING_MODEL`
- `RAG_LLM_MODEL`
- `RAG_DATABASE_URL` (optional outside Compose; selects PostgreSQL/pgvector)
- `RAG_VECTOR_TABLE_PREFIX` (optional; defaults to `rag`)

The provider layer is deliberately HTTP-based so compatible hosted or self-hosted services can be used without coupling the core to one SDK.

## Local Docker Compose

The repository includes a non-root API image and a PostgreSQL/pgvector service with a named data volume. In Compose, the API is published on loopback only, uses a read-only root filesystem, drops Linux capabilities, and prevents privilege escalation. These are local-deployment safeguards, not a complete public-deployment security configuration.

1. Copy `.env.example` to `.env`.
2. Set `RAG_API_KEY`, `RAG_EMBEDDING_MODEL`, and `RAG_LLM_MODEL` for the chosen OpenAI-compatible provider.
3. Set a local database password using URL-safe characters; the sample password is not for public deployment.
4. Add Markdown knowledge files to `data/knowledge`.
5. Run:

```powershell
docker compose up --build --detach
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/ready
docker compose logs --follow api
docker compose down
```

Set `RAG_PORT` to change the API's host port; the container listens on port `8000`. The host port remains bound to `127.0.0.1` to avoid exposing the local API to other machines by default. Compose waits for PostgreSQL readiness, passes `RAG_DATABASE_URL` to the API, and mounts `data/knowledge` read-only. The database is not exposed on a host port by default. PostgreSQL data persists in `postgres-data`; `docker compose down -v` removes this volume and the stored index.

The API container filesystem is read-only except for a temporary `/tmp` filesystem. The container drops all Linux capabilities and enables `no-new-privileges`. The PostgreSQL service keeps its own writable data volume.

The startup process reads Markdown files and chunks them. PostgreSQL stores vectors and chunk metadata, while the index tracks the embedding model identity and a content hash per chunk. New or text-changed chunks are embedded; unchanged chunks reuse their stored vectors. A model identifier change triggers re-indexing. Version your provider/model configuration explicitly to avoid reusing vectors if a remote model changes behind a stable alias.

Without provider settings, only the liveness endpoint succeeds; `/ready` and `/ask` return HTTP 503. A successful health check does not mean that the RAG pipeline is configured or production-ready. Real-corpus benchmarks, authentication, rate limiting, monitoring, backups, and more complete operational hardening remain before public deployment.

## Production boundary

Before public deployment, configure a persistent database, authentication, rate limiting, secret management, monitoring, backups, and an evaluated knowledge corpus. Configure network exposure deliberately instead of reusing the local Compose settings unchanged.
