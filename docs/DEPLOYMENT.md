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

The provider layer is deliberately HTTP-based so compatible hosted or self-hosted services can be used without coupling the core to one SDK.

## Local Docker Compose

The repository includes a non-root Docker image and a Compose service for reproducible startup.

1. Copy `.env.example` to `.env`.
2. Set `RAG_API_KEY`, `RAG_EMBEDDING_MODEL`, and `RAG_LLM_MODEL` for the chosen OpenAI-compatible provider.
3. Add Markdown knowledge files to `data/knowledge`.
4. Run:

```powershell
docker compose up --build --detach
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/ready
docker compose logs --follow api
docker compose down
```

Set `RAG_PORT` to change the host port; the container listens on port `8000`. Compose passes the provider settings to the application and mounts `data/knowledge` read-only. The image health check probes `/health`; use `/ready` to verify RAG configuration. If provider settings are absent, `/ready` and `/ask` return HTTP 503.

At startup, the current implementation reads Markdown files, chunks them, and builds an in-memory index. It re-embeds the corpus each time it starts, so use a small test corpus for now. Durable vector storage, embedding reuse, authentication, rate limiting, monitoring, backups, and measured real-corpus evaluation remain before production deployment.

## Production boundary

Before public deployment, configure a persistent database, authentication, rate limiting, secret management, monitoring, backups, and an evaluated knowledge corpus.
